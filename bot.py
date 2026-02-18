import os
from dotenv import load_dotenv
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from panel_client import PanelClient

#load_dotenv()

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)


BOT_TOKEN = os.environ["BOT_TOKEN"]
PANEL_BASE_URL = os.environ["PANEL_BASE_URL"]
PANEL_ADMIN_EMAIL = os.environ["PANEL_ADMIN_EMAIL"]
PANEL_ADMIN_PASSWORD = os.environ["PANEL_ADMIN_PASSWORD"]

panel = PanelClient(PANEL_BASE_URL, PANEL_ADMIN_EMAIL, PANEL_ADMIN_PASSWORD)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команды:\n/servers — список VPN-серверов")

async def servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = panel.get_servers()
    # аккуратно режем, чтобы не упереться в лимит Telegram
    text = str(data)
    if len(text) > 3500:
        text = text[:3500] + "..."
    await update.message.reply_text(text)

async def request_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    tg_username = update.effective_user.username or "no_username"
    name = f"tg_{tg_id}_{tg_username}"

    servers = panel.get_servers()
    # Подстройка под возможные форматы ответа
    items = servers.get("data") if isinstance(servers, dict) else servers
    if not items:
        await update.message.reply_text("Не вижу ни одного сервера в панели.")
        return

    server_id = items[0].get("id") if isinstance(items[0], dict) else None
    if not server_id:
        await update.message.reply_text(f"Не понял формат ответа /servers: {servers}")
        return

    created = panel.create_client(int(server_id), name)
    client_id = created.get("client_id") or created.get("id") or created.get("data", {}).get("id")

    if not client_id:
        await update.message.reply_text(f"Создал, но не нашёл client_id: {created}")
        return

    cfg = panel.get_client_config(int(client_id))
    config_text = cfg.get("config") or cfg.get("data") or str(cfg)

    await update.message.reply_document(
        document=config_text.encode("utf-8"),
        filename=f"{name}.conf",
        caption=f"Готово ✅ server_id={server_id}, client_id={client_id}"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("servers", servers))
    app.add_handler(CommandHandler("request", request_cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
