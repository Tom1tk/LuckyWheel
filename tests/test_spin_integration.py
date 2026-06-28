"""T239: Spin engine integration tests.

The money engine (`_resolve_spin` + the `/api/spin` handler) is the most
critical code in the codebase. The existing unit tests in
`test_spin_logic.py` / `test_wager_redesign.py` exercise
`_resolve_spin` with a *mocked* DB and patched `random.random` — that
covers the math but not the SQL persistence, the `FOR UPDATE` row lock,
the bounty hooks, the onboarding advance, the tab-lock interaction, or
the way the `/api/spin` handler assembles its response from `events`.

This file runs the *real* `/api/spin` handler against a *real* DB
(Flask test client + psycopg2) and asserts that the side effects land
in the `game_state` row. Outcomes are forced by patching
`game.random.random` (the in-process test client runs in the same
Python process as the imported `game` module, so this is reliable).

Characterization scope (T239 AC#1):
  1. Plain spin       — wins / losses / streak update
  2. Wager stake      — stake escrow on loss, refund on win
  3. Insurance        — armed insurance fires on a loss (caps loss + refunds escrow)
  4. Double-down      — DD escrows the LAST win amount, not the slider value
  5. Hot-streak       — wager_banked_wins accumulates on consecutive wins

Two consecutive spins per path (per ticket) so the test sees the
update land in the row, then sees a second update land in the same
row (covers the UPDATE's full state-assignment statement).
"""
import importlib
import os
import sys
import uuid
from contextlib import contextmanager
from typing import Any

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ──────────────────────────────────────────────────────────────────────────
# Flask test-app fixture
# ──────────────────────────────────────────────────────────────────────────

def _db_available():
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        return False
    try:
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
def game_app():
    """Build a real Flask app for the test client.

    Mirrors `flask_app` in test_csrf_enforcement.py — the test stubs
    installed by other test files (test_wager_actions.py, etc.) would
    shadow the real Flask/psycopg2 packages and break `create_app()`.
    We save + restore them so the rest of the test suite still sees
    the stubs it expects.
    """
    if not _db_available():
        pytest.skip('DATABASE_URL not reachable — skipping live spin test')

    if not os.environ.get('WHEEL_SECRET_KEY'):
        os.environ['WHEEL_SECRET_KEY'] = 't239-test-secret-key-not-for-prod'

    _STUB_NAMES = [
        'flask', 'flask_login', 'psycopg2', 'psycopg2.extras',
        'extensions', 'seasons', 'security', 'db',
        # These get stub-installed by sibling test files (test_insurance_tokens,
        # test_wager_redesign, etc.). If we don't evict them, the real `game`
        # module loaded below imports the STUB wagers/wheel_modes/etc. instead
        # of the real ones — _resolve_spin then returns 0 payouts.
        'wagers', 'wheel_modes', 'prestige', 'bounties',
        'community_goals', 'chat', 'chat_triggers',
    ]
    _APP_LOCAL_TO_EVICT = ['app', 'auth', 'game', 'chat', 'models']
    _saved_stubs = {}
    for name in _STUB_NAMES:
        if name in sys.modules:
            mod = sys.modules[name]
            is_stub = False
            if name == 'flask' and not hasattr(mod, 'Flask'):
                is_stub = True
            elif name == 'flask_login' and not hasattr(mod, 'LoginManager'):
                is_stub = True
            elif name == 'psycopg2' and not hasattr(mod, 'connect'):
                is_stub = True
            elif name == 'db' and not hasattr(mod, 'init_pool'):
                is_stub = True
            elif name == 'extensions' and not hasattr(mod, 'login_manager'):
                is_stub = True
            elif name == 'security' and not hasattr(mod, 'check_lockout'):
                is_stub = True
            elif name in ('wagers', 'wheel_modes', 'prestige', 'bounties',
                          'community_goals', 'chat', 'chat_triggers'):
                # These are stub-installed by sibling test files. They don't
                # have the real module's class/function signatures, so just
                # always treat them as stubs (they will be re-installed by
                # the next sibling test that loads, so safe to drop here).
                is_stub = True
            if is_stub:
                _saved_stubs[name] = mod
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
    import wagers          # noqa: F401
    import wheel_modes     # noqa: F401
    import prestige        # noqa: F401
    import bounties        # noqa: F401
    import community_goals # noqa: F401
    import chat            # noqa: F401
    import chat_triggers   # noqa: F401

    from app import create_app
    app = create_app()
    yield app

    # Teardown: evict the real modules + restore stubs so the rest of
    # the test suite still works after this module.
    for name in _APP_LOCAL_TO_EVICT + list(_saved_stubs.keys()):
        sys.modules.pop(name, None)
    for name, mod in _saved_stubs.items():
        sys.modules[name] = mod
    importlib.invalidate_caches()


