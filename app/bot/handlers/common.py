from telegram import Update
from telegram.ext import ContextTypes

from app.bot.middleware import tg_error_guard, private_only, with_effective_role, Role

@private_only
@with_effective_role
@tg_error_guard
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = context.user_data["role"]
    if role == Role.NO_ACCESS:
        await update.message.reply_text("Нет доступа. Нужно быть в клубном чате или получить инвайт.")
        return

    await update.message.reply_text(
        "Команды:\n"
        "/servers — список VPN-серверов\n"
        "/request — получить ключ (конфиг) для себя\n"
        "/health — проверить статус панели\n"
        "/status — статус своего клиента и сервера\n"
        "/my_id — узнать свой Telegram ID и username\n"
    )

@private_only
@with_effective_role
@tg_error_guard
async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = context.user_data["role"]
    if role == Role.NO_ACCESS:
        await update.message.reply_text("Нет доступа. Нужно быть в клубном чате или получить инвайт.")
        return
    
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

@private_only
@with_effective_role
@tg_error_guard
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = context.user_data["role"]
    if role == Role.NO_ACCESS:
        await update.message.reply_text("Нет доступа. Нужно быть в клубном чате или получить инвайт.")
        return
    
    u = update.effective_user
    await update.message.reply_text(
        f"tg_id={u.id}\nusername=@{u.username}\nname={u.full_name}"
    )

@private_only
@with_effective_role
@tg_error_guard
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = context.user_data["role"]
    if role == Role.NO_ACCESS:
        await update.message.reply_text("Нет доступа. Нужно быть в клубном чате или получить инвайт.")
        return
    
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