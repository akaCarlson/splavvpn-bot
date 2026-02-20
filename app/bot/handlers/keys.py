import html
import qrcode


from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from app.bot.middleware import require_roles, tg_error_guard, private_only, with_role, Role
from app.db.repo_profiles import get_profile, upsert_profile
from app.services.panel_utils import pick_server


async def _ensure_and_get_config(update, context) -> tuple[str, str]:
    """
    returns (name, cfg_text) or raises Exception with text
    """
    panel = context.application.bot_data["panel"]
    tg_id = update.effective_user.id
    name = f"tg_{tg_id}"

    prof = get_profile(tg_id)

    server_id = None
    client_id = None

    if prof and prof.get("server_id") and prof.get("client_id"):
        server_id = int(prof["server_id"])
        client_id = int(prof["client_id"])
    else:
        found = panel.find_client_by_name_any_server(name)
        if found:
            client_obj = found.get("client") if isinstance(found, dict) else None
            server_obj = found.get("server") if isinstance(found, dict) else None

            client_id = (
                (client_obj.get("id") if isinstance(client_obj, dict) else None)
                or found.get("client_id")
                or found.get("id")
            )
            server_id = (
                (server_obj.get("id") if isinstance(server_obj, dict) else None)
                or (client_obj.get("server_id") if isinstance(client_obj, dict) else None)
                or found.get("server_id")
            )

            if not server_id or not client_id:
                raise RuntimeError("Нашёл клиента в панели, но не смог определить server_id/client_id.")

            server_id = int(server_id)
            client_id = int(client_id)
            upsert_profile(tg_id, server_id, client_id, name)
        else:
            servers_json = panel.get_servers()
            srv = pick_server(servers_json)
            if not srv:
                raise RuntimeError("В панели нет доступных серверов.")

            server_id = int(srv["id"])
            created = panel.create_client(server_id, name)

            if isinstance(created, dict) and "client" in created and isinstance(created["client"], dict):
                client_id = int(created["client"]["id"])
            else:
                client_id = int(created["id"])

            upsert_profile(tg_id, server_id, client_id, name)

    cfg_text = panel.get_client_config_text(int(client_id))
    if not cfg_text:
        raise RuntimeError("Не удалось получить конфиг из панели.")

    return name, cfg_text

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST)
async def request_cmd(update, context):
    await update.message.reply_text(
        "Выбери формат ключа:\n"
        "/request_qr — QR-код\n"
        "/request_text — текст\n"
        "/request_config — файл .conf"
    )

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST)
async def request_text_cmd(update, context):
    name, cfg_text = await _ensure_and_get_config(update, context)
    safe = html.escape(cfg_text)
    await update.message.reply_text(
        f"<pre>{safe}</pre>\n"
        "✅ Копируй и вставляй в AmneziaVPN.\n"
        "Или используй:\n"
        "/request_qr - для получения QR-кода\n"
        "/request_config - для получения конфиг-файла\n"
        "/help - для справки",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST)
async def request_config_cmd(update, context):
    name, cfg_text = await _ensure_and_get_config(update, context)
    bio = BytesIO(cfg_text.encode("utf-8"))
    bio.name = f"{name}.conf"
    bio.seek(0)
    await update.message.reply_document(document=bio, caption="✅ Скачай и импортируй в AmneziaVPN.\n"
                                        "Или используй:\n"
                                        "/request_qr - для получения QR-кода\n"
                                        "/request_text - для получения текстового ключа\n"
                                        "/help - для справки")

@tg_error_guard
@private_only
@with_role
@require_roles(Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST)
async def request_qr_cmd(update, context):
    # гарантируем, что профиль есть (создастся при необходимости)
    name, _cfg_text = await _ensure_and_get_config(update, context)

    panel = context.application.bot_data["panel"]
    tg_id = update.effective_user.id

    prof = get_profile(tg_id)
  
    if not prof or not prof.get("client_id"):
        await update.message.reply_text("❌ Не нашёл client_id в профиле. Попробуй /request_config.")
        return

    client_id = int(prof["client_id"])

    try:
        png_bytes = panel.get_client_qr_png(client_id)
    except Exception as e:
        await update.message.reply_text(
            "❌ QR не удалось получить/распознать.\n"
            "Используй /request_config или /request_text.\n"
            f"Причина: {type(e).__name__}: {e}"
        )
        return

    #png_bytes = panel.get_client_qr_png(client_id)

    bio = BytesIO(png_bytes)
    bio.name = f"{name}.png"
    bio.seek(0)

    await update.message.reply_photo(photo=bio, caption=f"✅ Сканируй QR-код через AmneziaVPN.\n"
                                     "Или используй:\n"
                                     "/request_config - для получения конфиг-файла\n"
                                     "/request_text - для получения текствого ключа\n"
                                     "/help - для справки")




