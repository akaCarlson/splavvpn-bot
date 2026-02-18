from telegram import Update
from telegram.ext import ContextTypes

from app.bot.middleware import tg_error_guard

@tg_error_guard
async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panel = context.application.bot_data["panel"]
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
