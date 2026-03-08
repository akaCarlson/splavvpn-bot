from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from app.bot.middleware import tg_error_guard, private_only, with_role
from app.services.access import Role
from app.bot.help_registry import HELP_SPECS
from app.services.content import read_text_file
from app.bot.commands import role_allows  # у тебя уже есть role_allows в commands.py

def _visible_help(role: Role):
    return [h for h in HELP_SPECS if role_allows(role, h.visible_roles)]

@tg_error_guard
@private_only
@with_role
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = context.user_data.get("role", Role.NO_ACCESS)

    items = _visible_help(role)
    if not items:
        await update.message.reply_text("Справка недоступна. Проверь доступ.")
        return

    lines = ["<b>Справка</b>", "Выбери раздел:"]
    for h in items:
        lines.append(f"/{h.cmd} — {h.title}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def _send_help_file(update: Update, context: ContextTypes.DEFAULT_TYPE, cmd_name: str):
    role = context.user_data.get("role", Role.NO_ACCESS)
    item = next((h for h in HELP_SPECS if h.cmd == cmd_name), None)
    if not item:
        await update.message.reply_text("Раздел справки не найден.")
        return
    if not role_allows(role, item.visible_roles):
        await update.message.reply_text("Нет доступа к этому разделу справки.")
        return

    html = read_text_file(item.file_path)
    await update.message.reply_text(html, parse_mode="HTML", disable_web_page_preview=True)

# Команды-страницы
@tg_error_guard
@private_only
@with_role
async def help_android(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_help_file(update, context, "help_android")

@tg_error_guard
@private_only
@with_role
async def help_iphone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_help_file(update, context, "help_iphone")

@tg_error_guard
@private_only
@with_role
async def help_windows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_help_file(update, context, "help_windows")

@tg_error_guard
@private_only
@with_role
async def help_macos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_help_file(update, context, "help_macos")

@tg_error_guard
@private_only
@with_role
async def help_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_help_file(update, context, "help_bot")

@tg_error_guard
@private_only
@with_role
async def help_billing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_help_file(update, context, "help_billing")
