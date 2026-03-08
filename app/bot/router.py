from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.bot.handlers.common import  health, my_id, status
from app.bot.handlers.servers import servers
from app.bot.handlers.admin_delete import delete_user_cmd
from app.bot.handlers.keys import (
    request_cmd,
    request_text_cmd,
    request_config_cmd,
    request_qr_cmd
)
from app.bot.handlers.invites import (
    invite_create,
    start_payload,
    approve_activation_cmd,
    reject_activation_cmd,
    request_for_cmd
)
from app.bot.handlers.help import (
    help_cmd, 
    help_android, 
    help_iphone, 
    help_windows, 
    help_macos,
    help_bot,
    help_billing
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
    app.add_handler(MessageHandler(filters.Regex(r"^/request_text$"), request_text_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/request_config$"), request_config_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/request_qr$"), request_qr_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/approve_activation_\d+$"), approve_activation_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/reject_activation_\d+$"), reject_activation_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/delete_\d+$"), delete_user_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("help_android", help_android))
    app.add_handler(CommandHandler("help_iphone", help_iphone))
    app.add_handler(CommandHandler("help_windows", help_windows))
    app.add_handler(CommandHandler("help_macos", help_macos))
    app.add_handler(CommandHandler("help_bot", help_bot))
    app.add_handler(CommandHandler("help_billing", help_billing))


