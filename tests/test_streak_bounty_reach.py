"""bounty_streak10 completes at any streak >= 10, on manual and auto spins."""
import datetime as dt
import os
import re
import uuid

import psycopg2

from bounties import reach_bounty

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_reach_bounty_completes_once(db_url):
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    day = dt.date(2026, 10, 11)
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (username, password_hash, ip_address) VALUES (%s, 'x', '127.0.0.1') RETURNING id",
                        (f'sb{uuid.uuid4().hex[:8]}',))
            uid = cur.fetchone()[0]
        reach_bounty(conn, uid, 'bounty_streak10', day)
        with conn.cursor() as cur:
            cur.execute('SELECT progress, completed, completed_at FROM bounty_progress WHERE user_id = %s', (uid,))
            first = cur.fetchone()
        reach_bounty(conn, uid, 'bounty_streak10', day)
        with conn.cursor() as cur:
            cur.execute('SELECT progress, completed, completed_at FROM bounty_progress WHERE user_id = %s', (uid,))
            again = cur.fetchone()
        assert first[:2] == (10, True)
        assert again == first  # repeat calls don't move completed_at
    finally:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM bounty_progress WHERE user_id = %s', (uid,))
            cur.execute('DELETE FROM users WHERE id = %s', (uid,))
        conn.close()


def test_both_spin_paths_use_threshold_not_exact_match():
    src = open(os.path.join(REPO, 'game.py')).read()
    calls = re.findall(r"if events\.get\('streak', 0\) (>=|==) 10:\s+reach_bounty\(", src)
    assert calls == ['>=', '>='], calls  # /api/spin and /api/tick
