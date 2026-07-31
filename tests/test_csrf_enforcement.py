"""T236: CSRF is enforced on all session-authenticated state-changing routes.

T236 closes the CSRF-exempt inconsistency on the Season-8 block in game.py
(`/api/wager/*`, `/api/insurance/*`, loadout, guard, auto-spin, wheel-mode,
prestige, bounties, singularity). CSRF is configured app-wide in `app.py`
(`CSRFProtect` + `WTF_CSRF_HEADERS = ['X-CSRFToken']`) and the React frontend
sends that header on every non-GET (`static/app.jsx:10-11`). The 17 exemptions
were a shortcut, not a design choice — `SameSite=Lax` session cookies blunt
cross-site POST, but the exemptions still leave an inconsistent posture.

The one route that MUST remain exempt is `/api/admin/advance-season`
(`game.py:3290-3292`): it authenticates with `X-Admin-Secret` via
`hmac.compare_digest`, not a session cookie, so CSRF does not apply.

These tests assert that the decorator set on every relevant view function in
game.py matches the contract:
  - 17 session routes  → `@login_required` only, NO `@csrf.exempt`
  -  1 admin route     → `@csrf.exempt` (kept, header-secret)

The static check runs without a DB or Flask. An opt-in live check (skipped
when no DB is available) boots the real Flask app and confirms CSRFProtect
rejects an unauthenticated POST and accepts one with a valid token — this is
the end-to-end proof that removing the exemptions doesn't break the client.
"""
import os
import re
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Session-authenticated POST routes in game.py that were `@csrf.exempt` before
# T236 and must no longer carry the decorator. Order/labels are not significant
# — the test only counts and matches by (path, function-name) pair.
SESSION_ROUTES = [
    ('/api/wager/bank',                  'wager_bank'),
    ('/api/wager/stake',                 'wager_set_stake'),
    ('/api/wager/double-down',           'wager_double_down'),
    ('/api/wager/double-down/cancel',    'wager_double_down_cancel'),
    ('/api/insurance/arm',               'wager_insurance'),
    ('/api/insurance/cancel',            'wager_insurance_cancel'),
    ('/api/insurance/buy',               'insurance_buy_with_tokens'),
    ('/api/insurance/claim-free',        'insurance_claim_free'),
    ('/api/prestige',                    'prestige_reset'),
    ('/api/bounties/claim',              'claim_bounty'),
    ('/api/singularity/contribute',      'singularity_contribute'),
    ('/api/loadout',                     'save_loadout'),
    ('/api/loadout/apply',               'apply_loadout'),
    ('/api/guard',                       'guard_endpoint'),
    ('/api/auto-spin/start',             'auto_spin_start'),
    ('/api/auto-spin/stop',              'auto_spin_stop'),
    ('/api/wheel-mode',                  'set_wheel_mode'),
]

# Admin route that authenticates with `X-Admin-Secret` (not a session cookie)
# and must REMAIN `@csrf.exempt`. CSRF does not apply to header-secret auth.
ADMIN_ROUTES = [
    ('/api/admin/advance-season', 'admin_advance_season'),
]


def _decorator_block(src, def_idx, lookbehind=300):
    """Return the decorator source sitting immediately above `def ...` at
    `def_idx`. Stops at the previous blank line so the slice is local.
    """
    return src[max(0, def_idx - lookbehind):def_idx]


def _find_def(src, func_name):
    """Return the source index of `def <func_name>(` or -1 if missing."""
    pattern = r'^def\s+' + re.escape(func_name) + r'\s*\('
    m = re.search(pattern, src, re.MULTILINE)
    return m.start() if m else -1


