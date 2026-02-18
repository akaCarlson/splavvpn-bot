from app.db.conn import get_conn

def get_owner_for_guest(guest_tg_id: int) -> int | None:
    q = "select owner_tg_id from relationships where guest_tg_id=%s and status='ACTIVE'"
    with get_conn() as c, c.cursor() as cur:
        cur.execute(q, (guest_tg_id,))
        row = cur.fetchone()
        return int(row["owner_tg_id"]) if row else None
