from app.db.conn import get_conn

def create_invite(code: str, invite_type: str, created_by_tg_id: int, owner_tg_id: int | None, expires_at_iso: str):
    q = """
    insert into invites (code, type, created_by_tg_id, owner_tg_id, status, expires_at)
    values (%s, %s::invite_type, %s, %s, 'ACTIVE', %s::timestamptz)
    returning *
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(q, (code, invite_type, created_by_tg_id, owner_tg_id, expires_at_iso))
        return cur.fetchone()

def get_invite(code: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from invites where code=%s", (code,))
        return cur.fetchone()

def mark_invite_used(code: str, used_by_tg_id: int):
    q = """
    update invites
       set status='USED', used_by_tg_id=%s
     where code=%s
       and status='ACTIVE'
       and expires_at >= now()
    returning *
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(q, (used_by_tg_id, code))
        return cur.fetchone()

def revoke_invite(code: str):
    q = "update invites set status='REVOKED' where code=%s and status='ACTIVE' returning *"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(q, (code,))
        return cur.fetchone()

def expire_invites():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("update invites set status='EXPIRED' where status='ACTIVE' and expires_at < now()")
