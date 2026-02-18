import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# грузим .env из корня проекта
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)

@dataclass(frozen=True)
class Config:
    BOT_TOKEN: str
    PANEL_BASE_URL: str
    PANEL_ADMIN_EMAIL: str
    PANEL_ADMIN_PASSWORD: str
    ACCESS_CHAT_ID: int
    ADMIN_TG_IDS: set[int]
    INVITE_TTL_DAYS: int

def load_config() -> Config:
    return Config(
        BOT_TOKEN=os.environ["BOT_TOKEN"].strip(),
        PANEL_BASE_URL=os.environ["PANEL_BASE_URL"].strip(),
        PANEL_ADMIN_EMAIL=os.environ["PANEL_ADMIN_EMAIL"].strip(),
        PANEL_ADMIN_PASSWORD=os.environ["PANEL_ADMIN_PASSWORD"].strip(),
        ACCESS_CHAT_ID=int(os.environ["ACCESS_CHAT_ID"]),
        ADMIN_TG_IDS={int(x.strip()) for x in os.environ.get("ADMIN_TG_IDS", "").split(",") if x.strip()},
        INVITE_TTL_DAYS=int(os.environ.get("INVITE_TTL_DAYS", "7")),
    )
