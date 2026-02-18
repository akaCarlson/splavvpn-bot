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
