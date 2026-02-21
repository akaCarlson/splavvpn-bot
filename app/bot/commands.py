from dataclasses import dataclass
from app.services.access import Role

@dataclass(frozen=True)
class CommandSpec:
    name: str
    description: str
    visible_roles: set[Role]
    show_in_menu: bool = True  # можно скрыть из /start, но команда остаётся рабочей

@dataclass(frozen=True)
class SectionSpec:
    title: str
    visible_roles: set[Role]          # кто вообще видит раздел
    commands: list[CommandSpec]
    placeholder: str | None = None    # текст, если команд пока нет
    emoji: str = "⬇️"

def role_allows(role: Role, allowed: set[Role]) -> bool:
    # ADMIN видит всё
    if role == Role.ADMIN:
        return True
    return role in allowed

def _hdr(title: str, emoji: str) -> str:
    # аккуратная линия, читается одинаково в моноширинном и обычном шрифте
    line = "─"
    return f"{line} <b>{title}</b> {emoji}"

def build_start_menu(role: Role, sections: list[SectionSpec]) -> str:
    lines = ["<b>Команды:</b>"]
    any_visible = False

    for sec in sections:
        if not role_allows(role, sec.visible_roles):
            continue

        visible_cmds = [
            c for c in sec.commands
            if c.show_in_menu and role_allows(role, c.visible_roles)
        ]

        # если нет команд, но есть placeholder — всё равно показываем раздел
        if not visible_cmds and not sec.placeholder:
            continue

        any_visible = True
        lines.append(_hdr(sec.title, sec.emoji))

        for c in visible_cmds:
            lines.append(f"/{c.name} — {c.description}")

        if not visible_cmds and sec.placeholder:
            lines.append(sec.placeholder)

    if not any_visible:
        return "Команды недоступны. Проверь доступ."

    return "\n".join(lines)
