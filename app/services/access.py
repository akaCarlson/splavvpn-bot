from enum import Enum
from telegram.ext import ContextTypes

from app.db.repo_billing import is_billing_member
from app.db.repo_relationships import get_owner_for_guest

class Role(str, Enum):
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    CHAT_MEMBER = "CHAT_MEMBER"
    BILLING_MEMBER = "BILLING_MEMBER"
    INVITED_GUEST = "INVITED_GUEST"
    NO_ACCESS = "NO_ACCESS"


async def is_chat_member(context: ContextTypes.DEFAULT_TYPE, chat_id: int, tg_id: int) -> bool:
    m = await context.bot.get_chat_member(chat_id=chat_id, user_id=tg_id)
    return m.status in ("member", "administrator", "creator")


async def get_effective_role(context: ContextTypes.DEFAULT_TYPE, tg_id: int) -> tuple[Role, dict]:
    """
    Returns (role, extra), where extra can include owner_tg_id for INVITED_GUEST.
    """
    cfg = context.application.bot_data["cfg"]

    # 1) ADMIN / MODERATOR from config
    if tg_id in cfg.ADMIN_TG_IDS:
        return Role.ADMIN, {}
    if hasattr(cfg, "MODERATOR_TG_IDS") and tg_id in cfg.MODERATOR_TG_IDS:
        return Role.MODERATOR, {}

    # 2) CHAT_MEMBER via Telegram chat membership
    if await is_chat_member(context, cfg.ACCESS_CHAT_ID, tg_id):
        return Role.CHAT_MEMBER, {}

    # 3) BILLING_MEMBER via DB
    if is_billing_member(tg_id):
        return Role.BILLING_MEMBER, {}

    # 4) INVITED_GUEST via relationship
    owner = get_owner_for_guest(tg_id)
    if owner:
        return Role.INVITED_GUEST, {"owner_tg_id": owner}

    return Role.NO_ACCESS, {}
