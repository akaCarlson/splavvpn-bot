from app.db.conn import get_conn

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