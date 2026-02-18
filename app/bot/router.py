from telegram.ext import Application, CommandHandler

from app.bot.handlers.common import start, health, my_id, status
from app.bot.handlers.servers import servers
from app.bot.handlers.keys import request_cmd

def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("my_id", my_id))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("servers", servers))
    app.add_handler(CommandHandler("request", request_cmd))
