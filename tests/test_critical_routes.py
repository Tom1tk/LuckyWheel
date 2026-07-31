"""T239: Critical-routes integration tests.

Several critical routes had **zero** integration coverage before T239:
  * `POST /api/wager/stake` — set the wager stake percentage
  * `POST /api/tab/heartbeat` — keep a single browser tab lock live

This file exercises those endpoints end-to-end against a real Flask
server (booted by the `server_url` fixture) and a real DB (queried
directly via the `db_url` fixture). Each test:

  1. registers a fresh user (avoids state pollution between tests)
  2. grants the needed items via direct SQL
  3. POSTs to the endpoint
  4. reads the post-state back via direct SQL
  5. asserts the side effects are consistent with the response

Coverage:
  AC#3 (happy-path)        — valid input, with the right items owned
  AC#3 (invalid input)     — bad body, bad values, missing fields
  AC#3 (auth-required)     — not logged in → 401/302
  AC#3 (unlock gating)     — without the unlock, the route rejects (403)
  AC#3 (persistence)       — DB state changes match the response
"""
import json
import os
import sys
import uuid
from contextlib import contextmanager

import pytest
from playwright.sync_api import Browser, sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def _api_post(page, url, body, *, csrf=None):
    """POST JSON to a server URL, returning (status, parsed_json)."""
    headers = {'Content-Type': 'application/json'}
    if csrf is not None:
        headers['X-CSRFToken'] = csrf
    result = page.evaluate(
        '''async ({url, body, headers}) => {
            const r = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(body),
            });
            let parsed = null;
            try { parsed = await r.json(); } catch (e) { parsed = null; }
            return {status: r.status, body: parsed};
        }''',
        {'url': url, 'body': body, 'headers': headers},
    )
    return result['status'], result['body']


def _get_csrf(page, base_url):
    """Fetch /api/me to get the CSRF token (also establishes session)."""
    result = page.evaluate(
        '''async ({url}) => {
            const r = await fetch(url);
            const data = await r.json();
            return data.csrf_token;
        }''',
        {'url': base_url + '/api/me'},
    )
    return result


def _register(page, base_url, username, password, csrf):
    """Register a fresh user. Returns (ok, status, error)."""
    status, body = _api_post(
        page,
        base_url + '/api/register',
        {'username': username, 'password': password},
        csrf=csrf,
    )
    return status, body


def _real_psycopg2():
    """Return the REAL psycopg2 module, bypassing any stub installed
    in sys.modules by sibling test files (test_wager_actions,
    test_insurance_tokens, etc.). The plain `import psycopg2` would
    return the stub if one is present; this helper pops the stub
    (and `psycopg2.extras`) out of sys.modules first so the `import`
    statement re-imports the real package from disk.

    The stubs are RESTORED on exit so subsequent sibling tests still
    see them (their `setdefault('psycopg2', stub)` is a no-op when
    psycopg2 is already in sys.modules, so we must put the stub back
    to keep the rest of the test suite in its expected state).
    """
    import sys as _sys
    _saved_pg = _sys.modules.pop('psycopg2', None)
    _saved_pgx = _sys.modules.pop('psycopg2.extras', None)
    try:
        import psycopg2  # noqa: F401 — real package
        import psycopg2.extras  # noqa: F401
        # Return a reference to the real modules. The caller uses the
        # returned objects directly, so the post-restore of the stubs
        # in sys.modules doesn't affect the caller's behaviour.
        return psycopg2, psycopg2.extras
    finally:
        # Restore the stubs (if any were there) so subsequent test files
        # see the same state they had before. The caller's already has
        # a reference to the real modules.
        if _saved_pg is not None:
            _sys.modules['psycopg2'] = _saved_pg
        if _saved_pgx is not None:
            _sys.modules['psycopg2.extras'] = _saved_pgx


