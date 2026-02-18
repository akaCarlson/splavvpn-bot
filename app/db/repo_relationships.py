from app.db.conn import get_conn

def upsert_relationship(guest_tg_id: int, owner_tg_id: int):
    q = """
    insert into relationships (guest_tg_id, owner_tg_id, status)
    values (%s, %s, 'ACTIVE')
    on conflict (guest_tg_id) do update
      set owner_tg_id=excluded.owner_tg_id, status='ACTIVE'
    returning *
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(q, (guest_tg_id, owner_tg_id))
        return cur.fetchone()

def get_owner_for_guest(guest_tg_id: int) -> int | None:
    q = "select owner_tg_id from relationships where guest_tg_id=%s and status='ACTIVE'"
    with get_conn() as c, c.cursor() as cur:
        cur.execute(q, (guest_tg_id,))
        row = cur.fetchone()
        return int(row["owner_tg_id"]) if row else None
