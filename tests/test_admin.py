"""admin.py against the real app and wheeldb_test: the admin API, account approval, closed accounts,
suspensions, the daily cast cap and the steady-timing flag."""
import uuid

from tests.test_spin_integration import _read_csrf, _register, game_app  # noqa: F401


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


def _make_admin(db_url, name):
    _sql(db_url, 'UPDATE users SET is_admin = TRUE WHERE username = %s', (name,))


def _require_approval(db_url, on: bool):
    _sql(db_url, "UPDATE app_settings SET value = %s WHERE key = 'require_approval'", ('true' if on else 'false',))


def _uid(db_url, name):
    return _sql(db_url, 'SELECT id FROM users WHERE username = %s', (name,))[0][0]


def test_admin_api_is_hidden_from_players(game_app):  # noqa: F811
    client, _ = _new_user(game_app, 'norm')
    h = {'X-CSRFToken': _read_csrf(client)}
    assert client.get('/api/admin/overview').status_code == 404
    assert client.post('/api/admin/approve', json={'user_id': 1}, headers=h).status_code == 404
    assert game_app.test_client().get('/api/admin/overview').status_code in (401, 404)


def test_new_signup_waits_for_approval(game_app, db_url):  # noqa: F811
    admin, admin_name = _new_user(game_app, 'boss')
    _make_admin(db_url, admin_name)
    _require_approval(db_url, True)
    try:
        client, name = _new_user(game_app, 'wait')
        h = {'X-CSRFToken': _read_csrf(client)}

        state = client.get('/api/state')
        assert state.status_code == 200
        assert 'waiting for an admin' in state.get_json()['notice']
        r = client.post('/api/spin', json={}, headers=h)
        assert r.status_code == 403 and r.get_json()['restricted'] is True
        assert client.post('/api/chat', json={'message': 'hi'}, headers=h).status_code == 403

        r = admin.post('/api/admin/approve', json={'user_id': _uid(db_url, name)},
                       headers={'X-CSRFToken': _read_csrf(admin)})
        assert r.status_code == 200
        assert client.post('/api/spin', json={}, headers=h).status_code != 403
        assert client.get('/api/state').get_json()['notice'] is None
    finally:
        _require_approval(db_url, False)


def test_overview_lists_pending_with_device_and_matches(game_app, db_url):  # noqa: F811
    d1, d2 = uuid.uuid4().hex, uuid.uuid4().hex
    fp = {'platform': 'Win32', 'tz': 'Europe/London', 'screen': '1920x1080', 'dpr': 1, 'cores': 8,
          'gpu': 'ANGLE (NVIDIA)', 'canvas': 'abc123', 'evil': 'x' * 5000}
    admin, admin_name = _new_user(game_app, 'boss')
    _make_admin(db_url, admin_name)
    a_client, a_name = _new_user(game_app, 'ban', device=d1)
    r = a_client.post('/api/fingerprint', json={'fp': fp}, headers={'X-CSRFToken': _read_csrf(a_client)})
    assert r.status_code == 200
    _ban(db_url, a_name)

    _require_approval(db_url, True)
    try:
        b_client, b_name = _new_user(game_app, 'pend', device=d2)
        r = b_client.post('/api/fingerprint', json={'fp': fp}, headers={'X-CSRFToken': _read_csrf(b_client)})
        assert r.status_code == 200
        body = admin.get('/api/admin/overview').get_json()
    finally:
        _require_approval(db_url, False)

    pending = {p['username']: p for p in body['pending']}
    players = {p['username']: p for p in body['players']}
    assert b_name in pending and b_name not in players
    device = pending[b_name]['devices'][0]
    assert 'evil' not in device['fp'] and device['fp']['gpu'] == 'ANGLE (NVIDIA)'
    assert any(m['username'] == a_name and 'fingerprint' in m['via'] and m['suspended'] is True
               for m in pending[b_name]['matches'])
    assert players[a_name]['banned_until'] is not None
    assert body['settings']['require_approval'] is True
    assert body['settings']['daily_cast_limit'] == 1000


