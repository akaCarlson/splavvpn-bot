import functools
import requests
from enum import Enum
from telegram import Update
from telegram.ext import ContextTypes

#from app.services.access import is_chat_member
#from app.db.repo_users import get_user
from app.services.access import get_effective_role, Role

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
            return
        return await fn(update, context)
    return wrapper

def with_role(fn):
    @functools.wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        role, extra = await get_effective_role(context, update.effective_user.id)
        context.user_data["role"] = role
        context.user_data.update(extra)
        return await fn(update, context)
    return wrapper

def require_roles(*allowed: Role):
    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            role = context.user_data.get("role", Role.NO_ACCESS)
            if role not in allowed:
                await update.message.reply_text("Нет доступа. Нужен доступ через клубный чат или инвайт.")
                return
            return await fn(update, context)
        return wrapper
    return deco