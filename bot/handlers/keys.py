import io

from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware import tg_error_guard
from app.services.panel import pick_server


@tg_error_guard
async def request_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panel = context.application.bot_data["panel"]
    tg_id = update.effective_user.id
    tg_username = update.effective_user.username or "no_username"
    name = f"tg_{tg_id}_{tg_username}"

    found = panel.find_client_by_name_any_server(name)
    if found:
        client_id = found["client"].get("id")
        if not client_id:
            await update.message.reply_text(f"Нашёл клиента, но без id: {found['client']}")
            return
        server_id = found["client"].get("server_id")
        print(f"Клиент уже есть: client_id={client_id}, name={name}")
        config_text = panel.get_client_config_text(int(client_id))
    else:
        # 2) иначе создаём на первом active сервере
        servers_json = panel.get_servers()
        srv = pick_server(servers_json)
        if not srv:
            await update.message.reply_text("Не вижу ни одного сервера в панели.")
            return

        server_id = srv.get("id")
        created = panel.create_client(int(server_id), name)
        client = created.get("client", {})
        client_id = client.get("id")
        if not client_id:
            await update.message.reply_text(f"Создал, но не нашёл client_id: {created}")
            return
        config_text = client.get("config") or panel.get_client_config_text(int(client_id))

    bio = io.BytesIO(config_text.encode("utf-8"))
    bio.name = f"{name}.conf"

    await update.message.reply_document(
        document=bio,
        filename=bio.name,
        caption=f"Готово ✅ server_id={server_id}, client_id={client_id}",
    )