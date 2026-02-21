from app.services.access import Role
from app.bot.commands import CommandSpec, SectionSpec

LEGIT = {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST}
PAYERS = {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER}
ADMINS = {Role.ADMIN, Role.MODERATOR}

MENU_SECTIONS = [
    SectionSpec(
        title="Запросить/показать ключ для AmneziaVPN",
        emoji="🔑",
        visible_roles=LEGIT,
        commands=[
            # /request оставляем рабочим, но НЕ показываем в меню
            CommandSpec("request_text", "получить текстовый ключ", LEGIT),
            CommandSpec("request_config", "получить файл .conf", LEGIT),
            CommandSpec("request_qr", "получить QR", LEGIT),
            CommandSpec("request", "меню форматов ключа", LEGIT, show_in_menu=False),
            
        ],
    ),
    SectionSpec(
        title="Пригласить друга",
        emoji="👥",
        visible_roles=PAYERS,
        commands=[
            CommandSpec("request_for", "создать ссылку-приглашение", PAYERS),
            CommandSpec("invite_create", "создать admin-invite", ADMINS),
        ],
    ),
    SectionSpec(
        title="Денежки",
        emoji="💰",
        visible_roles=PAYERS,
        commands=[],
        placeholder="(скоро: биллинг/напоминания/оплата)",
    ),
    SectionSpec(
        title="Вопросики",
        emoji="❓",
        visible_roles=LEGIT | {Role.NO_ACCESS},
        commands=[
            CommandSpec("status", "мой статус (бот + панель)", LEGIT),
            CommandSpec("help", "справка", LEGIT | {Role.NO_ACCESS}),
            CommandSpec("health", "проверка панели (служебное)", ADMINS),
        ],
    ),
    SectionSpec(
        title="Служебное",
        emoji="🛠️",
        visible_roles=ADMINS,
        commands=[
            CommandSpec("approve_activation", "одобрить активацию", ADMINS, show_in_menu=True),
            CommandSpec("reject_activation", "отклонить активацию", ADMINS, show_in_menu=True),
            CommandSpec("delete", "удалить пользователя (revoke+purge)", ADMINS, show_in_menu=True),
        ],
    ),
]