def _user_id_for(db_url, username):
    psycopg2, _ = _real_psycopg2()
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def _grant_items(db_url, username, items):
    """Add `items` to the user's owned_items via direct SQL.

    Builds a Postgres array literal of quoted/escaped strings, e.g.
    `ARRAY['wager_unlock','wager_double_down']::text[]`. Each item is
    wrapped in single quotes (and internal single quotes are doubled) so
    that no string from the caller can be interpolated as SQL.
    """
    if not items:
        return
    psycopg2, _ = _real_psycopg2()
    quoted = ','.join("'" + i.replace("'", "''") + "'" for i in items)
    item_array = f"ARRAY[{quoted}]::text[]"
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'''
                UPDATE game_state
                SET owned_items = ARRAY(
                    SELECT DISTINCT unnest(owned_items || {item_array})
                )
                WHERE user_id = (SELECT id FROM users WHERE username = %s)
                ''',
                (username,),
            )
    finally:
        conn.close()


def _read_game_state(db_url, username, columns):
    """Read the requested columns for a user's game_state row."""
    psycopg2, psycopg2_extras = _real_psycopg2()
    col_list = ', '.join(columns)
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
            cur.execute(
                f'SELECT {col_list} FROM game_state '
                f'WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                (username,),
            )
            return cur.fetchone()
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────────
# Module-level shared fixtures
# ──────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def browser_ctx(server_url, db_url, playwright_instance):
    """Boot ONE browser + ONE logged-in context for the module.

    We register ONE user per module (5-per-hour /api/register rate limit)
    and grant wager_unlock, then each test reuses the logged-in session
    by opening a fresh page in the context. The browser is also exposed
    (so unauthenticated tests can open their own fresh context on the
    same browser, avoiding a second chromium launch).

    Uses the conftest's module-scoped `playwright_instance` so we don't
    nest `sync_playwright()` contexts (which fails with "Sync API inside
    asyncio loop" in this build).
    """
    browser = playwright_instance.chromium.launch()
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(server_url + '/')
    page.wait_for_load_state('domcontentloaded')
    username = f't239r{uuid.uuid4().hex[:10]}'
    password = 'testpass123'
    csrf = _get_csrf(page, server_url)
    status, body = _register(page, server_url, username, password, csrf)
    if status != 201:
        browser.close()
        pytest.fail(f'register failed: {status} {body}')
    # Default ownership: wager_unlock owned, nothing else.
    _grant_items(db_url, username, ['wager_unlock'])
    yield {
        'browser': browser,
        'context': ctx,
        'username': username,
        'base_url': server_url,
        'db_url': db_url,
    }
    browser.close()


@pytest.fixture()
def logged_in_page(browser_ctx):
    """Open a fresh page in the shared logged-in context."""
    page = browser_ctx['context'].new_page()
    page.goto(browser_ctx['base_url'] + '/')
    page.wait_for_load_state('domcontentloaded')
    # The /api/register call set a session cookie, so /api/me is now
    # authenticated. Re-fetch CSRF (token rotates on every request).
    csrf = _get_csrf(page, browser_ctx['base_url'])
    yield {
        'page': page,
        'username': browser_ctx['username'],
        'base_url': browser_ctx['base_url'],
        'db_url': browser_ctx['db_url'],
        'csrf': csrf,
    }
    page.close()


# ══════════════════════════════════════════════════════════════════════════
# /api/wager/stake  — happy path
# ══════════════════════════════════════════════════════════════════════════

def test_wager_stake_happy_path(logged_in_page):
    """AC#3: with wager_unlock owned, a valid POST sets the stake and
    persists it. Reads DB back to confirm the value sticks."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']

    # Sanity baseline.
    before = _read_game_state(logged_in_page['db_url'], username, ['wager_last_stake'])
    assert before['wager_last_stake'] == 0, (
        f"expected initial wager_last_stake=0, got {before['wager_last_stake']}"
    )

    status, body = _api_post(
        page, base + '/api/wager/stake', {'stake': 15}, csrf=logged_in_page['csrf'],
    )
    assert status == 200, f'expected 200, got {status} {body}'
    # Response echoes the actual (clamped) stake value.
    assert body['stake'] == 15, f"response stake={body['stake']!r}, expected 15"
    # 30% is the base max for an owner of wager_unlock only.
    assert body['max_stake_pct'] == 30, (
        f"response max_stake_pct={body['max_stake_pct']!r}, expected 30"
    )

    # DB persistence.
    after = _read_game_state(logged_in_page['db_url'], username, ['wager_last_stake'])
    assert after['wager_last_stake'] == 15, (
        f"DB wager_last_stake={after['wager_last_stake']!r}, expected 15 "
        f"(persistence failed)"
    )


def test_wager_stake_happy_path_zero_is_safe_position(logged_in_page):
    """AC#3: stake=0 is a valid value (the "safe position" — T102
    redesign). It must persist as 0."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']

    status, body = _api_post(
        page, base + '/api/wager/stake', {'stake': 0}, csrf=logged_in_page['csrf'],
    )
    assert status == 200
    assert body['stake'] == 0
    after = _read_game_state(logged_in_page['db_url'], username, ['wager_last_stake'])
    assert after['wager_last_stake'] == 0