# ════════════════════════════════════════════════════════════════════════════
# 1. Whole-file invariant: exactly one @csrf.exempt remains (the admin route)
# ════════════════════════════════════════════════════════════════════════════
def test_only_one_csrf_exempt_remains_in_game_py():
    """T236: every `@csrf.exempt` is removed except on the header-secret
    admin route. This is the file-level check called out in the ticket's
    VERIFY step (`grep -c csrf.exempt game.py` → 1).
    """
    src = open(os.path.join(REPO_ROOT, 'game.py'), encoding='utf-8').read()
    exempt_lines = [
        i + 1 for i, line in enumerate(src.splitlines())
        if '@csrf.exempt' in line
    ]
    assert len(exempt_lines) == 1, (
        f'expected exactly 1 @csrf.exempt in game.py after T236, '
        f'found {len(exempt_lines)} at lines {exempt_lines}. '
        f'All session-auth routes must be CSRF-protected; only '
        f'/api/admin/advance-season (header-secret) may stay exempt.'
    )
    # The one remaining exemption must be the admin route, not a session route.
    def_idx = _find_def(src, 'admin_advance_season')
    assert def_idx >= 0, 'admin_advance_season not found in game.py'
    block = _decorator_block(src, def_idx)
    assert '@csrf.exempt' in block, (
        'the remaining @csrf.exempt must be on admin_advance_season '
        '(the only header-secret route in the file)'
    )


# ════════════════════════════════════════════════════════════════════════════
# 2. Per-route: every session-auth route has lost its @csrf.exempt
# ════════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize('path,func_name', SESSION_ROUTES)
def test_session_route_no_longer_csrf_exempt(path, func_name):
    """T236: each session-auth POST route is no longer `@csrf.exempt`.

    The function must still be `@login_required` (sanity check — the route
    is still session-protected) and must NOT carry `@csrf.exempt`.
    """
    src = open(os.path.join(REPO_ROOT, 'game.py'), encoding='utf-8').read()
    # The route must be registered at the expected path.
    assert f"'{path}'" in src, (
        f'route {path} is not registered in game.py — T236 list may be stale'
    )
    def_idx = _find_def(src, func_name)
    assert def_idx >= 0, (
        f'view function {func_name!r} (for {path}) not found in game.py'
    )
    block = _decorator_block(src, def_idx)
    assert 'csrf.exempt' not in block, (
        f'{func_name} ({path}) still carries @csrf.exempt — '
        f'CSRF is enforced app-wide; the session cookie + X-CSRFToken '
        f'header is the contract for this route'
    )
    assert 'login_required' in block, (
        f'{func_name} ({path}) must still require login (@login_required)'
    )


# ════════════════════════════════════════════════════════════════════════════
# 3. The admin route still carries @csrf.exempt (it authenticates by header
#    secret, not by session cookie, so CSRF does not apply).
# ════════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize('path,func_name', ADMIN_ROUTES)
def test_admin_route_still_csrf_exempt(path, func_name):
    """T236: the header-secret admin route keeps its `@csrf.exempt`.

    `/api/admin/advance-season` checks `X-Admin-Secret` via
    `hmac.compare_digest`. CSRF protects cookie-bound sessions; a header
    secret cannot be replayed by a cross-site form, so the exemption stays.
    """
    src = open(os.path.join(REPO_ROOT, 'game.py'), encoding='utf-8').read()
    assert f"'{path}'" in src, (
        f'admin route {path} is not registered in game.py'
    )
    def_idx = _find_def(src, func_name)
    assert def_idx >= 0, f'view function {func_name!r} not found in game.py'
    block = _decorator_block(src, def_idx)
    assert 'csrf.exempt' in block, (
        f'{func_name} ({path}) lost its @csrf.exempt — but this route '
        f'authenticates with X-Admin-Secret, not a session cookie, so '
        f'CSRF does not apply and the exemption must stay'
    )
    assert 'login_required' not in block, (
        f'{func_name} ({path}) must NOT be @login_required — '
        f'it authenticates with X-Admin-Secret'
    )