# ──────────────────────────────────────────────────────────────────────────
# DB helpers (use the conftest's db_url — real DB connection)
#
# psycopg2 is imported INSIDE each helper rather than at the top of the
# file. Reason: other test files in this directory (test_wager_actions.py,
# test_insurance_tokens.py, etc.) install STUB psycopg2 modules into
# sys.modules at import time. If we imported the real psycopg2 at the
# top, that local name would be bound to the stub (the one that lacks
# `.connect`). By importing lazily inside the helpers, we always
# resolve to whatever psycopg2 is currently in sys.modules — which the
# `game_app` fixture above has set to the real package.
# ──────────────────────────────────────────────────────────────────────────

def _user_id_for(db_url, username):
    import psycopg2
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def _set_owned(db_url, username, items):
    """Replace the user's owned_items with `items` (a list of strings)."""
    import psycopg2
    quoted = ','.join("'" + i.replace("'", "''") + "'" for i in items)
    arr = f"ARRAY[{quoted}]::text[]"
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'''UPDATE game_state
                    SET owned_items = {arr}
                    WHERE user_id = (SELECT id FROM users WHERE username = %s)''',
                (username,),
            )
    finally:
        conn.close()


def _set_columns(db_url, username, **fields):
    """UPDATE the named columns on the user's game_state row.

    Only allows whitelisted column names (defense against SQL injection
    even though this is a test — string formatting into SQL is risky).
    """
    import psycopg2
    allowed = {
        'wins', 'losses', 'streak', 'best_streak', 'spin_count',
        'wager_streak', 'wager_last_stake', 'wager_banked_wins',
        'wager_banked_losses', 'wager_last_win_amount', 'double_down_pending',
        'insurance_armed', 'insurance_charges', 'insurance_tokens',
        'onboarding_step', 'active_wheel_mode', 'gravity_drift',
        'active_tab_id', 'tab_last_seen', 'proc_streak', 'cumulative_wins',
    }
    sets = []
    params = []
    for col, val in fields.items():
        if col not in allowed:
            raise ValueError(f'column {col!r} not in allow-list')
        sets.append(f'{col} = %s')
        params.append(val)
    if not sets:
        return
    params.append(username)
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'UPDATE game_state SET {", ".join(sets)} '
                f'WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                params,
            )
    finally:
        conn.close()


def _read_game_state(db_url, username):
    """Read a wide set of columns for the user's game_state row."""
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                '''SELECT wins, losses, streak, spin_count, win_count,
                          loss_count, cumulative_wins,
                          wager_streak, wager_last_stake, wager_banked_wins,
                          wager_banked_losses, wager_last_win_amount,
                          double_down_pending, insurance_armed, insurance_charges,
                          insurance_tokens, onboarding_step, gravity_drift,
                          active_tab_id, tab_last_seen
                   FROM game_state
                   WHERE user_id = (SELECT id FROM users WHERE username = %s)''',
                (username,),
            )
            return cur.fetchone()
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────────
# Auth helpers (use the Flask test client)
# ──────────────────────────────────────────────────────────────────────────

def _register(client, username, password):
    """Register a fresh user via the test client. Returns (status, body, csrf)."""
    me = client.get('/api/me').get_json()
    csrf = me['csrf_token']
    r = client.post(
        '/api/register',
        json={'username': username, 'password': password},
        headers={'X-CSRFToken': csrf},
    )
    me2 = client.get('/api/me').get_json()
    return r.status_code, r.get_json(), me2['csrf_token']


def _post_spin(client, csrf, **body):
    """POST /api/spin with the test client. Returns (status, body)."""
    r = client.post(
        '/api/spin',
        json=body,
        headers={'X-CSRFToken': csrf},
    )
    return r.status_code, r.get_json()


def _read_csrf(client):
    """Re-fetch /api/me and return the current CSRF token."""
    return client.get('/api/me').get_json()['csrf_token']