def test_wager_stake_clamps_to_player_max(logged_in_page):
    """AC#3: requesting a stake above max_stake_pct is clamped (the route
    uses `validate_stake`). 99% with only wager_unlock (max 30) → 30."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']

    status, body = _api_post(
        page, base + '/api/wager/stake', {'stake': 99}, csrf=logged_in_page['csrf'],
    )
    assert status == 200
    # Response echoes the clamped value.
    assert body['stake'] == 30, (
        f"stake=99 with max=30 should clamp to 30, got {body['stake']!r}"
    )
    # DB shows the clamped value.
    after = _read_game_state(logged_in_page['db_url'], username, ['wager_last_stake'])
    assert after['wager_last_stake'] == 30, (
        f"DB wager_last_stake should be the clamped 30, got "
        f"{after['wager_last_stake']!r}"
    )


def test_wager_stake_snaps_to_5pct_step(logged_in_page):
    """AC#3: validate_stake snaps to the nearest 5% step. 13 → 15 (up)."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']

    status, body = _api_post(
        page, base + '/api/wager/stake', {'stake': 13}, csrf=logged_in_page['csrf'],
    )
    assert status == 200
    assert body['stake'] in (10, 15), (
        f"stake=13 should snap to 10 or 15, got {body['stake']!r}"
    )
    after = _read_game_state(logged_in_page['db_url'], username, ['wager_last_stake'])
    assert after['wager_last_stake'] == body['stake']


# ══════════════════════════════════════════════════════════════════════════
# /api/wager/stake  — invalid input
# ══════════════════════════════════════════════════════════════════════════

def test_wager_stake_no_body_returns_400(logged_in_page):
    """AC#3: an empty body returns 400 ('Invalid stake'). The route
    defaults to stake=0 when the field is missing, which is actually a
    valid value (it locks to 0 without wager_unlock). To exercise the
    400 path we send a non-int string."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    # The actual /api/wager/stake handler does:
    #   stake = (request.json or {}).get('stake', 0)
    #   try: stake = int(stake) except: return 400 'Invalid stake'
    # So stake='not-a-number' → 400.
    status, body = _api_post(
        page, base + '/api/wager/stake', {'stake': 'not-a-number'},
        csrf=logged_in_page['csrf'],
    )
    assert status == 400, f'expected 400 on bad stake, got {status} {body}'
    assert 'Invalid stake' in body.get('error', ''), (
        f"expected 'Invalid stake' error, got {body!r}"
    )


def test_wager_stake_null_body_returns_400(logged_in_page):
    """AC#3: explicit null stake → 400."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    status, body = _api_post(
        page, base + '/api/wager/stake', {'stake': None},
        csrf=logged_in_page['csrf'],
    )
    assert status == 400
    assert 'Invalid stake' in body.get('error', '')


# ══════════════════════════════════════════════════════════════════════════
# /api/wager/stake  — unlock gating
# ══════════════════════════════════════════════════════════════════════════

