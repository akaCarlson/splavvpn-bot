from app.db.conn import get_conn

def is_billing_member(tg_id: int) -> bool:
    with get_conn() as c, c.cursor() as cur:
        cur.execute("select 1 from billing_members where tg_id=%s", (tg_id,))
        return cur.fetchone() is not None

def set_billing_member(tg_id: int, activated_by_tg_id: int | None):
    q = """
    insert into billing_members (tg_id, activated_by_tg_id)
    values (%s, %s)
    on conflict (tg_id) do update
      set activated_by_tg_id=excluded.activated_by_tg_id,
          activated_at=now()
    returning *
    """
    with get_conn() as c, c.cursor() as cur:
        cur.execute(q, (tg_id, activated_by_tg_id))
        return cur.fetchone()