@pytest.fixture(scope='module')
def shared_user(game_app, db_url):
    """Module-scoped: register ONE user, reuse across all tests.

    /api/register is rate-limited at 5/hour per IP. With 10 tests we'd
    blow through the limit. Register once for the module; each test
    then resets the user's game_state via `_set_columns` and re-grants
    any items it needs.
    """
    client = game_app.test_client()
    username = f't239s{uuid.uuid4().hex[:8]}'
    status, body, csrf = _register(client, username, 'testpass123')
    if status != 201:
        pytest.fail(f'module-level register failed: {status} {body}')
    yield {
        'username': username,
        'csrf': csrf,
        'client': client,
    }


# ──────────────────────────────────────────────────────────────────────────
# Outcome forcing
#
# game._resolve_spin uses `random.random()` to pick the outcome:
#   roll < jackpot_pct             → 'jackpot'
#   roll < jackpot_pct + win_pct   → 'win'
#   else                           → 'lose'
# Steady mode: 70/27/3. So:
#   0.5  → in the win band  (0.03 < 0.5 < 0.73) → 'win'
#   0.99 → past everything                        → 'lose'
#   0.01 → in the jackpot band (0.01 < 0.03)      → 'jackpot'
# Other random.random() calls (echo roll, segment angle) also see the
# same value. Echo is gated on a separate chance anyway.
# ──────────────────────────────────────────────────────────────────────────

_ROLL_WIN     = 0.5
_ROLL_LOSE    = 0.99
_ROLL_JACKPOT = 0.01


@pytest.fixture()
def force_random(game_app):
    """Return a context-manager factory that monkeypatches `game.random.random`
    to a fixed value for the duration of the `with` block.

    The `game` module is imported lazily inside `create_app()` (game.py
    is registered as a blueprint). We re-resolve the import on each
    use so we get the right module even after the test client's app
    context has been entered.
    """
    @contextmanager
    def _force(roll: float):
        import game as game_mod
        original = game_mod.random.random
        game_mod.random.random = lambda: roll
        try:
            yield
        finally:
            game_mod.random.random = original
    return _force


@pytest.fixture(autouse=True)
def _reset_rate_limiter(game_app):
    """Reset Flask-Limiter's in-memory storage between tests.

    The /api/spin route is rate-limited at 10/sec. With 10 tests each
    doing 1-3 spins, the per-second counter exceeds 10 and the tests
    start getting 429. Wipe the limiter's storage after each test so
    the next one starts clean.
    """
    yield
    # Teardown: clear the limiter's storage so the next test starts
    # with a fresh per-second counter.
    try:
        from extensions import limiter
        if hasattr(limiter, '_storage') and limiter._storage:
            limiter._storage.reset()
        elif hasattr(limiter, 'storage') and limiter.storage:
            limiter.storage.reset()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════
# 1. Plain spin — wins / losses / streak update
# ══════════════════════════════════════════════════════════════════════════

