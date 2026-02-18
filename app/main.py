from telegram.ext import Application

from app.config import load_config
from bot.router import register_handlers
from app.services.panel import PanelClient

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



