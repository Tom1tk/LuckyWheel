"""T213: 5 casino-themed fish added to the cosmetic shop (T213).

T213 extends the cosmetic "fish skins" category from 18 → 23 entries by
adding five casino-themed cosmetics priced strictly above `fish_ufo`
(425,000) and strictly increasing in cost:

  fish_dice     — 🎲  Lucky Dice    — 600,000
  fish_joker    — 🃏  Joker         — 850,000
  fish_diamond  — 💎  Diamond       — 1,200,000
  fish_poker    — ♠️   Poker         — 1,700,000
  fish_slot     — 🎰  Slot Machine  — 2,400,000

These tests verify:
  1. All 5 IDs are in `models.FISH_SKINS`.
  2. All 5 entries are present in `static/app.jsx` (and therefore in
     `static/app.js` after `make build`).
  3. Prices are strictly increasing AND strictly greater than fish_ufo.
  4. The /api/buy endpoint accepts the new IDs (a registered user with
     enough losses can actually buy fish_dice).
  5. The 5 IDs are in the client-side `COSMETIC_IDS` set so the shop
     UI renders them with the correct currency icon.

The test_buy_casino_fish and test_casino_fish_in_shop tests require a
live DATABASE_URL and a working Postgres connection. They are skipped
when the DB is unreachable so the pure-model tests still run.
"""
import os
import re
import sys
import uuid

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from models import FISH_SKINS, ITEM_CURRENCY  # noqa: E402


# ── The 5 new casino fish, in the order the ticket specifies ───────────────
CASINO_FISH = [
    ('fish_dice',    600_000,  '🎲'),
    ('fish_joker',   850_000,  '🃏'),
    ('fish_diamond', 1_200_000, '💎'),
    ('fish_poker',   1_700_000, '♠️'),
    ('fish_slot',    2_400_000, '🎰'),
]
CASINO_IDS = [fid for fid, _cost, _emoji in CASINO_FISH]
UFO_COST   = 425_000


# ════════════════════════════════════════════════════════════════════════════
# 1. models.FISH_SKINS contains all 5 new entries
# ════════════════════════════════════════════════════════════════════════════
def test_5_new_fish_in_models():
    """All 5 casino fish IDs must be in models.FISH_SKINS with a cost key."""
    for fid, expected_cost, _emoji in CASINO_FISH:
        assert fid in FISH_SKINS, (
            f'{fid} is missing from models.FISH_SKINS. '
            f'Current FISH_SKINS keys: {sorted(FISH_SKINS.keys())}'
        )
        assert 'cost' in FISH_SKINS[fid], (
            f'{fid} has no "cost" key: {FISH_SKINS[fid]!r}'
        )
        assert FISH_SKINS[fid]['cost'] == expected_cost, (
            f'{fid} cost is {FISH_SKINS[fid]["cost"]}, expected {expected_cost}'
        )


# ════════════════════════════════════════════════════════════════════════════
# 2. static/app.jsx contains all 5 new shop entries
# ════════════════════════════════════════════════════════════════════════════
def test_5_new_fish_in_shop_jsx():
    """All 5 casino fish entries are present in static/app.jsx.

    Also verifies the cost field in JSX matches models.py (catches drift
    between the client-side catalogue and the server-side authoritative
    cost dict).
    """
    jsx_path = os.path.join(REPO_ROOT, 'static', 'app.jsx')
    with open(jsx_path, 'r', encoding='utf-8') as f:
        jsx = f.read()

    for fid, expected_cost, emoji in CASINO_FISH:
        # Each entry looks like: { id: 'fish_dice', ..., cost: 600000, ... }
        m = re.search(
            r"id:\s*'" + re.escape(fid) + r"'[^}]*?cost:\s*(\d+)",
            jsx,
            re.DOTALL,
        )
        assert m, (
            f'{fid} entry not found in app.jsx '
            f'(looked for `id: \'{fid}\'` ... `cost: <int>`)'
        )
        cost_in_jsx = int(m.group(1))
        assert cost_in_jsx == expected_cost, (
            f'{fid} cost in app.jsx is {cost_in_jsx}, expected {expected_cost} '
            f'(must match models.FISH_SKINS)'
        )
        # The emoji must appear within the same entry block (rough check:
        # within the 200 chars before the id match).
        start = max(0, m.start() - 200)
        nearby = jsx[start:m.end()]
        assert emoji in nearby, (
            f'{fid} entry in app.jsx is missing emoji {emoji!r} '
            f'(block: {nearby!r})'
        )


def test_5_new_fish_in_built_app_js():
    """All 5 casino fish entries are present in static/app.js (the Babel
    build output). This catches the case where someone edits app.jsx
    but forgets to run `make build`.
    """
    js_path = os.path.join(REPO_ROOT, 'static', 'app.js')
    assert os.path.exists(js_path), (
        f'{js_path} does not exist — run `make build` first'
    )
    with open(js_path, 'r', encoding='utf-8') as f:
        built = f.read()
    for fid, _cost, _emoji in CASINO_FISH:
        assert fid in built, (
            f'{fid} is missing from built static/app.js — '
            f'JSX edit was not transpiled. Run `make build`.'
        )


