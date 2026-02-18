from telegram.ext import Application, CommandHandler

import app
from app.bot.handlers.common import  health, my_id, status
from app.bot.handlers.servers import servers
from app.bot.handlers.keys import request_cmd
from app.bot.handlers.invites import (
    invite_create,
    start_payload,
    approve_activation_cmd,
    reject_activation_cmd,
)

START_MENU = (
    "Команды:\n"
            "/request — получить ключ (конфиг) для себя\n"
            "/servers — список VPN-серверов\n"
            "/status — статус своего клиента и сервера\n"
            "/servers - покажет список серверов в панели\n"
            "/invite_create - команда для админов, создаёт инвайт-ссылку для вступления в клубной чат\n"
            "/approve_activation - команда для админов, одобрить заявку на доступ\n"
            "/reject_activation - команда для админов, отклонить заявку на доступ\n"
            "/health — проверить статус панели  (служебное)\n"
            "/my_id — узнать свой Telegram ID и username (служебное)\n"
)

def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_payload))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("my_id", my_id))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("servers", servers))
    app.add_handler(CommandHandler("request", request_cmd))
    app.add_handler(CommandHandler("invite_create", invite_create))
    app.add_handler(CommandHandler("approve_activation", approve_activation_cmd))
    app.add_handler(CommandHandler("reject_activation", reject_activation_cmd))