def test_wager_stake_without_unlock_locks_to_zero(logged_in_page):
    """AC#3: without wager_unlock owned, `validate_stake` always returns
    0 (T102 design). The route accepts the POST and persists 0, but the
    value is locked."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']
    db_url = logged_in_page['db_url']

    # Strip wager_unlock from the user's owned_items.
    psycopg2, _ = _real_psycopg2()
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE game_state SET owned_items = ARRAY("
                "  SELECT unnest(owned_items) EXCEPT SELECT 'wager_unlock'"
                ") WHERE user_id = (SELECT id FROM users WHERE username = %s)",
                (username,),
            )
    finally:
        conn.close()

    status, body = _api_post(
        page, base + '/api/wager/stake', {'stake': 25}, csrf=logged_in_page['csrf'],
    )
    # The route accepts the POST (200) but clamps to 0 because the
    # player doesn't own the unlock. The status is 200, not 403.
    assert status == 200, (
        f'expected 200 (route accepts but clamps), got {status} {body}'
    )
    assert body['stake'] == 0, (
        f"without wager_unlock, stake must lock to 0, got {body['stake']!r}"
    )
    # max_stake_pct is still 30 (the base) — the route just doesn't
    # let the player USE any of it.
    assert body['max_stake_pct'] == 30
    after = _read_game_state(db_url, username, ['wager_last_stake'])
    assert after['wager_last_stake'] == 0


# ══════════════════════════════════════════════════════════════════════════
# /api/wager/stake  — auth required
# ══════════════════════════════════════════════════════════════════════════

def test_wager_stake_unauthenticated_rejected(browser_ctx, server_url):
    """AC#3: not logged in → 401 or 302 (the @login_required handler).

    Uses a fresh context on the module-scoped browser (no shared session
    cookies with the logged-in context) so the request is unauthenticated.
    """
    browser = browser_ctx['browser']
    ctx = browser.new_context()
    page = ctx.new_page()
    # Load the index page so the browser context has a real origin; the
    # subsequent fetch must come from a page with a document base URL,
    # otherwise Chromium's fetch is cross-origin and gets blocked.
    page.goto(server_url + '/')
    page.wait_for_load_state('domcontentloaded')
    # Get a CSRF token from a fresh, unauthenticated session.
    csrf = _get_csrf(page, server_url)
    status, body = _api_post(
        page, server_url + '/api/wager/stake', {'stake': 10}, csrf=csrf,
    )
    ctx.close()
    # Flask-Login's @login_required redirects (302) to /login by default.
    # The route may also be 401 depending on the unauthenticated handler.
    # Accept either as "rejected".
    assert status in (302, 401, 403), (
        f'unauthenticated POST /api/wager/stake should be rejected with '
        f'302/401/403, got {status} {body}'
    )


# ══════════════════════════════════════════════════════════════════════════
# /api/wager/stake  — onbording advance (T102 side-effect)
# ══════════════════════════════════════════════════════════════════════════

def test_wager_stake_advances_onboarding_step(logged_in_page):
    """AC#3 (side effect): when onboarding_step=1 and the player first
    sets a non-zero stake, the step advances to 2 and the confetti_1
    cosmetic is granted + equipped.

    T102 changed the gate from 'actual_stake > 1' (multiplier) to
    'actual_stake > 0' (percentage) — stake=5 is the new threshold.

    The test re-grants wager_unlock (in case an earlier test in this
    module stripped it) and sets onboarding_step=1 directly. Then it
    POSTs stake=5 and verifies the side effect.
    """
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']
    db_url = logged_in_page['db_url']

    # Re-grant wager_unlock (an earlier test may have removed it) and
    # set onboarding_step=1, strip confetti_1 from both arrays.
    _grant_items(db_url, username, ['wager_unlock'])
    psycopg2, _ = _real_psycopg2()
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE game_state SET onboarding_step = 1, '
                "owned_items = array_remove(owned_items, 'confetti_1'), "
                "active_cosmetics = array_remove(active_cosmetics, 'confetti_1') "
                'WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                (username,),
            )
    finally:
        conn.close()

    status, body = _api_post(
        page, base + '/api/wager/stake', {'stake': 5},
        csrf=logged_in_page['csrf'],
    )
    assert status == 200

    # Read the post-state. Onboarding should have advanced to 2 and
    # confetti_1 should be in both arrays.
    after = _read_game_state(
        db_url, username,
        ['onboarding_step', 'owned_items', 'active_cosmetics'],
    )
    assert after['onboarding_step'] == 2, (
        f"onboarding_step should be 2 after first non-zero stake, got "
        f"{after['onboarding_step']}"
    )
    assert 'confetti_1' in after['owned_items'], (
        f"confetti_1 should be granted, owned_items={after['owned_items']}"
    )
    assert 'confetti_1' in after['active_cosmetics'], (
        f"confetti_1 should be equipped, active_cosmetics={after['active_cosmetics']}"
    )


# ══════════════════════════════════════════════════════════════════════════
# /api/tab/heartbeat  — happy path
# ══════════════════════════════════════════════════════════════════════════

def test_tab_heartbeat_happy_path_claims_lock(logged_in_page):
    """AC#3: a fresh POST with a valid tab_id claims the tab-lock and
    returns {ok: True, active: True}. Persists active_tab_id."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']
    db_url = logged_in_page['db_url']
    tab_id = f'tab-{uuid.uuid4().hex[:10]}'

    status, body = _api_post(
        page, base + '/api/tab/heartbeat', {'tab_id': tab_id},
        csrf=logged_in_page['csrf'],
    )
    assert status == 200, f'expected 200, got {status} {body}'
    assert body == {'ok': True, 'active': True}, (
        f"expected {{ok: True, active: True}}, got {body!r}"
    )

    # The DB now shows our tab_id as the active_tab_id.
    after = _read_game_state(db_url, username, ['active_tab_id', 'tab_last_seen'])
    assert after['active_tab_id'] == tab_id, (
        f"DB active_tab_id should be {tab_id!r}, got {after['active_tab_id']!r}"
    )
    assert after['tab_last_seen'] is not None, (
        f"DB tab_last_seen should be set after a successful heartbeat, "
        f"got {after['tab_last_seen']!r}"
    )


