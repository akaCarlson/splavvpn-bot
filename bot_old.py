import os
import io
import functools
import requests
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from db import get_user, upsert_user, create_invite, get_invite, mark_invite_used, expire_invites
from panel_client import PanelClient

# Всегда читаем .env рядом с bot.py и перезаписываем env vars
load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

BOT_TOKEN = os.environ["BOT_TOKEN"].strip()
PANEL_BASE_URL = os.environ["PANEL_BASE_URL"].strip()
PANEL_ADMIN_EMAIL = os.environ["PANEL_ADMIN_EMAIL"].strip()
PANEL_ADMIN_PASSWORD = os.environ["PANEL_ADMIN_PASSWORD"].strip()
ACCESS_CHAT_ID = int(os.environ["ACCESS_CHAT_ID"])
ADMIN_TG_IDS = {int(x.strip()) for x in os.environ.get("ADMIN_TG_IDS","").split(",") if x.strip()}
INVITE_TTL_DAYS = int(os.environ.get("INVITE_TTL_DAYS","7"))

panel = PanelClient(PANEL_BASE_URL, PANEL_ADMIN_EMAIL, PANEL_ADMIN_PASSWORD)

async def is_chat_member(context: ContextTypes.DEFAULT_TYPE, tg_id: int) -> bool:
    m = await context.bot.get_chat_member(chat_id=ACCESS_CHAT_ID, user_id=tg_id)
    return m.status in ("member", "administrator", "creator")

async def ensure_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    expire_invites()

    u = update.effective_user
    tg_id = u.id
    username = u.username

    # Админ всегда ок
    if tg_id in ADMIN_TG_IDS:
        upsert_user(tg_id, username, role="ADMIN", status="ACTIVE")
        return True

    # Если он член чата — даём доступ как BILLING_MEMBER
    if await is_chat_member(context, tg_id):
        upsert_user(tg_id, username, role="BILLING_MEMBER", status="ACTIVE")
        return True

    # Иначе — проверяем, есть ли он в БД и активен
    dbu = get_user(tg_id)
    if dbu and dbu["status"] == "ACTIVE":
        return True

    await update.message.reply_text(
        "Доступ закрыт.\n"
        "Варианты:\n"
        "1) Вступи в основной чат (доступ по умолчанию)\n"
        "2) Попроси инвайт у админа/модератора"
    )
    return False


def pick_server(servers_json: dict) -> dict | None:
    items = servers_json.get("servers", []) if isinstance(servers_json, dict) else []
    if not items:
        return None
    # берём первый active, иначе первый
    for s in items:
        if isinstance(s, dict) and s.get("status") == "active":
            return s
    return items[0] if isinstance(items[0], dict) else None

def tg_error_guard(fn):
    @functools.wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await fn(update, context)
        except requests.HTTPError as e:
            r = e.response
            url = getattr(r, "url", "unknown_url")
            status = getattr(r, "status_code", "unknown_status")
            # кусочек body, но без риска больших простыней
            body = ""
            try:
                body = (r.text or "")[:300]
            except Exception:
                pass
            await update.message.reply_text(f"❌ Panel HTTP {status} on {url}\n{body}")
        except requests.RequestException as e:
            await update.message.reply_text(f"❌ Network error: {type(e).__name__}: {e}")
        except Exception as e:
            await update.message.reply_text(f"❌ Internal error: {type(e).__name__}: {e}")
            raise
    return wrapper

@tg_error_guard
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # print("CHAT_ID =", update.effective_chat.id, "CHAT_TYPE =", update.effective_chat.type)

    await update.message.reply_text(
        "Команды:\n"
        "/servers — список VPN-серверов\n"
        "/request — получить ключ (конфиг) для себя\n"
        "/health — проверить статус панели\n"
        "/status — статус своего клиента и сервера\n"
        "/my_id — узнать свой Telegram ID и username\n"
    )

@tg_error_guard
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(
        f"tg_id={u.id}\nusername=@{u.username}\nname={u.full_name}"
    )

@tg_error_guard
async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = panel.get_servers()
    items = data.get("servers", [])
    if not items:
        await update.message.reply_text("Серверов в панели не найдено.")
        return

    # ВАЖНО: не показываем password/keys/awg_params
    lines = []
    for s in items:
        lines.append(
            f'id={s.get("id")} name={s.get("name")} host={s.get("host")} status={s.get("status")}'
        )
    await update.message.reply_text("\n".join(lines))

@tg_error_guard
async def request_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    tg_username = update.effective_user.username or "no_username"
    name = f"tg_{tg_id}_{tg_username}"

    found = panel.find_client_by_name_any_server(name)
    if found:
        client_id = found["client"].get("id")
        if not client_id:
            await update.message.reply_text(f"Нашёл клиента, но без id: {found['client']}")
            return
        server_id = found["client"].get("server_id")
        print(f"Клиент уже есть: client_id={client_id}, name={name}")
        config_text = panel.get_client_config_text(int(client_id))
    else:
        # 2) иначе создаём на первом active сервере
        servers_json = panel.get_servers()
        srv = pick_server(servers_json)
        if not srv:
            await update.message.reply_text("Не вижу ни одного сервера в панели.")
            return

        server_id = srv.get("id")
        created = panel.create_client(int(server_id), name)
        client = created.get("client", {})
        client_id = client.get("id")
        if not client_id:
            await update.message.reply_text(f"Создал, но не нашёл client_id: {created}")
            return
        config_text = client.get("config") or panel.get_client_config_text(int(client_id))

    bio = io.BytesIO(config_text.encode("utf-8"))
    bio.name = f"{name}.conf"

    await update.message.reply_document(
        document=bio,
        filename=bio.name,
        caption=f"Готово ✅ server_id={server_id}, client_id={client_id}",
    )

@tg_error_guard
async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hc = panel.healthcheck()

    lines = [
        f"auth: {'OK' if hc['auth'] else 'FAIL'}",
        f"servers: {'OK' if hc['servers_ok'] else 'FAIL'}",
        f"active_server_id: {hc['active_server_id']}",
        f"clients_list: {'OK' if hc['clients_list_ok'] else 'FAIL'}",
        f"clients_count: {hc['clients_count']}",
    ]

    if hc["client_details_ok"] is not None:
        lines.append(f"client_details: {'OK' if hc['client_details_ok'] else 'FAIL'}")
        lines.append(f"config_present: {'OK' if hc['config_present'] else 'FAIL'}")
    else:
        lines.append("client_details: SKIP (no clients)")

    if hc["error"]:
        lines.append(f"error: {hc['error']}")

    await update.message.reply_text("\n".join(lines))

@tg_error_guard
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    tg_username = update.effective_user.username or "no_username"
    name = f"tg_{tg_id}_{tg_username}"

    found = panel.find_client_by_name_any_server(name)
    if not found:
        await update.message.reply_text("Клиент ещё не создан. Используй /request.")
        return

    s = found["server"]
    c = found["client"]
    await update.message.reply_text(
        f"server: id={s.get('id')} name={s.get('name')} host={s.get('host')} status={s.get('status')}\n"
        f"client: id={c.get('id')} name={c.get('name')}"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("servers", servers))
    app.add_handler(CommandHandler("request", request_cmd))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("my_id", my_id))
    app.run_polling()

if __name__ == "__main__":
    main()
