"""RV-06 (Season 9): prestige, loadouts, singularity and aquarium are retired.

Runs the real app against the real test DB (wheeldb_test):
  - the eight retired routes answer 410 for a logged-in user
  - /api/buy refuses prestige_unlock and aquarium with 403
  - /api/buy still sells a functional item
  - /api/leaderboard ranks by wins and no longer returns prestige_level
"""
import uuid

import pytest

from tests.test_spin_integration import (  # noqa: F401
    _read_csrf,
    _register,
    _set_columns,
    _set_owned,
    game_app,
)

RETIRED_ROUTES = [
    ('GET', '/api/prestige'),
    ('POST', '/api/prestige'),
    ('GET', '/api/singularity'),
    ('POST', '/api/singularity/contribute'),
    ('GET', '/api/loadout'),
    ('POST', '/api/loadout'),
    ('POST', '/api/loadout/apply'),
    ('GET', '/api/aquarium'),
]
RETIRED_BODY = {'error': 'Retired in Season 9.'}
RETIRED_SHOP_BODY = {'error': 'This item was retired in Season 9.'}
LB_WINS = (50, 20, 5)


@pytest.fixture(autouse=True)
def _fresh_rate_limiter(game_app):  # noqa: F811
    """/api/register and /api/leaderboard are rate-limited; start each test clean."""
    from extensions import limiter
    limiter.reset()
    yield


@pytest.fixture(scope='module')
def rv06_client(game_app):  # noqa: F811
    """One registered, logged-in client for the module (/api/register is 5/hour per IP)."""
    client = game_app.test_client()
    username = f'rv06{uuid.uuid4().hex[:8]}'
    status, body, _csrf = _register(client, username, 'testpass123')
    if status != 201:
        pytest.fail(f'module-level register failed: {status} {body}')
    return client, username


@pytest.fixture()
def lb_users(db_url):
    """Three users with wins 50/20/5 on a non-localhost IP, so the T241 filter keeps them."""
    import psycopg2
    suffix = uuid.uuid4().hex[:6]
    names = [f'rv06lb{wins}{suffix}' for wins in LB_WINS]
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for name, wins in zip(names, LB_WINS):
                cur.execute(
                    'INSERT INTO users (username, password_hash, ip_address) '
                    'VALUES (%s, %s, %s) RETURNING id',
                    (name, 'x', '192.0.2.1'),
                )
                cur.execute(
                    'INSERT INTO game_state (user_id, wins) VALUES (%s, %s)',
                    (cur.fetchone()[0], wins),
                )
        yield names
    finally:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM users WHERE username = ANY(%s)', (names,))
        conn.close()


def _owned_items(db_url, username):
    import psycopg2
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT owned_items FROM game_state '
                'WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                (username,),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


@pytest.mark.parametrize('method,path', RETIRED_ROUTES)
def test_retired_route_returns_410(rv06_client, method, path):
    client, _username = rv06_client
    r = client.open(path, method=method, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 410
    assert r.get_json() == RETIRED_BODY


@pytest.mark.parametrize('item_id', ['prestige_unlock', 'aquarium'])
def test_retired_shop_item_returns_403(rv06_client, item_id):
    client, _username = rv06_client
    r = client.post(
        '/api/buy',
        json={'item_id': item_id},
        headers={'X-CSRFToken': _read_csrf(client)},
    )
    assert r.status_code == 403
    assert r.get_json() == RETIRED_SHOP_BODY


def test_functional_item_still_sells(db_url, rv06_client):
    client, username = rv06_client
    _set_owned(db_url, username, [])
    _set_columns(db_url, username, wins=1000, cumulative_wins=1000)
    r = client.post(
        '/api/buy',
        json={'item_id': 'winmult_1'},
        headers={'X-CSRFToken': _read_csrf(client)},
    )
    assert r.status_code == 200, r.get_json()
    assert 'winmult_1' in _owned_items(db_url, username)


def test_leaderboard_ranks_by_wins_without_prestige(game_app, lb_users):  # noqa: F811
    r = game_app.test_client().get('/api/leaderboard')
    assert r.status_code == 200
    rows = r.get_json()
    assert all('prestige_level' not in row for row in rows)
    wins = [row['wins'] for row in rows]
    assert all(w > 0 for w in wins)
    assert wins == sorted(wins, reverse=True)
    seeded = [row['username'] for row in rows if row['username'] in lb_users]
    assert seeded == lb_users
