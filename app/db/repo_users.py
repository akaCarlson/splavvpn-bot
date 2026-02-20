from app.db.conn import get_conn

def upsert_user(tg_id: int, username: str | None):
    q = """
    insert into users (tg_id, username) values (%s, %s)
    on conflict (tg_id) do update
      set username=excluded.username, updated_at=now()
    returning *
    """
    with get_conn() as c, c.cursor() as cur:
        cur.execute(q, (tg_id, username))
        return cur.fetchone()

def get_user(tg_id: int):
    with get_conn() as c, c.cursor() as cur:
        cur.execute("select * from users where tg_id=%s", (tg_id,))
        return cur.fetchone()

def get_user_by_username(username: str):
    # username храним без @ (как приходит от Telegram)
    q = "select * from users where lower(username)=lower(%s) limit 1"
    with get_conn() as c, c.cursor() as cur:
        cur.execute(q, (username,))
        return cur.fetchone()

def delete_user(tg_id: int):
    # каскады сделают остальное (profiles, key_requests, billing_members, relationships, etc.)
    q = "delete from users where tg_id=%s returning *"
    with get_conn() as c, c.cursor() as cur:
        cur.execute(q, (tg_id,))
        return cur.fetchone()

