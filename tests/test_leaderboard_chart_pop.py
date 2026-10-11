"""Leaderboard rows carry each player's talent_alloc so hovering TP can show their Chart."""
import uuid

import psycopg2
import requests


def test_leaderboard_rows_include_talent_alloc(server_url, db_url):
    username = f'lbc{uuid.uuid4().hex[:8]}'
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            # Leaderboard hides 127.0.0.1 users, so seed this one off localhost and at the top.
            cur.execute("INSERT INTO users (username, password_hash, ip_address) VALUES (%s, 'x', '10.0.0.9') RETURNING id",
                        (username,))
            uid = cur.fetchone()[0]
            cur.execute('''INSERT INTO game_state (user_id, wins, talent_alloc)
                           VALUES (%s, 10000000, '{"undertow": 2}')''', (uid,))
        rows = requests.get(f'{server_url}/api/leaderboard').json()
        row = next(r for r in rows if r['username'] == username)
        assert row['talent_alloc'] == {'undertow': 2}
    finally:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM game_state WHERE user_id = (SELECT id FROM users WHERE username = %s)', (username,))
            cur.execute('DELETE FROM users WHERE username = %s', (username,))
        conn.close()