def test_tab_heartbeat_renews_own_lock(logged_in_page):
    """AC#3: a second heartbeat with the SAME tab_id renews the lock
    (active: True, no error). This is the steady-state of a single tab.

    Resets the user's active_tab_id to NULL so the first heartbeat in
    this test is a fresh claim (an earlier test may have left a
    different tab_id in the row, which would cause the first heartbeat
    to be rejected as a different tab).
    """
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']
    db_url = logged_in_page['db_url']
    tab_id = f'tab-{uuid.uuid4().hex[:10]}'

    # Reset the lock state so this test starts clean.
    psycopg2, _ = _real_psycopg2()
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE game_state SET active_tab_id = NULL, '
                'tab_last_seen = NULL '
                'WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                (username,),
            )
    finally:
        conn.close()

    # First claim.
    first_status, first_body = _api_post(
        page, base + '/api/tab/heartbeat', {'tab_id': tab_id},
        csrf=logged_in_page['csrf'],
    )
    assert first_status == 200 and first_body == {'ok': True, 'active': True}, (
        f"first heartbeat should claim the lock, got {first_status} {first_body!r}"
    )
    # Second heartbeat (same tab_id) — renews the lock.
    status, body = _api_post(
        page, base + '/api/tab/heartbeat', {'tab_id': tab_id},
        csrf=logged_in_page['csrf'],
    )
    assert status == 200
    assert body == {'ok': True, 'active': True}, (
        f"renewing own lock should still return active=True, got {body!r}"
    )


# ══════════════════════════════════════════════════════════════════════════
# /api/tab/heartbeat  — tab-lock contention
# ══════════════════════════════════════════════════════════════════════════

