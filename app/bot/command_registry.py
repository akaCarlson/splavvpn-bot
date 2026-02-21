from app.services.access import Role
from app.bot.commands import CommandSpec

COMMAND_SPECS = [
    CommandSpec("request", "получить меню форматов ключа", {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST}),
    CommandSpec("request_qr", "получить QR", {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST}),
    CommandSpec("request_text", "получить текст", {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST}),
    CommandSpec("request_config", "получить файл .conf", {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST}),
    CommandSpec("status", "мой статус (бот + панель)", {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST}),
    CommandSpec("help", "справка", {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST, Role.NO_ACCESS}),

    CommandSpec("request_for", "создать гостевой инвайт", {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER}),

    CommandSpec("invite_create", "создать admin-invite", {Role.ADMIN, Role.MODERATOR}),
    CommandSpec("approve_activation", "одобрить активацию (служебное)", {Role.ADMIN, Role.MODERATOR}),
    CommandSpec("reject_activation", "отклонить активацию (служебное)", {Role.ADMIN, Role.MODERATOR}),
    CommandSpec("health", "проверка панели (служебное)", {Role.ADMIN, Role.MODERATOR}),
    CommandSpec("delete_<tg_id>", "удалить пользователя (служебное)", {Role.ADMIN, Role.MODERATOR}),
]
