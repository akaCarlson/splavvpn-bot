import os
import io
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from panel_client import PanelClient

# Всегда читаем .env рядом с bot.py и перезаписываем env vars
load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

BOT_TOKEN = os.environ["BOT_TOKEN"].strip()
PANEL_BASE_URL = os.environ["PANEL_BASE_URL"].strip()
PANEL_ADMIN_EMAIL = os.environ["PANEL_ADMIN_EMAIL"].strip()
PANEL_ADMIN_PASSWORD = os.environ["PANEL_ADMIN_PASSWORD"].strip()

panel = PanelClient(PANEL_BASE_URL, PANEL_ADMIN_EMAIL, PANEL_ADMIN_PASSWORD)

def pick_server(servers_json: dict) -> dict | None:
    items = servers_json.get("servers", []) if isinstance(servers_json, dict) else []
    if not items:
        return None
    # берём первый active, иначе первый
    for s in items:
        if isinstance(s, dict) and s.get("status") == "active":
            return s
    return items[0] if isinstance(items[0], dict) else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/servers — список VPN-серверов\n"
        "/request — получить ключ (конфиг) для себя"
    )

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

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("servers", servers))
    app.add_handler(CommandHandler("request", request_cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