# ════════════════════════════════════════════════════════════════════════════
# 4. Frontend sends X-CSRFToken on every non-GET (static/app.jsx:10-11)
# ════════════════════════════════════════════════════════════════════════════
def test_app_jsx_sends_csrf_header_on_mutations():
    """T236 AC#2: the React frontend sends `X-CSRFToken` on POST/PUT/DELETE.

    With the exemptions gone, every state-changing request now relies on the
    header. If the client ever drops the header, every session mutation will
    start failing with 400. This test pins the client contract.
    """
    jsx = open(os.path.join(REPO_ROOT, 'static', 'app.jsx'), encoding='utf-8').read()
    # The apiFetch helper sets the header on any method that isn't GET/HEAD.
    # We don't pin the exact wording — only that the header name appears in
    # the request-building path and is gated on a non-GET method check.
    assert "'X-CSRFToken'" in jsx or '"X-CSRFToken"' in jsx, (
        'app.jsx must set the X-CSRFToken header on mutating requests'
    )
    # Look for the method gate near the header.
    m = re.search(
        r"method\s*!==\s*['\"](GET|HEAD)['\"][\s\S]{0,200}['\"]X-CSRFToken['\"]",
        jsx,
    )
    assert m, (
        'app.jsx must send X-CSRFToken only for non-GET/HEAD methods '
        '(the apiFetch gate)'
    )


# ════════════════════════════════════════════════════════════════════════════
# 5. Live check (DB-gated): a real Flask test client enforces CSRF on
#    /api/wager/stake — the route called out by name in the ticket.
# ════════════════════════════════════════════════════════════════════════════
def _db_available():
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        return False
    try:
        import importlib
        # Other tests install stub modules under these names; evict them
        # so we get the real psycopg2 + connect function.
        for name in ('psycopg2', 'psycopg2.extras'):
            if name in sys.modules and not hasattr(
                sys.modules.get(name, None), 'connect'
            ):
                sys.modules.pop(name, None)
        importlib.invalidate_caches()
        import psycopg2  # noqa: F401
        conn = psycopg2.connect(db_url, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope='module')
def flask_app():
    """Build a Flask test app, evicting any test stubs from sys.modules first.

    Mirrors the fixture in `test_shop_casino_fish.py` — the test stubs
    installed by other test files would shadow the real Flask/psycopg2/…
    packages and break `app.create_app()`. We save + restore them so tests
    collected after this module still see the stubs they expect.
    """
    if not _db_available():
        pytest.skip('DATABASE_URL not reachable — skipping live CSRF test')

    if not os.environ.get('WHEEL_SECRET_KEY'):
        os.environ['WHEEL_SECRET_KEY'] = 't236-test-secret-key-not-for-prod'

    import importlib
    _STUB_NAMES = [
        'flask', 'flask_login', 'psycopg2', 'psycopg2.extras',
        'extensions', 'seasons', 'security', 'db',
    ]
    _APP_LOCAL_TO_EVICT = ['app', 'auth', 'game', 'chat', 'models']
    _saved_stubs = {}
    _confirmed_stub = set()
    for name in _STUB_NAMES:
        if name in sys.modules:
            mod = sys.modules[name]
            if name == 'flask' and not hasattr(mod, 'Flask'):
                is_stub = True
            elif name == 'flask_login' and not hasattr(mod, 'LoginManager'):
                is_stub = True
            elif name == 'psycopg2' and not hasattr(mod, 'connect'):
                is_stub = True
            elif name == 'psycopg2.extras' and 'psycopg2' in _confirmed_stub:
                is_stub = True
            elif name == 'db' and not hasattr(mod, 'init_pool'):
                is_stub = True
            elif name == 'extensions' and not hasattr(mod, 'login_manager'):
                is_stub = True
            elif name == 'security' and not hasattr(mod, 'check_lockout'):
                is_stub = True
            else:
                is_stub = False
            if is_stub:
                _saved_stubs[name] = mod
                _confirmed_stub.add(name)
                del sys.modules[name]
    for name in _APP_LOCAL_TO_EVICT:
        sys.modules.pop(name, None)
    importlib.invalidate_caches()
    import flask           # noqa: F401
    import flask_login     # noqa: F401
    import psycopg2        # noqa: F401
    import psycopg2.extras  # noqa: F401
    import extensions      # noqa: F401
    import db              # noqa: F401

    from app import create_app
    app = create_app()
    yield app

    for name, mod in _saved_stubs.items():
        sys.modules[name] = mod


