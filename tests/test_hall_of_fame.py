"""RV-05: GET /api/hall-of-fame lists ended seasons/tides newest first with their
podiums, and counts medals for S9 tides (label 9.x) only.

Seeds committed rows (the app reads on its own connection) and deletes them after.
"""
import uuid

import psycopg2
import pytest

from tests.test_spin_integration import game_app  # noqa: F401

# internal season_numbers well clear of anything real
OLD, TIDE1, TIDE2 = 99001, 99002, 99003


@pytest.fixture()
def hof(db_url):
    suffix = uuid.uuid4().hex[:6]
    names = {k: f'hof{k}{suffix}' for k in ('a', 'b', 'c')}
    conn = psycopg2.connect(db_url)
    ids = {}
    try:
        with conn.cursor() as cur:
            for k, name in names.items():
                cur.execute("INSERT INTO users (username, password_hash, ip_address) "
                            "VALUES (%s, 'x', '192.0.2.9') RETURNING id", (name,))
                ids[k] = cur.fetchone()[0]
            cur.executemany(
                'INSERT INTO season_log (season_number, label, name, ended_at) '
                "VALUES (%s, %s, %s, NOW() - %s * INTERVAL '1 day')",
                [(OLD, '7', 'Old', 30), (TIDE1, '9.1', 'Tides', 14), (TIDE2, '9.2', 'Tides', 7)])
            podiums = {OLD: 'abc', TIDE1: 'abc', TIDE2: 'ba'}  # TIDE2: only two players
            for season, order in podiums.items():
                for pos, k in enumerate(order, 1):
                    cur.execute(
                        'INSERT INTO season_snapshots (season_number, position, user_id, username, wins, losses) '
                        'VALUES (%s, %s, %s, %s, %s, 0)', (season, pos, ids[k], names[k], 100 - pos))
        conn.commit()
        yield names
    finally:
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM season_snapshots WHERE season_number IN (%s, %s, %s)', (OLD, TIDE1, TIDE2))
            cur.execute('DELETE FROM season_log WHERE season_number IN (%s, %s, %s)', (OLD, TIDE1, TIDE2))
            cur.execute('DELETE FROM users WHERE id = ANY(%s)', (list(ids.values()),))
        conn.commit()
        conn.close()


def test_hall_of_fame_tides_and_medals(game_app, hof):  # noqa: F811
    from extensions import limiter
    limiter.reset()
    resp = game_app.test_client().get('/api/hall-of-fame')
    assert resp.status_code == 200
    body = resp.get_json()

    ours = [t for t in body['tides'] if t['label'] in ('7', '9.1', '9.2') and t['podium']
            and t['podium'][0]['username'] in hof.values()]
    assert [t['label'] for t in ours] == ['9.2', '9.1', '7']  # newest first
    assert ours[0]['podium'] == [
        {'position': 1, 'username': hof['b'], 'wins': 99},
        {'position': 2, 'username': hof['a'], 'wins': 98},
    ]
    assert ours[0]['ended_at']

    medals = {m['username']: (m['gold'], m['silver'], m['bronze'])
              for m in body['medals'] if m['username'] in hof.values()}
    # season 7 awards nothing; 9.1 = a,b,c; 9.2 = b,a
    assert medals == {hof['a']: (1, 1, 0), hof['b']: (1, 1, 0), hof['c']: (0, 0, 1)}
