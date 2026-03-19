import logging
from datetime import datetime, timezone

from flask import request, jsonify

from models import LOCKOUT_RULES

log = logging.getLogger('wheel')


def check_lockout(conn, identifier):
    """Return seconds remaining in lockout (0 = not locked)."""
    with conn.cursor() as cur:
        cur.execute(
            '''SELECT COUNT(*), MAX(attempted_at)
               FROM login_attempts
               WHERE identifier = %s AND success = FALSE
                 AND attempted_at > NOW() - INTERVAL '1 hour' ''',
            (identifier,),
        )
        row = cur.fetchone()
    fail_count = row[0] or 0
    last_fail = row[1]
    if not last_fail or fail_count == 0:
        return 0
    for threshold, lock_secs in LOCKOUT_RULES:
        if fail_count >= threshold:
            elapsed = (datetime.now(timezone.utc) - last_fail).total_seconds()
            remaining = lock_secs - elapsed
            return max(0, int(remaining))
    return 0


def record_attempt(conn, identifier, success):
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO login_attempts (identifier, success) VALUES (%s, %s)',
            (identifier, success),
        )


def clear_attempts(conn, identifier):
    with conn.cursor() as cur:
        cur.execute('DELETE FROM login_attempts WHERE identifier = %s', (identifier,))


def require_json():
    if request.method == 'POST' and not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    return None
