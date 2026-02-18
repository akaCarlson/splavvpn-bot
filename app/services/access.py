from telegram.ext import ContextTypes


async def is_chat_member(context: ContextTypes.DEFAULT_TYPE, tg_id: int) -> bool:
    cfg = context.application.bot_data["cfg"]

    m = await context.bot.get_chat_member(chat_id=cfg.ACCESS_CHAT_ID, user_id=tg_id)
    return m.status in ("member", "administrator", "creator")