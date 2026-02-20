from app.db.conn import get_conn

def get_profile(tg_id: int):
    with get_conn() as c, c.cursor() as cur:
        cur.execute("select * from profiles where tg_id=%s", (tg_id,))
        return cur.fetchone()

def upsert_profile(tg_id: int, server_id: int, client_id: int, name: str):
    q = """
    insert into profiles (tg_id, server_id, client_id, name)
    values (%s, %s, %s, %s)
    on conflict (tg_id) do update
      set server_id=excluded.server_id,
          client_id=excluded.client_id,
          name=excluded.name,
          updated_at=now()
    returning *
    """
    with get_conn() as c, c.cursor() as cur:
        cur.execute(q, (tg_id, server_id, client_id, name))
        return cur.fetchone()
