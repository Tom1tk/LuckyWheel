"""anticheat.py against the real app and wheeldb_test: suspensions, browser strings,
banned-device registration and continuous-play flags."""
import uuid

import pytest

from tests.test_spin_integration import _read_csrf, _register, game_app  # noqa: F401

CHROME = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0 Safari/537.36'
REMOTE = {'REMOTE_ADDR': '203.0.113.7'}


def _sql(db_url, query, params=()):
    import psycopg2
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall() if cur.description else None
    finally:
        conn.close()


def _new_user(app, prefix, device=None):
    from extensions import limiter
    limiter.reset()
    client = app.test_client()
    if device:
        client.set_cookie('device_id', device)
    name = f'{prefix}{uuid.uuid4().hex[:8]}'
    status, body, _ = _register(client, name, 'testpass123')
    assert status == 201, body
    return client, name


def _ban(db_url, name, until="NOW() + interval '1 day'"):
    _sql(db_url, f"UPDATE users SET banned_until = {until}, ban_reason = 'automated play' WHERE username = %s", (name,))


def test_suspended_account_cannot_act_but_can_look_and_chat(game_app, db_url):  # noqa: F811
    client, name = _new_user(game_app, 'ban')
    _ban(db_url, name)
    h = {'X-CSRFToken': _read_csrf(client)}

    r = client.post('/api/spin', json={}, headers=h)
    assert r.status_code == 403
    body = r.get_json()
    assert body['suspended_until'] and 'suspended until' in body['error'] and '(automated play)' in body['error']
    assert client.post('/api/cast', json={}, headers=h).status_code == 403

    state = client.get('/api/state')
    assert state.status_code == 200
    assert state.get_json()['charts']['points'] == 0
    assert client.post('/api/chat', json={'message': 'hi'}, headers=h).status_code != 403


def test_expired_ban_lifts_itself(game_app, db_url):  # noqa: F811
    client, name = _new_user(game_app, 'unban')
    _ban(db_url, name, "NOW() - interval '1 second'")
    r = client.post('/api/spin', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code != 403


@pytest.mark.parametrize('ua', ['Mozilla/5.0 (X11; Linux x86_64) somebot/1.0', 'python-requests/2.34', 'curl/8.14', '',
                                'Mozilla/5.0 (X11; Linux x86_64) HeadlessChrome/149.0 Safari/537.36'])
def test_non_browser_clients_are_refused(game_app, ua):  # noqa: F811
    r = game_app.test_client().get('/api/me', headers={'User-Agent': ua}, environ_overrides=REMOTE)
    assert r.status_code == 403
    assert 'web browser' in r.get_json()['error']


def test_browsers_and_this_machine_are_allowed(game_app):  # noqa: F811
    c = game_app.test_client()
    assert c.get('/api/me', headers={'User-Agent': CHROME}, environ_overrides=REMOTE).status_code == 200
    assert c.get('/api/me', headers={'User-Agent': 'curl/8.14'}).status_code == 200  # 127.0.0.1


def test_banned_players_browser_cannot_register_a_new_account(game_app, db_url):  # noqa: F811
    device = uuid.uuid4().hex
    client, name = _new_user(game_app, 'cheat')
    client.set_cookie('device_id', device)
    client.get('/api/state')  # links this browser to the account
    assert _sql(db_url, 'SELECT 1 FROM user_devices d JOIN users u ON u.id = d.user_id '
                        'WHERE u.username = %s AND d.device_id = %s', (name, device))
    _ban(db_url, name)

    from extensions import limiter
    limiter.reset()
    alt = game_app.test_client()
    alt.set_cookie('device_id', device)
    csrf = alt.get('/api/me').get_json()['csrf_token']
    r = alt.post('/api/register', json={'username': f'alt{uuid.uuid4().hex[:8]}', 'password': 'testpass123'},
                 headers={'X-CSRFToken': csrf})
    assert r.status_code == 403
    assert "isn't available on this device" in r.get_json()['error']


def test_long_unbroken_manual_play_is_flagged_once(game_app, db_url):  # noqa: F811
    import anticheat
    client, name = _new_user(game_app, 'grind')
    _sql(db_url, "UPDATE users SET active_since = NOW() - interval '7 hours', "
                 "last_action_at = NOW() - interval '1 minute' WHERE username = %s", (name,))
    h = {'X-CSRFToken': _read_csrf(client)}
    for _ in range(2):
        anticheat._last_tracked.clear()
        client.post('/api/cast', json={}, headers=h)
    rows = _sql(db_url, "SELECT f.detail FROM cheat_flags f JOIN users u ON u.id = f.user_id "
                        "WHERE u.username = %s AND f.kind = 'continuous_play'", (name,))
    assert len(rows) == 1 and 'no 15-minute break' in rows[0][0]


def test_a_break_starts_a_new_run(game_app, db_url):  # noqa: F811
    import anticheat
    client, name = _new_user(game_app, 'rest')
    _sql(db_url, "UPDATE users SET active_since = NOW() - interval '7 hours', "
                 "last_action_at = NOW() - interval '20 minutes' WHERE username = %s", (name,))
    anticheat._last_tracked.clear()
    client.post('/api/cast', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    assert not _sql(db_url, 'SELECT 1 FROM cheat_flags f JOIN users u ON u.id = f.user_id WHERE u.username = %s', (name,))
    assert _sql(db_url, "SELECT active_since > NOW() - interval '1 minute' FROM users WHERE username = %s",
                (name,))[0][0]
