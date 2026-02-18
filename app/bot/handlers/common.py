from telegram import Update
from telegram.ext import ContextTypes

from app.bot.middleware import tg_error_guard


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
async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panel = context.application.bot_data["panel"]
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
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(
        f"tg_id={u.id}\nusername=@{u.username}\nname={u.full_name}"
    )

@tg_error_guard
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panel = context.application.bot_data["panel"]
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