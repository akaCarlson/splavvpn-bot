from dataclasses import dataclass
from app.services.access import Role

@dataclass(frozen=True)
class HelpSpec:
    cmd: str                 # например "help_android"
    title: str               # человекочитаемый заголовок
    file_path: str           # путь в content/
    visible_roles: set[Role] # кто видит этот раздел

LEGIT = {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER, Role.INVITED_GUEST}
PAYERS = {Role.ADMIN, Role.MODERATOR, Role.CHAT_MEMBER, Role.BILLING_MEMBER}
ADMINS = {Role.ADMIN, Role.MODERATOR}

HELP_SPECS = [
    # Настройка клиента
    HelpSpec("help_android", "Настройка клиента: Android", "content/help/setup_android.html", LEGIT),
    HelpSpec("help_iphone", "Настройка клиента: iPhone/iOS", "content/help/setup_iphone.html", LEGIT),
    HelpSpec("help_windows", "Настройка клиента: Windows", "content/help/setup_windows.html", LEGIT),
    HelpSpec("help_macos", "Настройка клиента: macOS", "content/help/setup_macos.html", LEGIT),

    # Работа с ботом
    HelpSpec("help_bot", "Как работает бот (роли, ключи, инвайты)", "content/help/bot.html", LEGIT),

    # Биллинг (только плательщикам)
    HelpSpec("help_billing", "Биллинг и оплата", "content/help/billing.html", PAYERS),
]
