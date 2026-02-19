from telegram.ext import Application, CommandHandler, MessageHandler, filters

import app
from app.bot.handlers.common import  health, my_id, status
from app.bot.handlers.servers import servers
from app.bot.handlers.keys import request_cmd
from app.bot.handlers.invites import (
    invite_create,
    start_payload,
    approve_activation_cmd,
    reject_activation_cmd,
    request_for_cmd
)

START_MENU = (
    "Команды:\n"
            "/request — получить ключ (конфиг) для себя\n" \
            "/request_for — создать гостевой инвайт для другого пользователя\n"
            "/servers — список VPN-серверов\n"
            "/status — статус своего клиента и сервера\n"
            "/invite_create - создаёт инвайт-ссылку для вступления в клубной чат (служебное)\n"
            "/approve_activation - одобрить заявку на доступ (служебное)\n"
            "/reject_activation - отклонить заявку на доступ (служебное)\n"
            "/health — проверить статус панели (служебное)\n"
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
    app.add_handler(CommandHandler("request_for", request_for_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/approve_activation_\d+$"), approve_activation_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/reject_activation_\d+$"), reject_activation_cmd))
    #app.add_handler(CommandHandler("approve_activation", approve_activation_cmd))
    #app.add_handler(CommandHandler("reject_activation", reject_activation_cmd))
