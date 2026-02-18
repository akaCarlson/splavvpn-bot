import functools
import requests
from enum import Enum
from telegram import Update
from telegram.ext import ContextTypes

from app.services.access import is_chat_member
from app.db.repo_users import get_user

class Role(str, Enum):
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    CHAT_MEMBER = "CHAT_MEMBER"
    BILLING_MEMBER = "BILLING_MEMBER"
    INVITED_GUEST = "INVITED_GUEST"
    NO_ACCESS = "NO_ACCESS"

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

def private_only(fn):
    @functools.wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat and update.effective_chat.type != "private":
            return  # FR-01: игнорим группы/каналы
        return await fn(update, context)
    return wrapper

def with_effective_role(fn):
    @functools.wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        cfg = context.application.bot_data["cfg"]
        tg_id = update.effective_user.id

        # ADMIN/MODERATOR по спискам
        if tg_id in cfg.ADMIN_TG_IDS:
            role = Role.ADMIN
        else:
            # chat membership
            if await is_chat_member(context, tg_id):
                role = Role.CHAT_MEMBER
            else:
                # пока простая заглушка: если есть в БД — NO_ACCESS (позже BILLING_MEMBER/INVITED_GUEST)
                role = Role.NO_ACCESS

        context.user_data["role"] = role
        return await fn(update, context)
    return wrapper