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

from app.config import load_config
from app.services.panel import PanelClient
from bot.router import register_handlers
from db import get_user, upsert_user, create_invite, get_invite, mark_invite_used, expire_invites
from app.services.panel import PanelClient

# Всегда читаем .env рядом с bot.py и перезаписываем env vars
'''load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

BOT_TOKEN = os.environ["BOT_TOKEN"].strip()
PANEL_BASE_URL = os.environ["PANEL_BASE_URL"].strip()
PANEL_ADMIN_EMAIL = os.environ["PANEL_ADMIN_EMAIL"].strip()
PANEL_ADMIN_PASSWORD = os.environ["PANEL_ADMIN_PASSWORD"].strip()
ACCESS_CHAT_ID = int(os.environ["ACCESS_CHAT_ID"])
ADMIN_TG_IDS = {int(x.strip()) for x in os.environ.get("ADMIN_TG_IDS","").split(",") if x.strip()}
INVITE_TTL_DAYS = int(os.environ.get("INVITE_TTL_DAYS","7"))

panel = PanelClient(PANEL_BASE_URL, PANEL_ADMIN_EMAIL, PANEL_ADMIN_PASSWORD)'''



'''async def ensure_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
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
    return False'''





def main():
    cfg = load_config()

    app = Application.builder().token(cfg.BOT_TOKEN).build()

    # зависимости для handlers
    app.bot_data["cfg"] = cfg
    app.bot_data["panel"] = PanelClient(cfg.PANEL_BASE_URL, cfg.PANEL_ADMIN_EMAIL, cfg.PANEL_ADMIN_PASSWORD)

    register_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()