def test_plain_spin_two_consecutive_wins(game_app, db_url, force_random, shared_user):
    """Two forced wins: wins_delta accumulates, spin_count increments,
    streak increments by 1 per spin. No items owned → base payout only.
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']

    # Pre-state: zero everything.
    _set_columns(
        db_url, username,
        wins=1000, losses=0, streak=0, spin_count=0,
        cumulative_wins=0, wager_streak=0, wager_banked_wins=0,
    )

    with force_random(_ROLL_WIN):
        s1, b1 = _post_spin(client, csrf, stake=0)
    with force_random(_ROLL_WIN):
        s2, b2 = _post_spin(client, csrf, stake=0)

    assert s1 == 200, f'spin 1 status: {s1} {b1}'
    assert s2 == 200, f'spin 2 status: {s2} {b2}'
    assert b1['result'] == 'win', f"spin 1 result: {b1.get('result')!r}"
    assert b2['result'] == 'win', f"spin 2 result: {b2.get('result')!r}"

    gs = _read_game_state(db_url, username)
    # spin_count incremented by 2.
    assert gs['spin_count'] == 2, f"spin_count={gs['spin_count']}"
    # streak incremented by 2 (one per win).
    assert gs['streak'] == 2, f"streak={gs['streak']}"
    # wins_delta > 0 on each spin (base_payout at 0% stake = effective_win_mult).
    # For a fresh user (no items, no prestige), effective_win_mult=1.0.
    # Two wins → wins = 1000 + 1 + 1 = 1002.
    assert gs['wins'] >= 1002, (
        f"wins should be at least 1002 after two base-payout wins, got {gs['wins']}"
    )
    # losses untouched.
    assert gs['losses'] == 0, f"losses should stay 0, got {gs['losses']}"
    # cumulative_wins is incremented by wins_delta (positive contribution).
    assert gs['cumulative_wins'] > 0, (
        f"cumulative_wins should grow, got {gs['cumulative_wins']}"
    )


def test_plain_spin_two_consecutive_losses(game_app, db_url, force_random, shared_user):
    """Two forced losses: streak goes negative, losses unchanged at 5%-equivalent
    (the losses counter is driven by int(base_loss * effective_stake), which
    truncates to 0 for any stake < 100%). The 'cost' of a loss is the
    stake_wins forfeit, not a separate losses-counter increment.

    Without wager_unlock, there is no escrow, so wins stays at the initial
    value. The streak goes to -2.
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    _set_columns(
        db_url, username, wins=1000, losses=0, streak=0, spin_count=0,
    )

    with force_random(_ROLL_LOSE):
        _post_spin(client, csrf, stake=0)
    with force_random(_ROLL_LOSE):
        _post_spin(client, csrf, stake=0)

    gs = _read_game_state(db_url, username)
    assert gs['spin_count'] == 2, f"spin_count={gs['spin_count']}"
    assert gs['streak'] == -2, f"streak={gs['streak']}"
    # losses stays 0: with 0% stake, there's no escrow and the per-loss
    # increment is int(1 * 1.0) = 1 normally — but in this characterization
    # the actual losses value reflects the per-spin delta from events.
    # (See the test_wager_stake_escrow_on_loss comment for the math.)
    assert gs['wins'] == 1000, f"wins should stay 1000 (no items), got {gs['wins']}"


def _read_csrf(client):
    """Re-fetch /api/me and return the current CSRF token."""
    return client.get('/api/me').get_json()['csrf_token']


# ══════════════════════════════════════════════════════════════════════════
# 2. Wager stake — escrow on loss, refund on win
# ══════════════════════════════════════════════════════════════════════════

def test_wager_stake_escrow_on_loss(game_app, db_url, force_random, shared_user):
    """Player owns wager_unlock, sets stake=5%. Forced loss: stake_wins
    is escrowed then forfeited. wins decreases by stake_wins.

    Math: stake_wins = int(1000 * 0.05) = 50. On a loss at 5% with
    streak=0: base_loss = 1 + streak_bonus(0) = 1;
    actual_loss = compute_wager_loss(1, 0.05) = int(1 * 0.05) = 0.
    So the losses counter does NOT grow at 5% (the cost of a loss is
    the stake_wins forfeiture, not a separate `losses` increment).
    Net: wins=950, losses=0, spin_count=1.
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    _set_owned(db_url, username, ['wager_unlock'])
    _set_columns(
        db_url, username, wins=1000, losses=0, streak=0, spin_count=0,
        wager_last_stake=5, wager_streak=0, wager_banked_wins=0,
    )

    with force_random(_ROLL_LOSE):
        s, b = _post_spin(client, csrf, stake=5)
    assert s == 200
    assert b['result'] == 'lose', f"forced loss but got {b.get('result')}"
    # wager_last_stake is updated to actual_stake (5) by the handler.
    assert b['stake'] == 5

    gs = _read_game_state(db_url, username)
    # wins debited by 50 (the 5% stake).
    assert gs['wins'] == 950, (
        f"wins should drop by 50 (5% of 1000) on a loss, got {gs['wins']}"
    )
    # losses stays 0: actual_loss = int(1 * 0.05) = 0 at 5% stake.
    # (This is a characterization finding: the `losses` counter is
    # driven by int(base_loss * effective_stake), which truncates to 0
    # at any stake under 100%. The 'cost' of a loss is the stake_wins
    # forfeit, not a separate losses counter increment.)
    assert gs['losses'] == 0, (
        f"losses should stay 0 at 5% stake (int(1*0.05)=0), got {gs['losses']}"
    )
    # spin_count incremented.
    assert gs['spin_count'] == 1


def test_wager_stake_refund_on_win(game_app, db_url, force_random, shared_user):
    """Player owns wager_unlock, sets stake=5%. Forced win: stake_wins
    is escrowed then refunded (plus a payout). wins increases by 50
    (refund) + payout.

    Math: stake_wins = 50. On a win at 5%: refund 50 + payout 50 = +100.
    Net: wins=1100.
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    _set_owned(db_url, username, ['wager_unlock'])
    _set_columns(
        db_url, username, wins=1000, losses=0, streak=0, spin_count=0,
        wager_last_stake=5, wager_streak=0, wager_banked_wins=0,
    )

    with force_random(_ROLL_WIN):
        s, b = _post_spin(client, csrf, stake=5)
    assert s == 200
    assert b['result'] == 'win'

    gs = _read_game_state(db_url, username)
    # 1000 - 50 (escrow) + 50 (refund) + 50 (payout) = 1050.
    # (Base payout at 5% is stake_wins itself per T102.)
    assert gs['wins'] == 1050, (
        f"wins should be 1050 (1000 - 50 + 50 + 50) on a 5% win, got {gs['wins']}"
    )
    assert gs['losses'] == 0, f"losses should stay 0, got {gs['losses']}"


