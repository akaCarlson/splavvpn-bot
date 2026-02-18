import os
import psycopg
from pathlib import Path
from dotenv import load_dotenv
from psycopg.rows import dict_row

'''# Всегда читаем .env рядом с bot.py и перезаписываем env vars
load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

DB_DSN = os.environ["BOT_DB_DSN"]

def get_conn():
    return psycopg.connect(DB_DSN, row_factory=dict_row)'''

'''def upsert_user(tg_id: int, username: str | None, role: str, status: str, inviter_tg_id: int | None = None):
    q = """
    insert into users (tg_id, username, role, status, inviter_tg_id)
    values (%s, %s, %s, %s, %s)
    on conflict (tg_id) do update
      set username=excluded.username,
          role=excluded.role,
          status=excluded.status,
          inviter_tg_id=coalesce(users.inviter_tg_id, excluded.inviter_tg_id),
          updated_at=now()
    returning *
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q, (tg_id, username, role, status, inviter_tg_id))
            return cur.fetchone()

def get_user(tg_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("select * from users where tg_id=%s", (tg_id,))
            return cur.fetchone()'''

def create_invite(code: str, created_by: int, expires_at_iso: str):
    q = """
    insert into invites (code, created_by, status, expires_at)
    values (%s, %s, 'ACTIVE', %s::timestamptz)
    returning *
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q, (code, created_by, expires_at_iso))
            return cur.fetchone()

def get_invite(code: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("select * from invites where code=%s", (code,))
            return cur.fetchone()

def mark_invite_used(code: str, used_by: int):
    q = """
    update invites
       set status='USED', used_by=%s
     where code=%s
       and status='ACTIVE'
    returning *
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q, (used_by, code))
            return cur.fetchone()

def expire_invites():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("update invites set status='EXPIRED' where status='ACTIVE' and expires_at < now()")