# ════════════════════════════════════════════════════════════════════════════
# 3. Prices are strictly increasing AND strictly greater than fish_ufo
# ════════════════════════════════════════════════════════════════════════════
def test_prices_increasing_and_above_ufo():
    """All 5 new fish are > fish_ufo (425,000) and each > the previous one.

    This is the core ordering invariant the operator asked for.
    """
    assert 'fish_ufo' in FISH_SKINS, 'fish_ufo is missing from FISH_SKINS'
    assert FISH_SKINS['fish_ufo']['cost'] == UFO_COST, (
        f'fish_ufo cost has drifted to {FISH_SKINS["fish_ufo"]["cost"]} '
        f'(tests assume {UFO_COST})'
    )

    prev_cost = FISH_SKINS['fish_ufo']['cost']
    for fid, cost, _emoji in CASINO_FISH:
        assert cost > UFO_COST, (
            f'{fid} cost {cost:,} is NOT strictly above fish_ufo ({UFO_COST:,})'
        )
        assert cost > prev_cost, (
            f'{fid} cost {cost:,} is NOT strictly above the previous fish '
            f'cost {prev_cost:,} (ticket requires strictly increasing prices)'
        )
        prev_cost = cost


def test_most_expensive_fish_is_now_fish_slot():
    """After T213, fish_slot (2,400,000) is the new most-expensive fish.

    Catches regressions where someone re-orders FISH_SKINS by accident.
    """
    most_expensive = max(FISH_SKINS.items(), key=lambda kv: kv[1]['cost'])
    assert most_expensive[0] == 'fish_slot', (
        f'expected fish_slot to be the most expensive fish, '
        f'got {most_expensive[0]} at {most_expensive[1]["cost"]:,}'
    )
    assert most_expensive[1]['cost'] == 2_400_000


# ════════════════════════════════════════════════════════════════════════════
# 4. /api/buy accepts the new IDs (direct API test via Flask test_client)
# ════════════════════════════════════════════════════════════════════════════
def _db_available():
    """Return True if a Postgres DB is reachable for integration tests.

    The pure-Python model tests must work even without a DB, so the
    /api/buy integration test is gated on this.
    """
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        return False
    try:
        # Force-import real psycopg2 — another test in the suite
        # (test_insurance_buy_with_tokens.py) installs a stub via
        # sys.modules.setdefault, which would shadow the real one.
        # We must also force-import psycopg2.extras because it's a
        # subpackage that `import psycopg2` does NOT auto-attach.
        import importlib
        if 'psycopg2' in sys.modules and not hasattr(sys.modules['psycopg2'], 'connect'):
            del sys.modules['psycopg2']
            sys.modules.pop('psycopg2.extras', None)
            importlib.invalidate_caches()
        import psycopg2          # noqa: F401
        import psycopg2.extras   # noqa: F401
        conn = psycopg2.connect(db_url, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope='module')
def flask_app():
    """Build a Flask test client + a connected DB. Skips module if no DB."""
    if not _db_available():
        pytest.skip('DATABASE_URL not reachable — skipping /api/buy integration test')

    if not os.environ.get('WHEEL_SECRET_KEY'):
        os.environ['WHEEL_SECRET_KEY'] = 't213-test-secret-key-not-for-prod'

    # Other tests in the suite (e.g. test_insurance_buy_with_tokens.py) use
    # `sys.modules.setdefault(<name>, <stub>)` to avoid pulling in real Flask
    # / psycopg2 / extensions / etc. When that file is collected before this
    # one, the stubs stay in sys.modules and our `from app import create_app`
    # would import the stubs instead of the real packages. We need to:
    #   1. Snapshot the stub modules so we can restore them in teardown
    #      (otherwise downstream tests that rely on the stubs would break).
    #   2. Evict the stubs and force-import the real ones for this test.
    import importlib
    _STUB_NAMES = [
        'flask', 'flask_login', 'psycopg2', 'psycopg2.extras',
        'extensions', 'seasons', 'security', 'db',
    ]
    # App-local modules that may already be cached in sys.modules with
    # stub-flask references inside them. We must evict them too, or
    # their old `from flask import Blueprint` bindings will still point
    # at the stub and break app.create_app().
    _APP_LOCAL_TO_EVICT = ['app', 'auth', 'game', 'chat', 'models']
    _saved_stubs = {}
    # Track which modules we've already confirmed as stubs.
    _confirmed_stub = set()
    for name in _STUB_NAMES:
        if name in sys.modules:
            mod = sys.modules[name]
            # Real flask has `Flask`; stub does not. Real flask_login
            # has `LoginManager`; stub has `current_user`/`UserMixin` only.
            # Real psycopg2 has `connect`; stub has only `extras`.
            # Real psycopg2.extras is a stub iff its parent psycopg2 is.
            # Real db has `init_pool`; stub has only `db_connection`.
            # Real extensions has `login_manager`; stub has only `limiter`
            # + `csrf`. Real security has `check_lockout`; stub has only
            # `require_json`.
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
    # Evict cached app-local modules so they re-import with real flask.
    for name in _APP_LOCAL_TO_EVICT:
        sys.modules.pop(name, None)
    importlib.invalidate_caches()
    # Force-import the real packages so subsequent `from app import ...` finds them.
    import flask           # noqa: F401
    import flask_login     # noqa: F401
    import psycopg2        # noqa: F401
    import psycopg2.extras  # noqa: F401  (subpackage — not auto-loaded by `import psycopg2`)
    import extensions      # noqa: F401
    import db              # noqa: F401

    from app import create_app
    app = create_app()

    yield app

    # Teardown: restore the stubs so any tests run after this module
    # that depend on the stubs (e.g. test_insurance_buy_with_tokens.py)
    # still see what they expect.
    for name, mod in _saved_stubs.items():
        sys.modules[name] = mod