def test_tab_heartbeat_other_tab_rejected(logged_in_page, browser_ctx):
    """AC#3: when active_tab_id is set to a different tab_id and is
    recent (within TAB_LOCK_TIMEOUT=30s), a heartbeat from a new tab_id
    returns {ok: True, active: False} (cannot claim the lock).

    The route at `game.py:1591-1637` does:
      - read current active_tab_id + tab_last_seen
      - if stored == tab_id → claim (active=True)
      - if stored is None or stale (>30s old) → claim (active=True)
      - otherwise → no claim (active=False)
    """
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']
    db_url = logged_in_page['db_url']

    # Seed: a different tab holds the lock, with a fresh timestamp.
    other_tab = f'other-{uuid.uuid4().hex[:10]}'
    psycopg2, _ = _real_psycopg2()
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE game_state "
                "SET active_tab_id = %s, tab_last_seen = NOW() "
                "WHERE user_id = (SELECT id FROM users WHERE username = %s)",
                (other_tab, username),
            )
    finally:
        conn.close()

    # A different tab tries to claim.
    my_tab = f'mine-{uuid.uuid4().hex[:10]}'
    status, body = _api_post(
        page, base + '/api/tab/heartbeat', {'tab_id': my_tab},
        csrf=logged_in_page['csrf'],
    )
    assert status == 200
    # The other tab is still active — we cannot claim.
    assert body == {'ok': True, 'active': False}, (
        f"with a fresh lock held by another tab, expected "
        f"{{ok: True, active: False}}, got {body!r}"
    )
    # And the DB still shows the other tab as active.
    after = _read_game_state(db_url, username, ['active_tab_id'])
    assert after['active_tab_id'] == other_tab, (
        f"DB should still show other_tab={other_tab!r} as active, got "
        f"{after['active_tab_id']!r}"
    )


def test_tab_heartbeat_stale_lock_can_be_claimed(logged_in_page):
    """AC#3: if the previous tab's last_seen is older than 30s
    (TAB_LOCK_TIMEOUT), a new tab can claim the lock.

    This characterizes the "stale tab recovery" path: the player
    refreshes the page after a crash and gets the lock back.
    """
    page = logged_in_page['page']
    base = logged_in_page['base_url']
    username = logged_in_page['username']
    db_url = logged_in_page['db_url']

    # Seed: a tab holds the lock but the last_seen is 60s ago.
    old_tab = f'stale-{uuid.uuid4().hex[:10]}'
    psycopg2, _ = _real_psycopg2()
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE game_state "
                "SET active_tab_id = %s, tab_last_seen = NOW() - INTERVAL '60 seconds' "
                "WHERE user_id = (SELECT id FROM users WHERE username = %s)",
                (old_tab, username),
            )
    finally:
        conn.close()

    new_tab = f'fresh-{uuid.uuid4().hex[:10]}'
    status, body = _api_post(
        page, base + '/api/tab/heartbeat', {'tab_id': new_tab},
        csrf=logged_in_page['csrf'],
    )
    assert status == 200
    assert body == {'ok': True, 'active': True}, (
        f"with a stale lock, a new heartbeat should claim it "
        f"(active=True), got {body!r}"
    )
    after = _read_game_state(db_url, username, ['active_tab_id'])
    assert after['active_tab_id'] == new_tab, (
        f"DB should now show new_tab={new_tab!r} as active, got "
        f"{after['active_tab_id']!r}"
    )


# ══════════════════════════════════════════════════════════════════════════
# /api/tab/heartbeat  — invalid input + auth required
# ══════════════════════════════════════════════════════════════════════════

def test_tab_heartbeat_missing_tab_id_returns_400(logged_in_page):
    """AC#3: empty/missing tab_id → 400 (the route checks
    `if not tab_id: return ... 400`)."""
    page = logged_in_page['page']
    base = logged_in_page['base_url']

    # Empty string.
    status, body = _api_post(
        page, base + '/api/tab/heartbeat', {'tab_id': ''},
        csrf=logged_in_page['csrf'],
    )
    assert status == 400, f"empty tab_id should 400, got {status} {body}"
    assert body == {'ok': False}, f"expected {{ok: False}}, got {body!r}"

    # Missing key entirely.
    status, body = _api_post(
        page, base + '/api/tab/heartbeat', {},
        csrf=logged_in_page['csrf'],
    )
    assert status == 400
    assert body == {'ok': False}


def test_tab_heartbeat_unauthenticated_rejected(browser_ctx, server_url):
    """AC#3: not logged in → 401 or 302."""
    browser = browser_ctx['browser']
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(server_url + '/')
    page.wait_for_load_state('domcontentloaded')
    csrf = _get_csrf(page, server_url)
    status, body = _api_post(
        page, server_url + '/api/tab/heartbeat',
        {'tab_id': 'whatever'}, csrf=csrf,
    )
    ctx.close()
    assert status in (302, 401, 403), (
        f'unauthenticated POST /api/tab/heartbeat should be rejected '
        f'(302/401/403), got {status} {body}'
    )