def test_reject_closes_account_and_its_browser(game_app, db_url):  # noqa: F811
    device = uuid.uuid4().hex
    admin, admin_name = _new_user(game_app, 'boss')
    _make_admin(db_url, admin_name)
    approved_client, approved_name = _new_user(game_app, 'okay')
    _require_approval(db_url, True)
    try:
        client, name = _new_user(game_app, 'rej', device=device)
        client.get('/api/state')  # links this browser to the account

        h_admin = {'X-CSRFToken': _read_csrf(admin)}
        assert admin.post('/api/admin/reject', json={'user_id': _uid(db_url, name)}, headers=h_admin).status_code == 200
        r = client.post('/api/spin', json={}, headers={'X-CSRFToken': _read_csrf(client)})
        assert r.status_code == 403 and 'has been closed' in r.get_json()['error']

        from extensions import limiter
        limiter.reset()
        alt = game_app.test_client()
        alt.set_cookie('device_id', device)
        csrf = alt.get('/api/me').get_json()['csrf_token']
        r = alt.post('/api/register', json={'username': f'alt{uuid.uuid4().hex[:8]}', 'password': 'testpass123'},
                     headers={'X-CSRFToken': csrf})
        assert r.status_code == 403
        assert "isn't available on this device" in r.get_json()['error']

        r = admin.post('/api/admin/reject', json={'user_id': _uid(db_url, approved_name)}, headers=h_admin)
        assert r.status_code == 409
    finally:
        _require_approval(db_url, False)


def test_suspend_and_lift(game_app, db_url):  # noqa: F811
    admin, admin_name = _new_user(game_app, 'boss')
    _make_admin(db_url, admin_name)
    player, player_name = _new_user(game_app, 'sus')
    uid = _uid(db_url, player_name)
    h_admin = {'X-CSRFToken': _read_csrf(admin)}
    h = {'X-CSRFToken': _read_csrf(player)}

    r = admin.post('/api/admin/suspend', json={'user_id': uid, 'reason': ''}, headers=h_admin)
    assert r.status_code == 400 and 'Give a reason' in r.get_json()['error']
    assert admin.post('/api/admin/suspend', json={'user_id': uid, 'reason': 'testing'},
                      headers=h_admin).status_code == 200
    r = player.post('/api/spin', json={}, headers=h)
    assert r.status_code == 403 and '(testing)' in r.get_json()['error']

    assert admin.post('/api/admin/unsuspend', json={'user_id': uid}, headers=h_admin).status_code == 200
    assert player.post('/api/spin', json={}, headers=h).status_code != 403

    _, other_name = _new_user(game_app, 'boss')
    _make_admin(db_url, other_name)
    r = admin.post('/api/admin/suspend', json={'user_id': _uid(db_url, other_name), 'reason': 'testing'},
                   headers=h_admin)
    assert r.status_code == 409


def test_settings_toggle(game_app, db_url):  # noqa: F811
    admin, admin_name = _new_user(game_app, 'boss')
    _make_admin(db_url, admin_name)
    h = {'X-CSRFToken': _read_csrf(admin)}
    try:
        r = admin.post('/api/admin/settings', json={'require_approval': 'yes'}, headers=h)
        assert r.status_code == 400 and 'require_approval must be' in r.get_json()['error']
        assert admin.post('/api/admin/settings', json={'require_approval': True}, headers=h).status_code == 200
        assert admin.get('/api/admin/overview').get_json()['settings']['require_approval'] is True
    finally:
        _require_approval(db_url, False)


