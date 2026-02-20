from telegram import Update
from telegram.ext import ContextTypes

from app.bot.middleware import tg_error_guard, private_only, with_role, require_roles
from app.services.access import Role
from app.db.repo_users import upsert_user, delete_user, get_user
from app.db.repo_profiles import get_profile

def _parse_delete_tg_id(update: Update) -> int | None:
    raw = (update.message.text or "").strip()
    if not raw.startswith("/delete_"):
        return None
    tail = raw[len("/delete_"):].strip()
    if not tail.isdigit():
        return None
    return int(tail)

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR)
async def delete_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin = update.effective_user
    upsert_user(admin.id, admin.username)

    tg_id = _parse_delete_tg_id(update)
    if not tg_id:
        await update.message.reply_text("Формат: /delete_<tg_id> (только цифры)")
        return
    # найти tg_id по username в БД бота
    victim = get_user(tg_id)
    if not victim:
        await update.message.reply_text(f"❌ Пользователь с tg_id '{tg_id}' не найден в БД бота.")
        return

    tg_id = int(victim["tg_id"])

    # Safety: не даём удалить самого себя случайно
    if tg_id == admin.id:
        await update.message.reply_text("❌ Нельзя удалить самого себя этой командой.")
        return

    panel = context.application.bot_data["panel"]

    # 1) удалить профиль в панели, если есть
    prof = get_profile(tg_id)
    await update.message.reply_text(f"DEBUG profile={prof}")

    if prof and prof.get("client_id"):
        client_id = int(prof["client_id"])
        try:
            resp = panel.delete_client(client_id)
            await update.message.reply_text(f"🧹 Panel delete OK: client_id={client_id} resp={resp}")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Panel delete FAILED: client_id={client_id} err={type(e).__name__}: {e}")

    # 2) удалить в БД бота (каскад подчистит связи)
    deleted = delete_user(tg_id)
    if not deleted:
        await update.message.reply_text("⚠️ Не смог удалить пользователя из БД (уже удалён?).")
        return

    # 3) уведомить удаляемого (если возможно)
    try:
        await context.bot.send_message(chat_id=tg_id, text="🗑️ Твой доступ к VPN удалён администратором.")
    except Exception:
        pass

    await update.message.reply_text(f"✅ Удалено: tg_id={tg_id} username={deleted.get('username')}")


