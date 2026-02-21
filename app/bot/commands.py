from dataclasses import dataclass
from typing import Callable, Iterable
from telegram.ext import Application, BaseHandler

from app.services.access import Role

@dataclass(frozen=True)
class CommandSpec:
    # то, что показываем пользователю
    name: str                 # например "request" или "request_qr"
    description: str
    visible_roles: set[Role]  # кто видит в /start
    # регистрация хендлера делается в router, тут просто "мета"

def role_allows(role: Role, allowed: set[Role]) -> bool:
    # ADMIN видит всё
    if role == Role.ADMIN:
        return True
    return role in allowed

def build_start_menu(role: Role, commands: list[CommandSpec]) -> str:
    visible = [c for c in commands if role_allows(role, c.visible_roles)]
    if not visible:
        return "Команды недоступны. Проверь доступ."

    lines = ["Команды:"]
    for c in visible:
        lines.append(f"/{c.name} — {c.description}")
    return "\n".join(lines)