def test_buy_casino_fish(flask_app):
    """A fresh user with enough losses can buy fish_dice and ends up
    with it in their owned_items array.

    Uses Flask's test_client (no subprocess, no Playwright) and writes
    losses directly via SQL — the buy endpoint deducts losses server-
    side, so we seed 1,000,000 losses to comfortably afford 600,000.
    """
    import psycopg2

    client = flask_app.test_client()
    username = f't213{uuid.uuid4().hex[:10]}'
    password = 'testpass123'

    # Step 1: register (also gives us a CSRF token + session cookie).
    me = client.get('/api/me').get_json()
    csrf = me['csrf_token']
    r = client.post(
        '/api/register',
        json={'username': username, 'password': password},
        headers={'X-CSRFToken': csrf},
    )
    assert r.status_code == 201, f'register failed: {r.status_code} {r.get_json()}'

    # Step 2: grant losses directly so we can afford fish_dice (600,000).
    db_url = os.environ['DATABASE_URL']
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE game_state SET losses = 1000000 "
                "WHERE user_id = (SELECT id FROM users WHERE username = %s)",
                (username,),
            )
    finally:
        conn.close()

    # Step 3: actually call /api/buy for fish_dice.
    me2 = client.get('/api/me').get_json()
    csrf2 = me2['csrf_token']
    r2 = client.post(
        '/api/buy',
        json={'item_id': 'fish_dice'},
        headers={'X-CSRFToken': csrf2},
    )
    assert r2.status_code == 200, (
        f'buy fish_dice failed: {r2.status_code} {r2.get_json()}'
    )

    # Step 4: verify the fish is in owned_items (read the row directly).
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT owned_items, losses FROM game_state "
                "WHERE user_id = (SELECT id FROM users WHERE username = %s)",
                (username,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    owned, losses_after = row
    assert 'fish_dice' in owned, (
        f'fish_dice not in owned_items after buy: {owned}'
    )
    # The 600,000 cost should have been deducted from the 1,000,000 seed.
    assert int(losses_after) == 400_000, (
        f'expected losses to be 400,000 after 600,000 deduction, '
        f'got {int(losses_after):,}'
    )


# ════════════════════════════════════════════════════════════════════════════
# 5. The 5 new fish are in the client-side COSMETIC_IDS set so the shop
#    renders them with the losses-currency icon.
# ════════════════════════════════════════════════════════════════════════════
def test_casino_fish_in_shop_cosmetics_set():
    """All 5 new fish IDs are in the COSMETIC_IDS Set in static/app.jsx.

    The shop uses COSMETIC_IDS to decide the currency icon (🏆 wins vs
    💀 losses). If a new fish ID is not in this set, the shop would
    fall through to the default ('wins') and show the wrong icon.
    """
    jsx_path = os.path.join(REPO_ROOT, 'static', 'app.jsx')
    with open(jsx_path, 'r', encoding='utf-8') as f:
        jsx = f.read()

    # Find the COSMETIC_IDS = new Set([ ... ]) block.
    m = re.search(r"const\s+COSMETIC_IDS\s*=\s*new\s+Set\(\[([\s\S]*?)\]\)", jsx)
    assert m, 'COSMETIC_IDS Set literal not found in app.jsx'
    body = m.group(1)

    for fid in CASINO_IDS:
        assert f"'{fid}'" in body, (
            f'{fid} is missing from COSMETIC_IDS in app.jsx — '
            f'the shop will render the wrong currency icon for it'
        )


def test_casino_fish_currency_is_losses():
    """All 5 new fish are bought with losses (matching the rest of the
    FISH_SKINS category, which is themed around 'cosmetic loss' currency).
    """
    for fid, _cost, _emoji in CASINO_FISH:
        assert ITEM_CURRENCY.get(fid) == 'losses', (
            f'{fid} currency is {ITEM_CURRENCY.get(fid)!r}, expected "losses" '
            f'(FISH_SKINS are all bought with losses)'
        )


if __name__ == '__main__':
    import subprocess
    sys.exit(subprocess.call(['python3', '-m', 'pytest', __file__, '-v']))
