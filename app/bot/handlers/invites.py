import secrets
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.middleware import tg_error_guard, private_only, with_role, require_roles

from app.services.access import Role
from app.db.repo_users import upsert_user
from app.db.repo_invites import create_invite, get_invite, mark_invite_used, expire_invites
from app.db.repo_activation import create_activation_request, get_pending_request_for_user, approve_request, reject_request, get_request
from app.db.repo_billing import set_billing_member
from app.db.repo_relationships import upsert_relationship

def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR)
async def invite_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    expire_invites()

    cfg = context.application.bot_data["cfg"]
    me = update.effective_user
    upsert_user(me.id, me.username)

    code = secrets.token_urlsafe(16)
    expires_at = datetime.now(timezone.utc) + timedelta(days=cfg.INVITE_TTL_DAYS)

    create_invite(
        code=code,
        invite_type="ADMIN_INVITE",
        created_by_tg_id=me.id,
        owner_tg_id=None,
        expires_at_iso=_iso(expires_at),
    )

    # ссылка на запуск
    bot_username = (context.bot.username or "").lstrip("@")
    link = f"https://t.me/{bot_username}?start=admin_{code}" if bot_username else f"/start admin_{code}"

    await update.message.reply_text(
        "✅ Admin-invite создан.\n"
        f"⏳ TTL: {cfg.INVITE_TTL_DAYS} дней\n"
        f"🔗 {link}\n"
        "⚠️ Активация потребует подтверждения и может занять какое-то время."
    )

@tg_error_guard
@private_only
@with_role
async def start_payload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from app.bot.router import START_MENU
    expire_invites()
    
    me = update.effective_user
    upsert_user(me.id, me.username)

    if not context.args:
        await update.message.reply_text(START_MENU)
        return

    token = context.args[0].strip()
    if token.startswith("admin_"):
        code = token.removeprefix("admin_")
        inv = get_invite(code)
        if not inv or inv["type"] != "ADMIN_INVITE" or inv["status"] != "ACTIVE":
            await update.message.reply_text("❌ Инвайт недействителен или уже использован.")
            return
        if str(inv["expires_at"]) and inv["expires_at"] < datetime.now(timezone.utc):
            await update.message.reply_text("❌ Инвайт истёк.")
            return

        pending = get_pending_request_for_user(me.id)
        if pending:
            await update.message.reply_text(f"⏳ Заявка уже ожидает решения. ID={pending['id']}")
            return

        req = create_activation_request(me.id, code)

        # уведомим админов/модеров
        cfg = context.application.bot_data["cfg"]
        for admin_id in cfg.ADMIN_TG_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        "🟦 ActivationRequest\n"
                        f"id={req['id']}\n"
                        f"user=@{me.username or '-'} tg_id={me.id}\n"
                        f"cmd: /approve_activation_{req['id']}  или  /reject_activation_{req['id']}"
                    ),
                )
            except Exception:
                pass

        await update.message.reply_text(
            "✅ Заявка на доступ создана и отправлена админам.\n"
            f"ID={req['id']}\n"
            "Жди approve."
        )
        return

    if token.startswith("guest_"):
        code = token.removeprefix("guest_")
        inv = get_invite(code)
        if not inv or inv["type"] != "GUEST_INVITE" or inv["status"] != "ACTIVE":
            await update.message.reply_text("❌ Инвайт недействителен или уже использован.")
            return

        owner = inv["owner_tg_id"]
        if not owner:
            await update.message.reply_text("❌ Инвайт повреждён (нет owner).")
            return

        upsert_relationship(me.id, int(owner))
        mark_invite_used(code, me.id)

        await update.message.reply_text("✅ Гостевой доступ активирован. Теперь ты INVITED_GUEST.\n"
                                        "Используй /request для получения ключа для себя.\n"
                                        "Или /help для получения инструкций по настройке VPN-клиента.")
        return

    await update.message.reply_text("❌ Неизвестный формат инвайта.")

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR)
async def approve_activation_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #req_id = int(context.args[0])
    raw = (update.message.text or "").strip()
    # поддержка /approve_activation_123 и /approve_activation 123
    if raw.startswith("/approve_activation_"):
        req_id = int(raw.split("_", 2)[2])
    elif context.args:
        req_id = int(context.args[0])
    else:
        await update.message.reply_text("Формат: /approve_activation_<id>  или  /approve_activation <id>")
        return

    me = update.effective_user
    upsert_user(me.id, me.username)

    req = approve_request(req_id, me.id)
    if not req:
        await update.message.reply_text("❌ Не найдено или уже решено.")
        return

    # назначаем BILLING_MEMBER
    set_billing_member(int(req["tg_id"]), me.id)

    # помечаем инвайт использованным
    mark_invite_used(str(req["invite_code"]), int(req["tg_id"]))

    # уведомим пользователя
    try:
        await context.bot.send_message(chat_id=int(req["tg_id"]), text="✅ Доступ одобрен. Теперь ты BILLING_MEMBER.\n"
                                       "Используй /request для получения ключа для себя.\n"
                                       "Или /request_for для создания гостевого инвайта для другого пользователя.\n"
                                       "Или /help для получения инструкций по настройке VPN-клиента.")
    except Exception:
        pass

    await update.message.reply_text(f"✅ Approved. req_id={req_id}")

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR)
async def reject_activation_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = (update.message.text or "").strip()
    if raw.startswith("/reject_activation_"):
        req_id = int(raw.split("_", 2)[2])
    elif context.args:
        req_id = int(context.args[0])
    else:
        await update.message.reply_text("Формат: /reject_activation_<id>  или  /reject_activation <id>")
        return
    me = update.effective_user
    upsert_user(me.id, me.username)

    req = reject_request(req_id, me.id)
    if not req:
        await update.message.reply_text("❌ Не найдено или уже решено.")
        return

    try:
        await context.bot.send_message(chat_id=int(req["tg_id"]), text="❌ Доступ отклонён админом.")
    except Exception:
        pass

    await update.message.reply_text(f"✅ Rejected. req_id={req_id}")

@tg_error_guard
@private_only
@with_role
@require_roles(Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.ADMIN, Role.MODERATOR)
async def request_for_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    expire_invites()

    cfg = context.application.bot_data["cfg"]
    me = update.effective_user
    upsert_user(me.id, me.username)

    code = secrets.token_urlsafe(16)
    expires_at = datetime.now(timezone.utc) + timedelta(days=cfg.INVITE_TTL_DAYS)

    create_invite(
        code=code,
        invite_type="GUEST_INVITE",
        created_by_tg_id=me.id,
        owner_tg_id=me.id,  # owner = текущий плательщик
        expires_at_iso=_iso(expires_at),
    )

    bot_username = (context.bot.username or "").lstrip("@")
    link = f"https://t.me/{bot_username}?start=guest_{code}" if bot_username else f"/start guest_{code}"

    await update.message.reply_text(
        "✅ Гостевой инвайт создан.\n"
        f"⏳ TTL: {cfg.INVITE_TTL_DAYS} дней\n"
        f"🔗 {link}\n"
        "⚠️ Поделись этой ссылкой с пользователем, которому хочешь предоставить доступ к VPN в течение 7 дней, потом ссылка станет недействительной.\n"
        "⚠️ Для активации, приглашенному пользователю необходимо пройти по ссылке и выполнить команду /request для получения ключа.\n"
        "⚠️ Для помощи в настройке VPN-клиента, выполните команду /help."      
    )