def test_daily_cast_limit(game_app, db_url):  # noqa: F811
    client, name = _new_user(game_app, 'cap')
    uid = _uid(db_url, name)
    _sql(db_url, "INSERT INTO fishing_days (user_id, day, casts, last_cast_at) "
                 "VALUES (%s, (NOW() AT TIME ZONE 'Europe/London')::date, 1000, NOW())", (uid,))
    h = {'X-CSRFToken': _read_csrf(client)}

    r = client.post('/api/cast', json={}, headers=h)
    assert r.status_code == 429 and 'daily limit' in r.get_json()['error']
    assert _sql(db_url, "SELECT COUNT(*) FROM cheat_flags WHERE user_id = %s AND kind = 'daily_cap'", (uid,))[0][0] == 1

    r = client.post('/api/cast', json={}, headers=h)
    assert r.status_code == 429 and 'daily limit' in r.get_json()['error']
    assert _sql(db_url, "SELECT COUNT(*) FROM cheat_flags WHERE user_id = %s AND kind = 'daily_cap'", (uid,))[0][0] == 1


def test_steady_cast_timing_is_flagged(game_app, db_url):  # noqa: F811
    client, name = _new_user(game_app, 'steady')
    uid = _uid(db_url, name)
    _sql(db_url, "INSERT INTO fishing_days (user_id, day, casts, last_cast_at, gap_n, gap_mean, gap_m2) "
                 "VALUES (%s, (NOW() AT TIME ZONE 'Europe/London')::date, 1, NOW() - interval '10 seconds', 99, 10, 0.5)",
         (uid,))
    client.post('/api/cast', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    assert _sql(db_url, "SELECT 1 FROM cheat_flags WHERE user_id = %s AND kind = 'steady_timing'", (uid,))
    assert _sql(db_url, "SELECT gap_n FROM fishing_days WHERE user_id = %s "
                        "AND day = (NOW() AT TIME ZONE 'Europe/London')::date", (uid,))[0][0] == 0

    # Same mean gap with a wider spread (CV 0.5): not flagged.
    human, human_name = _new_user(game_app, 'human')
    human_uid = _uid(db_url, human_name)
    _sql(db_url, "INSERT INTO fishing_days (user_id, day, casts, last_cast_at, gap_n, gap_mean, gap_m2) "
                 "VALUES (%s, (NOW() AT TIME ZONE 'Europe/London')::date, 1, NOW() - interval '10 seconds', 99, 10, %s)",
         (human_uid, 99 * 25))
    human.post('/api/cast', json={}, headers={'X-CSRFToken': _read_csrf(human)})
    assert not _sql(db_url, "SELECT 1 FROM cheat_flags WHERE user_id = %s AND kind = 'steady_timing'", (human_uid,))


def test_spoofed_forwarded_for_is_not_local(game_app):  # noqa: F811
    r = game_app.test_client().get('/api/me', headers={'User-Agent': 'curl/8', 'X-Forwarded-For': '127.0.0.1'})
    assert r.status_code == 403
    assert 'web browser' in r.get_json()['error']


def test_fingerprint_needs_device_cookie(game_app):  # noqa: F811
    client, _ = _new_user(game_app, 'nodev')
    # The register flow never sets the device cookie (only GET / does), so there is usually nothing to delete.
    if client.get_cookie('device_id'):
        client.delete_cookie('device_id')
    r = client.post('/api/fingerprint', json={'fp': {'platform': 'Win32'}},
                    headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 400 and r.get_json()['error'] == 'No device cookie'


OFFSITE = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) Chrome/130', 'X-Forwarded-For': '203.0.113.7'}


def test_manual_spins_are_paced_like_auto_spin(game_app, db_url):  # noqa: F811
    client, name = _new_user(game_app, 'fast')
    h = {**OFFSITE, 'X-CSRFToken': _read_csrf(client)}
    assert client.post('/api/spin', json={}, headers=h).status_code == 200
    r = client.post('/api/spin', json={}, headers=h)
    assert r.status_code == 429 and 'still spinning' in r.get_json()['error']
    uid = _uid(db_url, name)
    _sql(db_url, "UPDATE game_state SET last_spin_at = NOW() - interval '2.5 seconds' WHERE user_id = %s", (uid,))
    assert client.post('/api/spin', json={}, headers=h).status_code == 429
    _sql(db_url, "UPDATE game_state SET last_spin_at = NOW() - interval '3.1 seconds' WHERE user_id = %s", (uid,))
    assert client.post('/api/spin', json={}, headers=h).status_code == 200