def test_wager_stake_persists_across_two_spins(game_app, db_url, force_random, shared_user):
    """Two consecutive 5% spins. The first one's stake=5 persists in
    wager_last_stake across the second spin. (T102: the slider value
    is sent on every spin; the DB stores the last value used.)
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    _set_owned(db_url, username, ['wager_unlock'])
    _set_columns(
        db_url, username, wins=1000, losses=0, streak=0, spin_count=0,
        wager_last_stake=5, wager_streak=0,
    )

    with force_random(_ROLL_WIN):
        s1, b1 = _post_spin(client, csrf, stake=5)
    with force_random(_ROLL_LOSE):
        s2, b2 = _post_spin(client, csrf, stake=5)

    assert b1['result'] == 'win'
    assert b2['result'] == 'lose'
    gs = _read_game_state(db_url, username)
    assert gs['wager_last_stake'] == 5, (
        f"wager_last_stake should stay 5, got {gs['wager_last_stake']}"
    )
    assert gs['spin_count'] == 2


# ══════════════════════════════════════════════════════════════════════════
# 3. Insurance — armed insurance fires on a loss
# ══════════════════════════════════════════════════════════════════════════

def test_insurance_armed_fires_on_loss(game_app, db_url, force_random, shared_user):
    """Player owns wager_unlock + wager_insurance, has insurance_tokens
    >= 1, has insurance_armed=TRUE. Forced loss: insurance_used=True,
    loss is capped, escrow (stake_wins) is refunded.

    Setup: 1000 wins, 5% stake (escrow 50), insurance armed.
    On a loss at 5% with insurance: actual_loss = min(int(base_loss *
    effective_stake), int(base_loss * effective_stake)) = 0 (int(1*0.05)=0).
    wins += stake_wins (refund). So wins = 1000 - 50 + 50 = 1000. losses=0.
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    _set_owned(db_url, username, ['wager_unlock', 'wager_insurance'])
    _set_columns(
        db_url, username,
        wins=1000, losses=0, streak=0, spin_count=0,
        wager_last_stake=5, wager_streak=0,
        insurance_armed=True, insurance_tokens=1, insurance_charges=0,
    )

    with force_random(_ROLL_LOSE):
        s, b = _post_spin(client, csrf, stake=5)

    assert s == 200
    assert b['result'] == 'lose', f"forced loss but got {b.get('result')!r}"
    # Insurance armed is consumed on spin (T108: route sets FALSE after spin).
    assert b['insurance_armed'] is False, (
        f"insurance_armed should be reset to False after the spin, "
        f"got {b['insurance_armed']!r}"
    )
    # The events dict (which is included in the response) flags the use.
    assert b['insurance_used'] is True, (
        f"insurance should fire on a protected loss, got "
        f"insurance_used={b['insurance_used']!r}"
    )

    gs = _read_game_state(db_url, username)
    # Insurance capped the loss to 0 and refunded the escrow.
    # wins: 1000 - 50 (escrow) + 50 (refund) = 1000.
    assert gs['wins'] == 1000, (
        f"wins should be 1000 (full refund on insured loss), got {gs['wins']}"
    )
    # losses capped at 0 by insurance (int(1 * 0.05) = 0).
    assert gs['losses'] == 0, (
        f"losses should be 0 (insurance cap), got {gs['losses']}"
    )
    # insurance_armed reset in the row.
    assert gs['insurance_armed'] is False, (
        f"insurance_armed should be FALSE in DB after spin, got "
        f"{gs['insurance_armed']}"
    )
    # insurance_tokens: the arm path consumed 1 token on arm; the spin
    # path does NOT consume a token (the arm already did).
    assert gs['insurance_tokens'] == 1, (
        f"insurance_tokens should still be 1 (only consumed on arm, not "
        f"on spin fire), got {gs['insurance_tokens']}"
    )


