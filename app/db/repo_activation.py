from app.db.conn import get_conn

def create_activation_request(tg_id: int, invite_code: str):
    q = """
    insert into activation_requests (tg_id, invite_code, status)
    values (%s, %s, 'PENDING')
    returning *
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(q, (tg_id, invite_code))
        return cur.fetchone()

def get_pending_request_for_user(tg_id: int):
    q = "select * from activation_requests where tg_id=%s and status='PENDING' order by id desc limit 1"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(q, (tg_id,))
        return cur.fetchone()

def get_request(req_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from activation_requests where id=%s", (req_id,))
        return cur.fetchone()

def approve_request(req_id: int, decided_by_tg_id: int):
    q = """
    update activation_requests
       set status='APPROVED', decided_by_tg_id=%s, decided_at=now()
     where id=%s and status='PENDING'
    returning *
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(q, (decided_by_tg_id, req_id))
        return cur.fetchone()

def reject_request(req_id: int, decided_by_tg_id: int):
    q = """
    update activation_requests
       set status='REJECTED', decided_by_tg_id=%s, decided_at=now()
     where id=%s and status='PENDING'
    returning *
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(q, (decided_by_tg_id, req_id))
        return cur.fetchone()