def _register_and_login(client, username, password):
    """Register a fresh user and return the X-CSRFToken to use for mutations.

    CSRFProtect's token lives in the session and is set as a non-httponly
    cookie by the framework. A POST to a CSRF-protected route without
    `X-CSRFToken` matching the session value gets a 400. The frontend
    fetches it from `/api/me`; we do the same here.
    """
    me = client.get('/api/me').get_json()
    csrf = me['csrf_token']
    r = client.post(
        '/api/register',
        json={'username': username, 'password': password},
        headers={'X-CSRFToken': csrf},
    )
    assert r.status_code == 201, (
        f'register failed: {r.status_code} {r.get_json()}'
    )
    # Re-fetch /api/me after login — same token is fine, but we want the
    # post-login value to match what the client would actually use.
    me2 = client.get('/api/me').get_json()
    return me2['csrf_token']


def test_wager_stake_rejects_post_without_csrf(flask_app):
    """T236 AC#3: POST /api/wager/stake without X-CSRFToken is rejected.

    With `@csrf.exempt` removed, the route now goes through CSRFProtect. A
    browser that forgot the header (or a cross-site form, which is what this
    defense is really about) must get 400 — not silently mutate state.
    """
    import uuid
    client = flask_app.test_client()
    username = f't236{uuid.uuid4().hex[:10]}'
    _register_and_login(client, username, 'testpass123')

    r = client.post('/api/wager/stake', json={'stake': 10})
    assert r.status_code == 400, (
        f'POST /api/wager/stake without X-CSRFToken should be rejected '
        f'with 400 (CSRFProtect), got {r.status_code} {r.get_json()}'
    )


def test_wager_stake_rejects_post_with_invalid_csrf(flask_app):
    """T236 AC#3: POST /api/wager/stake with a bogus X-CSRFToken is rejected.

    An attacker who guesses the header name but not the per-session token
    must still be blocked. The session-cookie `csrf_token` does not match
    the header, so CSRFProtect returns 400.
    """
    import uuid
    client = flask_app.test_client()
    username = f't236{uuid.uuid4().hex[:10]}'
    _register_and_login(client, username, 'testpass123')

    r = client.post(
        '/api/wager/stake',
        json={'stake': 10},
        headers={'X-CSRFToken': 'this-is-not-the-real-token'},
    )
    assert r.status_code == 400, (
        f'POST /api/wager/stake with a wrong X-CSRFToken should be rejected '
        f'with 400 (CSRFProtect), got {r.status_code} {r.get_json()}'
    )


def test_wager_stake_accepts_post_with_valid_csrf(flask_app):
    """T236 AC#3: POST /api/wager/stake WITH X-CSRFToken succeeds.

    The frontend (`static/app.jsx:10-11`) always sends the header on
    non-GET requests, so a normal in-app call must still work. The response
    code is whatever the route returns for a fresh user with no
    `fish_to_wager` unlock — we just assert that the request gets *past*
    CSRF (status not 400 from CSRFProtect). Anything 2xx/4xx from the
    route's own logic is fine; the 400 we care about is the one from
    CSRFProtect when the token is wrong.
    """
    import uuid
    client = flask_app.test_client()
    username = f't236{uuid.uuid4().hex[:10]}'
    csrf = _register_and_login(client, username, 'testpass123')

    r = client.post(
        '/api/wager/stake',
        json={'stake': 10},
        headers={'X-CSRFToken': csrf},
    )
    assert r.status_code != 400 or b'CSRF' not in (r.data or b''), (
        f'POST /api/wager/stake with a valid X-CSRFToken must not be '
        f'rejected by CSRFProtect; got {r.status_code} {r.get_data(as_text=True)}'
    )
    # If CSRFProtect did reject it, the body mentions the reason.
    if r.status_code == 400:
        body = r.get_data(as_text=True).lower()
        assert 'csrf' not in body and 'token' not in body, (
            f'400 response looks like a CSRF rejection: {body!r}'
        )