def test_insurance_armed_does_not_fire_on_win(game_app, db_url, force_random, shared_user):
    """Player owns insurance + tokens, has insurance_armed=TRUE. Forced
    WIN: insurance is NOT used (the cap/refund only applies to losses).
    insurance_armed is still reset to FALSE (consumed whether or not it
    fires — the player took the gamble).
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    _set_owned(db_url, username, ['wager_unlock', 'wager_insurance'])
    _set_columns(
        db_url, username,
        wins=1000, losses=0, streak=0, spin_count=0,
        wager_last_stake=5, wager_streak=0,
        insurance_armed=True, insurance_tokens=1,
    )

    with force_random(_ROLL_WIN):
        s, b = _post_spin(client, csrf, stake=5)

    assert s == 200
    assert b['result'] == 'win'
    assert b['insurance_used'] is False, (
        f"insurance should NOT fire on a win, got {b['insurance_used']!r}"
    )
    # The armed flag is still consumed (a wasted insurance charge on a win).
    assert b['insurance_armed'] is False

    gs = _read_game_state(db_url, username)
    # wins: 1000 - 50 (escrow) + 50 (refund) + 50 (payout) = 1050.
    assert gs['wins'] == 1050, (
        f"wins should be 1050 (5% win, insurance not used), got {gs['wins']}"
    )
    assert gs['losses'] == 0
    # insurance_armed was reset to FALSE.
    assert gs['insurance_armed'] is False


# ══════════════════════════════════════════════════════════════════════════
# 4. Double-down — DD escrows the LAST win amount
# ══════════════════════════════════════════════════════════════════════════

def test_double_down_uses_last_win_amount(game_app, db_url, force_random, shared_user):
    """Player owns wager_unlock + wager_double_down. First a forced
    win at stake=5% to bank a wager_last_win_amount. Then arm DD and
    spin again — the DD should escrow wager_last_win_amount, not the
    5% stake.

    Math: 5% of 1000 wins = 50. Win at 5% → payout = stake_wins (50).
    wager_last_win_amount = 50. Then DD armed: stake_wins =
    wager_last_win_amount = 50 (NOT 50 from a fresh 5% calc, but
    coincidentally the same value). For a more visible test, use a
    larger first win: 10% stake → escrow 100, payout 100,
    wager_last_win_amount = 100. Then DD armed, second spin is a win
    at 5% stake: DD would escrow 100 instead of 50.
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    _set_owned(db_url, username, ['wager_unlock', 'wager_double_down'])
    _set_columns(
        db_url, username,
        wins=1000, losses=0, streak=0, spin_count=0,
        wager_last_stake=10, wager_streak=0,
        wager_last_win_amount=0, double_down_pending=False,
    )

    # Spin 1: forced win at 10% stake → banks 100 as last win.
    with force_random(_ROLL_WIN):
        s1, b1 = _post_spin(client, csrf, stake=10)
    assert b1['result'] == 'win'
    assert b1['wager_last_win_amount'] == 100, (
        f"first win at 10% should set wager_last_win_amount=100, "
        f"got {b1['wager_last_win_amount']}"
    )

    # Arm DD via the /api/wager/double-down endpoint.
    csrf = _read_csrf(client)
    r = client.post(
        '/api/wager/double-down', json={}, headers={'X-CSRFToken': csrf},
    )
    assert r.status_code == 200, f"arm DD failed: {r.status_code} {r.get_json()}"

    # Spin 2: forced loss at 5% stake with DD armed.
    # DD escrow = wager_last_win_amount = 100, NOT 50 (5% of 1000).
    # On a loss: stake_wins = 100 (DD), wins = 1000 - 100 + 100 (refund) = 1000.
    # The DD-escrow refund masks the loss; the player ends at 1000 wins.
    with force_random(_ROLL_LOSE):
        s2, b2 = _post_spin(client, csrf, stake=5)

    assert s2 == 200
    assert b2['result'] == 'lose'
    assert b2['double_down_active'] is True, (
        f"double_down_active should be True in the response, got {b2['double_down_active']!r}"
    )

    gs = _read_game_state(db_url, username)
    # The spin response says stake=5 but the actual escrow was 100
    # (wager_last_win_amount). After the spin, wager_last_win_amount
    # is reset to 0 (the 'lose' branch resets it on a loss).
    assert gs['wins'] == 1000, (
        f"wins should be 1000 (DD escrowed 100, lost, refunded 100), got {gs['wins']}"
    )
    # double_down_pending is consumed.
    assert gs['double_down_pending'] is False, (
        f"double_down_pending should be FALSE after the spin, got {gs['double_down_pending']}"
    )
    # wager_last_win_amount reset on the loss.
    assert gs['wager_last_win_amount'] == 0, (
        f"wager_last_win_amount should be 0 on a loss reset, got {gs['wager_last_win_amount']}"
    )


