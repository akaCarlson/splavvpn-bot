import functools
import requests
from telegram import Update
from telegram.ext import ContextTypes

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