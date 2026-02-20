from telegram import Update
from telegram.ext import ContextTypes

from app.bot.middleware import require_roles, tg_error_guard, private_only, with_role, Role
from app.db.repo_profiles import get_profile
from app.db.repo_billing import is_billing_member
from app.db.repo_relationships import get_owner_for_guest
from app.services.access import Role, is_chat_member


@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST)
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

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST)
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = context.user_data["role"]
    if role == Role.NO_ACCESS:
        await update.message.reply_text("Нет доступа. Нужно быть в клубном чате или получить инвайт.")
        return
    
    u = update.effective_user
    await update.message.reply_text(
        f"tg_id={u.id}\nusername=@{u.username}\nname={u.full_name}"
    )

@tg_error_guard
@private_only
@with_role
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.application.bot_data["cfg"]
    panel = context.application.bot_data["panel"]

    u = update.effective_user
    tg_id = u.id
    username = u.username or "-"
    role = context.user_data.get("role", Role.NO_ACCESS)

    # статус в боте
    chat_member = await is_chat_member(context, cfg.ACCESS_CHAT_ID, tg_id)
    billing = is_billing_member(tg_id)
    owner = get_owner_for_guest(tg_id)  # int|None

    # профиль (маппинг к панели)
    prof = get_profile(tg_id)

    lines = []
    lines.append(f"tg_id: {tg_id}")
    lines.append(f"username: @{username}" if username != "-" else "username: -")
    lines.append(f"role: {role}")

    # bot-side status
    lines.append("bot:")
    lines.append(f"  chat_member: {'YES' if chat_member else 'NO'}")
    lines.append(f"  billing_member: {'YES' if billing else 'NO'}")
    if owner:
        lines.append(f"  invited_guest_owner_tg_id: {owner}")

    # panel-side status
    lines.append("panel:")
    if not prof or not prof.get("client_id"):
        lines.append("panel:")
        lines.append("  profile: NONE")
        lines.append("")
        lines.append("👉 Чтобы получить ключ: /request")
        await update.message.reply_text("\n".join(lines))
        return


    client_id = int(prof["client_id"])
    server_id = prof.get("server_id")
    lines.append(f"  profile: server_id={server_id} client_id={client_id} name={prof.get('name')}")

    # детали клиента
    try:
        details = panel.get_client_details(client_id)
        client = details.get("client", {}) if isinstance(details, dict) else {}
        lines.append(f"  status: {client.get('status', '-')}")
        if client.get("expires_at"):
            lines.append(f"  expires_at: {client.get('expires_at')}")
        if client.get("traffic_limit"):
            lines.append(f"  traffic_limit: {client.get('traffic_limit')}")
    except Exception as e:
        lines.append(f"  details: ERROR {type(e).__name__}: {e}")

    # метрики (sent/receive)
    def _fmt_bytes(n):
        try:
            n = int(n)
        except Exception:
            return "-"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n} {unit}"
            n //= 1024
        return f"{n} PB"

    try:
        m = panel.get_client_metrics(client_id)
        # формат может отличаться, поэтому достаём гибко
        sent = m.get("sent") or (m.get("metrics") or {}).get("sent")
        recv = m.get("received") or m.get("recv") or (m.get("metrics") or {}).get("received")
        lines.append(f"  sent: {_fmt_bytes(sent)}")
        lines.append(f"  received: {_fmt_bytes(recv)}")
    except Exception as e:
        lines.append(f"  metrics: ERROR {type(e).__name__}: {e}")

    await update.message.reply_text("\n".join(lines))