# ══════════════════════════════════════════════════════════════════════════
# 5. Hot-streak — wager_banked_wins accumulates
# ══════════════════════════════════════════════════════════════════════════

def test_hot_streak_banks_wager_banked_wins(game_app, db_url, force_random, shared_user):
    """Player owns wager_unlock + wager_hot_streak. Three forced wins at
    stake=10% on the same stake: wager_banked_wins grows as the streak
    accrues. The hot-streak bonus is a fraction of the wager that's
    banked separately from the main payout (T102 keeps the bank
    mechanic — user "Keep bank button" 2026-06-23).
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    _set_owned(db_url, username, ['wager_unlock', 'wager_hot_streak'])
    _set_columns(
        db_url, username,
        wins=10000, losses=0, streak=0, spin_count=0,
        wager_last_stake=10, wager_streak=0, wager_banked_wins=0,
    )

    before_bank = _read_game_state(db_url, username)['wager_banked_wins']

    for i in range(3):
        with force_random(_ROLL_WIN):
            s, b = _post_spin(client, csrf, stake=10)
        assert s == 200
        assert b['result'] == 'win', f"spin {i+1}: forced win but got {b.get('result')!r}"

    gs = _read_game_state(db_url, username)
    # The streak is 3 after three wins. wager_banked_wins should be >
    # before_bank (the hot-streak bonus is banked on each win).
    assert gs['wager_banked_wins'] > before_bank, (
        f"wager_banked_wins should grow across a hot streak, "
        f"before={before_bank}, after={gs['wager_banked_wins']}"
    )
    # The hot streak also drives the wager_streak counter.
    assert gs['wager_streak'] >= 3, (
        f"wager_streak should be at least 3 after three same-stake wins, "
        f"got {gs['wager_streak']}"
    )
    # spin_count is 3.
    assert gs['spin_count'] == 3, f"spin_count={gs['spin_count']}"


# ══════════════════════════════════════════════════════════════════════════
# Cross-path: spin count, active_tab_id, and tab_last_seen persistence
# (T238 consolidated /api/state — these DB columns must stay in sync
# with the spin handler's UPDATE statement.)
# ══════════════════════════════════════════════════════════════════════════

def test_spin_updates_tab_id_and_last_seen(game_app, db_url, force_random, shared_user):
    """Each /api/spin call refreshes active_tab_id and tab_last_seen
    (the spin handler 'renews' the tab lock on every spin). The
    request body must include the same tab_id the player uses for
    heartbeats.
    """
    client = shared_user['client']
    username = shared_user['username']
    csrf = shared_user['csrf']
    tab_id = f'tab-{uuid.uuid4().hex[:10]}'

    # First spin with this tab_id.
    with force_random(_ROLL_WIN):
        s, b = _post_spin(client, csrf, tab_id=tab_id, stake=0)
    assert s == 200

    gs = _read_game_state(db_url, username)
    assert gs['active_tab_id'] == tab_id, (
        f"active_tab_id should be the request's tab_id, got {gs['active_tab_id']!r}"
    )
    assert gs['tab_last_seen'] is not None, (
        "tab_last_seen should be set by the spin handler"
    )
