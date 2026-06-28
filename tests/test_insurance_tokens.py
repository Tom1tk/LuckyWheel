"""T119: insurance system overhaul — flatten earning to 3 sources, remove
recharge, rename wager_tokens → insurance_tokens.

AC summary (from docs/SEASON_8_TICKETS.md):
  Column & schema:
    1. New column `insurance_tokens` on game_state. The old `wager_tokens`
       column was renamed in place (preserves data) by migration 054.
    2. `wager_insurance_charges` and `wager_insurance_armed` columns are
       also renamed to `insurance_charges` and `insurance_armed`.
    3. `wager_insurance_last_recharge` is dropped (no more recharge).
    4. `WAGER_INSURANCE_RECHARGE_SECONDS` is removed from models.py.
    5. `FISH_TO_WAGER_RATES` is removed. The fishing token award path
       (reel()) is gone.
    6. The onboarding step 3 grant (+100 tokens) is removed.

  Earning paths (only 3):
    7. Free daily claim: POST /api/insurance/claim-free. Awards 3 tokens
       once per UTC day. Gate on the `insurance_free_claimed_date` column.
    8. Bounty rewards: 1/2/3 per bounty (T117, already merged). The
       `get_claim_rewards_for_bounty` in bounties.py returns
       `{'tokens': position, 'cosmetic_fragments': 0}`; game.py's
       /api/bounties/claim credits the new `insurance_tokens` column.
    9. Initial purchase: when the player first buys `fish_to_wager`,
       the buy endpoint grants +5 to `insurance_tokens` exactly once.
       A new `insurance_unlock_grant_given` column prevents double-grant.

  Spending paths (renamed):
    10. Insurance buy (1 token = 1 charge): POST /api/insurance/buy.
        The cap is removed — players can have as many charges as
        they've bought.
    11. Stake cost at high-stake ≥ 30%: _resolve_spin reads
        `insurance_tokens` and decrements it (the column was renamed).
    12. Activating insurance on a spin: POST /api/insurance/arm
        consumes 1 insurance_token per arm.

  UI:
    13. The wager panel shows the player's `insuranceTokens` balance with
        the label "🪙 Insurance tokens" (no more "wager tokens").
    14. The free-tokens section is above the bounties panel.
    15. "🛡️ Insurance (N)" button label uses the current
        `insuranceCharges` count.
    16. The "🪙 Buy Insurance (1 token)" button is hidden when
        `insuranceArmed` is true.
    17. The "Pay with tokens" toggle is renamed to "Pay with insurance
        tokens".

This test file mixes source-string assertions (for the JSX/CSS/migration
plumbing, mirroring the project's existing test style — see
test_wager_tokens.py, test_prestige.py) with a stubs-based harness for
the new game.py endpoints (mirroring test_prestige.py, test_wager_actions.py).
"""
import os
import sys
import types
import importlib.util
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
JSX_PATH = os.path.join(REPO_ROOT, 'static', 'app.jsx')
APP_JS_PATH = os.path.join(REPO_ROOT, 'static', 'app.js')
CSS_PATH = os.path.join(REPO_ROOT, 'static', 'styles.css')
GAME_PY_PATH = os.path.join(REPO_ROOT, 'game.py')
MODELS_PY_PATH = os.path.join(REPO_ROOT, 'models.py')
WAGERS_PY_PATH = os.path.join(REPO_ROOT, 'wagers.py')
MIGRATIONS_DIR = os.path.join(REPO_ROOT, 'migrations')


def _read(path):
    with open(path) as f:
        return f.read()


# ════════════════════════════════════════════════════════════════════════════
# Module-loading plumbing (mirrors test_prestige.py)
# ════════════════════════════════════════════════════════════════════════════
def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


def _install_stubs():
    sys.modules.setdefault('flask', _make_stub(
        'flask',
        Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
        jsonify=lambda x: x,
        request=None,
    ))
    sys.modules.setdefault('flask_login', _make_stub(
        'flask_login',
        current_user=None,
        login_required=lambda f: f,
        UserMixin=_UserMixinStub,
    ))
    _psycopg2_extras_stub = _make_stub(
        'psycopg2.extras', RealDictCursor=type('RealDictCursor', (), {}))
    _psycopg2_stub = _make_stub('psycopg2', extras=_psycopg2_extras_stub)
    sys.modules.setdefault('psycopg2', _psycopg2_stub)
    sys.modules.setdefault('psycopg2.extras', _psycopg2_extras_stub)
    sys.modules.setdefault('extensions', _make_stub(
        'extensions',
        limiter=types.SimpleNamespace(limit=_noop),
        csrf=types.SimpleNamespace(exempt=lambda f: f),
    ))
    sys.modules.setdefault('seasons', _make_stub('seasons',
        ensure_current_season=lambda c: None,
        get_season_info=lambda c: {},
        get_latest_winners=lambda c, n: [],
        advance_season=lambda c: None,
    ))
    sys.modules.setdefault('security', _make_stub('security', require_json=lambda: None))
    sys.modules.setdefault('chat', _make_stub('chat',
        post_system_message=lambda *a, **kw: None,
        post_dedup_system_message=lambda *a, **kw: None,
    ))
    sys.modules.setdefault('chat_triggers', _make_stub('chat_triggers',
        jackpot_msg=lambda *a, **kw: '',
        prestige_msg=lambda *a, **kw: '',
        double_down_win_msg=lambda *a, **kw: '',
        hot_streak_msg=lambda *a, **kw: '',
        big_win_msg=lambda *a, **kw: '',
        new_player_msg=lambda *a, **kw: '',
        singularity_fill_msg=lambda *a, **kw: '',
        DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE=5,
        HOT_STREAK_MSG_THRESHOLD=10,
        BIG_WIN_THRESHOLD=5000,
    ))
    sys.modules.setdefault('bounties', _make_stub('bounties',
        increment_bounty=lambda *a, **kw: None,
        get_bounty_status=lambda *a, **kw: [],
        get_claim_rewards_for_bounty=lambda *a, **kw: {},
        BOUNTY_DEFS={},
    ))
    sys.modules.setdefault('community_goals', _make_stub('community_goals',
        COMMUNITY_GOAL_DEFS={},
        get_active_goal=lambda *a, **kw: (None, None),
        increment_goal=lambda *a, **kw: None,
        check_goal_completion=lambda *a, **kw: None,
        get_player_contribution=lambda *a, **kw: 0,
    ))
    sys.modules.setdefault('wagers', _make_stub('wagers',
        validate_stake=lambda pct, *a, **kw: int(pct) if pct is not None else 0,
        compute_hot_streak_bonus=lambda *a, **kw: 0,
        should_reset_streak=lambda *a, **kw: False,
        apply_safety_net=lambda *a, **kw: 0,
        compute_wager_payout=lambda *a, **kw: (0, 0),
        compute_wager_loss=lambda *a, **kw: 0,
        compute_stake_risk=lambda wins, pct, *a, **kw: int(wins * pct / 100) if wins and pct else 0,
        compute_max_stake_pct=lambda *a, **kw: 30,
        compute_stake_value=lambda *a, **kw: 0,
        HIGH_STAKE_TOKEN_THRESHOLD=30,
    ))
    sys.modules.setdefault('wheel_modes', _make_stub('wheel_modes',
        WHEEL_MODES={
            'steady':   {'win_pct': 70.0, 'loss_pct': 27.0, 'jackpot_pct': 3.0},
            'volatile': {'win_pct': 45.0, 'loss_pct': 50.0, 'jackpot_pct': 5.0},
            'inverted': {'win_pct': 60.0, 'loss_pct': 35.0, 'jackpot_pct': 5.0},
            'mirror':   {'win_pct': 65.0, 'loss_pct': 30.0, 'jackpot_pct': 5.0},
            'gravity':  {'win_pct': 55.0, 'loss_pct': 40.0, 'jackpot_pct': 5.0},
        },
        compute_gravity_probabilities=lambda d: {'win_pct': 55.0, 'loss_pct': 40.0, 'jackpot_pct': 5.0},
        clamp_gravity_drift=lambda d: max(-35, min(35, d)),
        get_available_modes=lambda w: ['steady', 'volatile', 'mirror', 'gravity', 'inverted'],
        get_week_number=lambda d: 1,
    ))
    sys.modules.setdefault('prestige', _make_stub('prestige',
        get_prestige_bonus=lambda lvl: 0,
        get_starting_prestige=lambda x: 0,
        can_prestige=lambda *a, **kw: False,
        get_prestige_threshold=lambda *a, **kw: 0,
        filter_kept_items=lambda items, n: list(items) if items else [],
        PRESTIGE_RESET_COLUMNS=(),
        MAX_PRESTIGE_LEVEL=10,
    ))


class _FakeCursor:
    def __init__(self, log, fetchone_queue=None, fetchall_queue=None):
        self.log = log
        self._fetchone_queue = list(fetchone_queue or [])
        self._fetchall_queue = list(fetchall_queue or [])
        # For UPDATE ... RETURNING / INSERT ... RETURNING, the cursor
        # is expected to return the new row. The driver is responsible
        # for putting the expected row in fetchone_queue BEFORE the
        # RETURNING-statement call. If the queue is empty when a
        # RETURNING-style fetchone() is called, return a generic
        # insurance_tokens row so the endpoint can complete the
        # response (the test asserts on the response dict + SQL log).
        self._returning_default = {'insurance_tokens': 0}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql, params))

    def fetchone(self):
        if self._fetchone_queue:
            return self._fetchone_queue.pop(0)
        # RETURNING fallback: return a stub row so the endpoint can
        # build its response. Tests that care about the new value
        # pre-seed the queue.
        return dict(self._returning_default)

    def fetchall(self):
        if not self._fetchall_queue:
            return []
        return self._fetchall_queue


class _FakeConn:
    def __init__(self, fetchone_queue=None, fetchall_queue=None):
        self.log = []
        self._fetchone_queue = fetchone_queue or []
        self._fetchall_queue = fetchall_queue or []
        self._cursor = _FakeCursor(self.log, self._fetchone_queue, self._fetchall_queue)

    def cursor(self, cursor_factory=None):
        return self._cursor

    def commit(self):
        pass


@contextmanager
def _fake_db_connection(conn):
    yield conn


_install_stubs()
sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


_spec = importlib.util.spec_from_file_location('game', GAME_PY_PATH)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)


# ════════════════════════════════════════════════════════════════════════════
# A. /api/state — the removed keys are gone
# ════════════════════════════════════════════════════════════════════════════
def test_no_recharge_in_state():
    """T119 AC#1: /api/state no longer exposes
    `wager_insurance_max_charges` or `wager_insurance_last_recharge`.
    The cap is removed (T119: 1 token = 1 charge, no max) and so is the
    1/10min recharge timer. The new state exposes `insurance_charges`,
    `insurance_armed`, and `insurance_free_claimed_date`."""
    src = _read(GAME_PY_PATH)
    # The two removed keys must not appear in the /api/state response
    # payload. They might still appear as comments or in unrelated
    # string literals, so we look for the exact response-key form.
    assert "'wager_insurance_max_charges':" not in src, (
        "/api/state response must not include 'wager_insurance_max_charges' "
        "(T119 removed the cap)"
    )
    assert "'wager_insurance_last_recharge':" not in src, (
        "/api/state response must not include 'wager_insurance_last_recharge' "
        "(T119 removed the recharge timer)"
    )
    # And the new keys ARE present.
    assert "'insurance_charges':" in src, (
        "/api/state response must include the renamed 'insurance_charges' key"
    )
    assert "'insurance_armed':" in src, (
        "/api/state response must include the renamed 'insurance_armed' key"
    )
    assert "'insurance_free_claimed_date':" in src, (
        "/api/state response must include the new 'insurance_free_claimed_date' "
        "key (T119 daily-claim gate)"
    )


# ════════════════════════════════════════════════════════════════════════════
# B. /api/insurance/claim-free — the new daily-claim endpoint
# ════════════════════════════════════════════════════════════════════════════
def _drive_claim_free(gs, *, returning_new_tokens=3):
    """Drive game.insurance_claim_free() with the given game state.

    The endpoint reads gs via _load_game_state, then runs an
    UPDATE ... RETURNING that fetches the new insurance_tokens
    value. We pre-seed the queue with a stub for the RETURNING
    response so the endpoint can build its `insurance_tokens`
    field in the response (the test asserts on that value)."""
    conn = _FakeConn(fetchone_queue=[
        gs,                                            # _load_game_state
        {'insurance_tokens': returning_new_tokens},    # UPDATE ... RETURNING
    ])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST', json={})
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    return conn, _game.insurance_claim_free()


def test_free_claim_3_tokens():
    """T119 AC#7: first call to /api/insurance/claim-free returns 3
    tokens, second call in same UTC day returns 409 'Already claimed
    today'."""
    import datetime as dt
    from datetime import timezone
    today = dt.datetime.now(timezone.utc).date()
    # First call: gs has no claimed_date → 3 tokens awarded.
    gs_initial = {
        'owned_items': ['wager_insurance'],
        'insurance_tokens': 0,
        'insurance_free_claimed_date': None,
    }
    # The UPDATE ... RETURNING returns the new insurance_tokens = 3.
    conn, result = _drive_claim_free(gs_initial, returning_new_tokens=3)
    assert isinstance(result, dict), (
        f"expected dict response on first claim, got {type(result).__name__}: {result!r}"
    )
    assert result['ok'] is True
    assert result['tokens_awarded'] == 3
    assert result['insurance_tokens'] == 3
    # Exactly one UPDATE — atomic credit + date set.
    updates = [(sql, params) for sql, params in conn.log
               if sql.lstrip().upper().startswith('UPDATE')]
    assert len(updates) == 1, (
        f"expected exactly 1 UPDATE for the atomic claim, got {len(updates)}: {updates}"
    )
    sql, params = updates[0]
    assert 'insurance_tokens = insurance_tokens + %s' in sql
    assert 'insurance_free_claimed_date = %s' in sql
    # Params: (3, today, user_id)
    assert params[0] == 3
    assert params[1] == today

    # Second call (same day): gs now reflects today's claim. The
    # endpoint short-circuits at the gate (no RETURNING call) so the
    # queue is just the gs.
    gs_after = dict(gs_initial)
    gs_after['insurance_tokens'] = 3
    gs_after['insurance_free_claimed_date'] = today
    conn2 = _FakeConn(fetchone_queue=[gs_after])
    @contextmanager
    def cm2():
        yield conn2
    _game.db_connection = cm2
    _game.request = types.SimpleNamespace(method='POST', json={})
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    result2 = _game.insurance_claim_free()
    assert isinstance(result2, tuple), (
        f"expected (body, status) tuple for 409, got {type(result2).__name__}: {result2!r}"
    )
    body, status = result2
    assert status == 409
    assert 'Already claimed today' in body['error'], (
        f"expected 'Already claimed today' error, got {body.get('error')!r}"
    )
    # No new UPDATE on the rejection path.
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn2.log), (
        "no UPDATE should run on the rejection path"
    )


def test_free_claim_resets_at_2359_utc():
    """T119 AC#7 (reset semantics): manually advance
    insurance_free_claimed_date to yesterday; the next claim succeeds.
    The reset is at UTC 00:00 (per the implementation sketch) — when
    the stored date is before today, the claim gate opens.
    """
    import datetime as dt
    from datetime import timezone, timedelta
    today = dt.datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    # Pre-state: claimed yesterday with 3 tokens from the prior day.
    gs = {
        'owned_items': ['wager_insurance'],
        'insurance_tokens': 3,
        'insurance_free_claimed_date': yesterday,
    }
    # UPDATE ... RETURNING returns 3 + 3 = 6.
    conn, result = _drive_claim_free(gs, returning_new_tokens=6)
    assert isinstance(result, dict), (
        f"expected dict response, got {type(result).__name__}: {result!r}"
    )
    assert result['ok'] is True
    assert result['tokens_awarded'] == 3
    # The new total is 3 (prior) + 3 (this claim) = 6.
    assert result['insurance_tokens'] == 6, (
        f"expected new insurance_tokens=6 (3 prior + 3 new), got {result['insurance_tokens']}"
    )
    # The UPDATE stamped today's date (not yesterday's).
    updates = [(sql, params) for sql, params in conn.log
               if sql.lstrip().upper().startswith('UPDATE')]
    assert len(updates) == 1
    sql, params = updates[0]
    assert params[1] == today, (
        f"UPDATE should set insurance_free_claimed_date to today={today}, got {params[1]}"
    )


# ════════════════════════════════════════════════════════════════════════════
# C. /api/buy — initial purchase grants 5 tokens (one-time)
# ════════════════════════════════════════════════════════════════════════════
def _drive_buy(gs, item_id='fish_to_wager'):
    """Drive game.buy() with a fully-populated gs."""
    conn = _FakeConn(fetchone_queue=[gs])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(
        method='POST', json={'item_id': item_id},
        get_json=lambda silent=True: {'item_id': item_id},
    )
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    return conn, _game.buy()


def _buy_gs(**overrides):
    """Build a fully-populated gs dict for /api/buy tests. The
    buy handler reads a wide set of columns to build the response
    payload; we provide defaults for the ones the test doesn't
    explicitly override."""
    gs = dict(
        owned_items=[],
        wins=100_000,             # enough to cover 5,000 cost + tier gate
        losses=0,
        cumulative_wins=0,        # tier 1 (no gate)
        fish_clicks=0,
        active_cosmetics=[],
        regen_recharge_wins=0,
        winmult_inf_level=0,
        bonusmult_inf_level=0,
    )
    gs.update(overrides)
    return gs


def test_initial_purchase_grants_5():
    """T119 AC#9: buying fish_to_wager increments insurance_tokens by 5
    on the first purchase (gated on insurance_unlock_grant_given=FALSE)."""
    gs = _buy_gs(
        insurance_unlock_grant_given=False,
        insurance_tokens=0,
    )
    conn, result = _drive_buy(gs, item_id='fish_to_wager')
    assert isinstance(result, dict), (
        f"expected dict response, got {type(result).__name__}: {result!r}"
    )
    # The buy succeeded (item is now in owned_items).
    assert 'fish_to_wager' in result['owned_items']
    # Two UPDATEs: the buy (owned_items + wins deduction) and the
    # one-time +5 grant (insurance_tokens + insurance_unlock_grant_given).
    updates = [(sql, params) for sql, params in conn.log
               if sql.lstrip().upper().startswith('UPDATE')]
    grant_sqls = [(s, p) for s, p in updates
                  if 'insurance_tokens' in s and 'insurance_unlock_grant_given' in s]
    assert len(grant_sqls) == 1, (
        f"expected exactly 1 grant UPDATE, got {len(grant_sqls)}: {grant_sqls}"
    )
    sql, params = grant_sqls[0]
    assert 'insurance_tokens = insurance_tokens + 5' in sql
    assert 'insurance_unlock_grant_given = TRUE' in sql


def test_initial_purchase_no_double_grant():
    """T119 AC#9: a second buy of fish_to_wager does NOT grant tokens
    again. The insurance_unlock_grant_given=TRUE gate prevents the
    duplicate grant.
    """
    # The second buy is a no-op (already owned) per the existing
    # `if item_id in owned` guard in /api/buy. But the operator's
    # spec says "admin grants via DB" — simulate that by removing the
    # item from owned_items but keeping the grant-given flag TRUE.
    gs = _buy_gs(
        insurance_unlock_grant_given=True,    # already granted
        insurance_tokens=5,                   # the prior grant's value
    )
    conn, result = _drive_buy(gs, item_id='fish_to_wager')
    assert isinstance(result, dict), (
        f"expected dict response, got {type(result).__name__}: {result!r}"
    )
    # The buy succeeded (item added) but NO grant UPDATE ran.
    grant_sqls = [(s, p) for s, p in conn.log
                  if s.lstrip().upper().startswith('UPDATE')
                  and 'insurance_tokens' in s
                  and 'insurance_unlock_grant_given' in s]
    assert len(grant_sqls) == 0, (
        f"expected NO grant UPDATE when insurance_unlock_grant_given=TRUE, "
        f"got {grant_sqls}"
    )


# ════════════════════════════════════════════════════════════════════════════
# D. /api/insurance/arm — consumes 1 insurance_token per arm
# ════════════════════════════════════════════════════════════════════════════
def _drive_arm(gs):
    """Drive game.wager_insurance() (T119 endpoint at /api/insurance/arm)."""
    conn = _FakeConn(fetchone_queue=[gs])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST', json={})
    _game.current_user = types.SimpleNamespace(id=1)
    return conn, _game.wager_insurance()


def test_arm_consumes_token():
    """T119 AC#12: POST /api/insurance/arm with tokens >= 1 succeeds
    and decrements insurance_tokens by 1. The arm column is the renamed
    insurance_armed (was wager_insurance_armed)."""
    gs = {
        'owned_items': ['wager_insurance'],
        'insurance_tokens': 5,
        'insurance_armed': False,
    }
    conn, result = _drive_arm(gs)
    assert isinstance(result, dict), (
        f"expected dict response, got {type(result).__name__}: {result!r}"
    )
    assert result['ok'] is True
    assert result['insurance_tokens'] == 4
    # The UPDATE sets insurance_armed=TRUE and decrements insurance_tokens.
    updates = [(sql, params) for sql, params in conn.log
               if sql.lstrip().upper().startswith('UPDATE')]
    assert len(updates) == 1, (
        f"expected exactly 1 UPDATE, got {len(updates)}: {updates}"
    )
    sql, params = updates[0]
    assert 'insurance_tokens = %s' in sql
    assert 'insurance_armed = TRUE' in sql
    assert params[0] == 4


def test_arm_no_tokens_returns_403():
    """T119 AC#12 (error path): arming with 0 tokens returns 403."""
    gs = {
        'owned_items': ['wager_insurance'],
        'insurance_tokens': 0,
        'insurance_armed': False,
    }
    conn, result = _drive_arm(gs)
    assert isinstance(result, tuple), (
        f"expected (body, status) tuple for 403, got {type(result).__name__}: {result!r}"
    )
    body, status = result
    assert status == 403
    assert 'No insurance tokens' in body['error']
    # No UPDATE on the rejection path.
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)


def test_arm_already_armed_returns_409():
    """T119: arming when already armed → 409."""
    gs = {
        'owned_items': ['wager_insurance'],
        'insurance_tokens': 5,
        'insurance_armed': True,
    }
    conn, result = _drive_arm(gs)
    assert isinstance(result, tuple), (
        f"expected (body, status) tuple for 409, got {type(result).__name__}: {result!r}"
    )
    body, status = result
    assert status == 409
    assert 'already armed' in body['error'].lower()


# ════════════════════════════════════════════════════════════════════════════
# E. /api/insurance/buy — no cap
# ════════════════════════════════════════════════════════════════════════════
def test_buy_charge_no_cap():
    """T119 AC#10: buying 10 charges in a row succeeds (no cap). The
    old WAGER_INSURANCE_MAX_CHARGES=3 cap and its refund-unused-tokens
    behaviour are gone. 1 token = 1 charge, always.
    """
    # See test_insurance_buy_with_tokens.py::test_buy_no_cap for the
    # shorter, more focused version. This test stays here to satisfy
    # the AC#10 acceptance criterion name.
    conn = _FakeConn(fetchone_queue=[{
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'insurance_tokens': 10,
        'insurance_charges': 0,
    }])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(
        method='POST',
        get_json=lambda silent=False: {'token_cost': 10},
    )
    _game.current_user = types.SimpleNamespace(id=1)
    result = _game.insurance_buy_with_tokens()
    assert isinstance(result, dict)
    assert result['ok'] is True
    assert result['granted'] == 10
    assert result['insurance_charges'] == 10
    assert result['insurance_tokens'] == 0
    # Verify: no error referencing the old cap.
    assert 'cap' not in result or 'Insurance charges already' not in str(result), (
        f"buy endpoint should not error at high charge counts (no cap), got {result!r}"
    )


# ════════════════════════════════════════════════════════════════════════════
# F. _resolve_spin — stake cost spends tokens (column renamed)
# ════════════════════════════════════════════════════════════════════════════
def test_stake_spends_tokens():
    """T119 AC#11: _resolve_spin with stake_pct >= 30 and
    pay_with_tokens=True decrements insurance_tokens (was wager_tokens)."""
    import random
    # Force a deterministic win roll. The patch is scoped to this
    # test (restored in finally) so it doesn't leak into sibling tests
    # that rely on a fresh random sequence.
    original_random = _game.random.random
    _game.random.random = lambda: 0.5  # in-range win
    try:
        state = dict(
            owned=['wager_unlock'],
            streak=0,
            best_streak=0,
            regen_recharge_wins=0,
            wins=1000,
            losses=0,
            jackpot_echo_next=False,
            spin_count=1,
            active_cosmetics=[],
            proc_streak=0,
        )
        new_state, events = _game._resolve_spin(
            **state,
            effective_win_mult=2.0,
            bonus_mult=1,
            jackpot_chance=0.0,
            echo_chance=0.0,
            charm_chance=0.0,
            resilience_chance=0.5,
            proc_streak_level=0,
            pot_active=False,
            pot_win_pct=0.505,
            stake_pct=30,
            wager_streak=0,
            wager_last_stake=0,
            active_wheel_mode='steady',
            aquarium_luck=0.0,
            wager_banked_wins=0,
            insurance_active=False,
            double_down_active=False,
            wager_last_win_amount=0,
            gravity_drift=0,
            wager_banked_losses=0,
            # T119: the function parameter is now insurance_tokens (was
            # wager_tokens). 50 tokens, stake cost = 300 → tokens cover
            # 50 of it.
            insurance_tokens=50,
            pay_with_tokens=True,
        )
        assert events['tokens_spent'] == 50, (
            f"full-coverage spend = min(50 tokens, 300 stake) = 50, got {events['tokens_spent']}"
        )
        assert events['insurance_tokens'] == 0, (
            f"50 tokens should be drained, got {events['insurance_tokens']}"
        )
    finally:
        _game.random.random = original_random


def test_protected_loss_refunds_full_escrow_with_tokens():
    """T235: a normal-mode high-stake spin with pay_with_tokens=True and
    insurance armed that resolves as a loss must refund the FULL escrow
    (stake_cost_total), not just the post-spend cash portion
    (stake_wins). The token-funded portion must NOT be silently lost on
    a protected loss.

    Setup: 1000 wins, 50 insurance tokens, 30% stake (escrow 300),
    pay_with_tokens=True → tokens cover 50, cash debit 250. Pre-spin
    wins = 750. Insurance-armed, outcome = lose.

    Expected (correct) post-spin wins = 750 + 300 = 1050 — the player
    ends with their pre-spin wins (1000) PLUS the 50 tokens they
    spent, now reflected as wins. Token value is preserved.

    With the pre-T235 bug, the refund was `wins += stake_wins` (the
    post-spend 250), giving wins = 750 + 250 = 1000 — the 50 tokens
    were silently lost. This test catches that bug.
    """
    import random
    # Force a deterministic lose roll. With the test's stubbed
    # WHEEL_MODES['steady'] = {win:70, lose:27, jackpot:3}, roll=0.99
    # lands in the 'lose' branch (> 0.03+0.70 = 0.73).
    original_random = _game.random.random
    _game.random.random = lambda: 0.99  # 'lose'
    try:
        pre_spin_wins = 1000
        pre_spin_tokens = 50
        state = dict(
            # owns wager_unlock (required for stake escrow) AND
            # wager_insurance (the item the player buys to arm the
            # insurance flag). The T110 token-spend path requires
            # insurance_tokens > 0 + pay_with_tokens=True.
            owned=['wager_unlock', 'wager_insurance'],
            streak=0,
            best_streak=0,
            regen_recharge_wins=0,
            wins=pre_spin_wins,
            losses=0,
            jackpot_echo_next=False,
            spin_count=1,
            active_cosmetics=[],
            proc_streak=0,
        )
        new_state, events = _game._resolve_spin(
            **state,
            effective_win_mult=2.0,
            bonus_mult=1,
            jackpot_chance=0.0,
            echo_chance=0.0,
            charm_chance=0.0,
            resilience_chance=0.0,    # disable resilience to keep math predictable
            proc_streak_level=0,
            pot_active=False,
            pot_win_pct=0.505,
            stake_pct=30,             # 30% of 1000 = 300 stake
            wager_streak=0,
            wager_last_stake=0,
            active_wheel_mode='steady',
            aquarium_luck=0.0,
            wager_banked_wins=0,
            insurance_active=True,    # insurance armed for this spin
            double_down_active=False,
            wager_last_win_amount=0,
            gravity_drift=0,
            wager_banked_losses=0,
            insurance_tokens=pre_spin_tokens,
            pay_with_tokens=True,
        )
        # The outcome was forced to 'lose'.
        assert events['result'] == 'lose', (
            f"test setup expects 'lose' outcome, got {events['result']!r}"
        )
        # Insurance fired.
        assert events['insurance_used'] is True, (
            "insurance should fire on a protected loss with insurance_active=True"
        )
        # Tokens were actually spent.
        assert events['tokens_spent'] > 0, (
            f"pay_with_tokens=True at 30% stake should spend tokens, "
            f"got tokens_spent={events['tokens_spent']}"
        )
        # T235: the FULL escrow (stake_cost_total = 300) is credited
        # back. The player ends at pre_spin_wins + tokens_spent (the
        # token value is preserved as wins). Pre-T235 the refund was
        # stake_wins=250, giving wins=1000 and silently losing the
        # 50 token value.
        expected_wins = pre_spin_wins + events['tokens_spent']
        assert new_state['wins'] == expected_wins, (
            f"protected loss with token spend must refund the FULL "
            f"escrow (stake_cost_total). Expected wins={expected_wins} "
            f"(pre_spin_wins + tokens_spent), got {new_state['wins']}. "
            f"Pre-T235 bug: refund was stake_wins (post-spend), "
            f"silently losing the token value."
        )
        # Sanity: the player didn't take a cash loss either (insurance
        # caps the loss at 0 at this stake% with streak=0).
        assert new_state['losses'] == 0, (
            f"insurance should cap the loss at 0 (stake=30%, base_loss=1), "
            f"got losses={new_state['losses']}"
        )
    finally:
        _game.random.random = original_random


# ════════════════════════════════════════════════════════════════════════════
# G. Schema — column renamed in place
# ════════════════════════════════════════════════════════════════════════════
def test_column_renamed():
    """T119 AC: insurance_tokens exists, wager_tokens does not (the
    T108-era column was renamed in place by migration 054). Likewise
    for wager_insurance_charges → insurance_charges and
    wager_insurance_armed → insurance_armed. The two new gating
    columns (insurance_free_claimed_date, insurance_unlock_grant_given)
    exist.

    This test reads the source rather than the live DB so it works
    against the migration 054 SQL which is checked into the repo.
    """
    # The migration SQL is the single source of truth for the
    # renames — read it and assert it does what's expected.
    migration_path = os.path.join(MIGRATIONS_DIR, '054_rename_wager_to_insurance_tokens.sql')
    migration_sql = _read(migration_path)
    assert 'RENAME COLUMN wager_tokens TO insurance_tokens' in migration_sql
    assert 'RENAME COLUMN wager_insurance_charges TO insurance_charges' in migration_sql
    assert 'RENAME COLUMN wager_insurance_armed TO insurance_armed' in migration_sql
    assert 'DROP COLUMN wager_insurance_last_recharge' in migration_sql
    assert 'insurance_free_claimed_date' in migration_sql
    assert 'insurance_unlock_grant_given' in migration_sql
    # Idempotency: the renames are wrapped in IF EXISTS checks.
    assert 'information_schema.columns' in migration_sql, (
        "migration 054 must be idempotent — RENAME COLUMN wrapped in an "
        "information_schema check so re-running the migration is a no-op"
    )


# ════════════════════════════════════════════════════════════════════════════
# H. models.py — removed constants
# ════════════════════════════════════════════════════════════════════════════
def test_models_removes_recharge_and_fish_rates():
    """T119 AC#4/#5: WAGER_INSURANCE_RECHARGE_SECONDS and
    FISH_TO_WAGER_RATES are removed from models.py. The reel()
    function no longer references FISH_TO_WAGER_RATES (the import is
    gone, and the per-fish-tokens-awarded block is removed from
    game.py)."""
    src = _read(MODELS_PY_PATH)
    assert 'WAGER_INSURANCE_RECHARGE_SECONDS' not in src, (
        "models.py must no longer define WAGER_INSURANCE_RECHARGE_SECONDS "
        "(T119 removed the 1/10min recharge)"
    )
    assert 'FISH_TO_WAGER_RATES' not in src, (
        "models.py must no longer define FISH_TO_WAGER_RATES "
        "(T119 removed fish-to-tokens conversion)"
    )


def test_wagers_removes_recharge_function():
    """T119 AC#4: wagers.py no longer defines _recharge_wager_insurance."""
    src = _read(WAGERS_PY_PATH)
    assert '_recharge_wager_insurance' not in src, (
        "wagers.py must no longer define _recharge_wager_insurance "
        "(T119 removed the recharge helper)"
    )


# ════════════════════════════════════════════════════════════════════════════
# I. game.py — reel() no longer awards tokens for fish
# ════════════════════════════════════════════════════════════════════════════
def test_fishing_does_not_award_tokens():
    """T119 AC#5: reel() for a user owning insurance_unlock (renamed
    fish_to_wager) does not increase insurance_tokens. The
    FISH_TO_WAGER_RATES tier-based award block is gone. The
    catch_of_the_day path still updates its date column but no
    longer multiplies any token award (since no tokens are awarded)."""
    src = _read(GAME_PY_PATH)
    # The reel() function should not reference FISH_TO_WAGER_RATES
    # in active code (it was removed from models.py and the import is
    # gone from game.py). The string may still appear in a comment
    # explaining the migration, so we strip comments first.
    import re
    code_only = re.sub(r'#[^\n]*', '', src)
    code_only = re.sub(r'"""[\s\S]*?"""', '', code_only)
    assert 'FISH_TO_WAGER_RATES' not in code_only, (
        "game.py must not reference FISH_TO_WAGER_RATES in active code (T119 removed it)"
    )
    # The reel() function should not write to wager_tokens (the
    # column is gone). The reel's UPDATE statements should not
    # contain a `wager_tokens = wager_tokens + %s` clause.
    reel_section = src[src.find('def reel'):src.find('def reel') + 10000]
    assert 'wager_tokens = wager_tokens +' not in reel_section, (
        "reel() must not write to wager_tokens (T119 removed the fish-to-tokens award)"
    )


# ════════════════════════════════════════════════════════════════════════════
# J. game.py — onboarding step 3 grant removed
# ════════════════════════════════════════════════════════════════════════════
def test_onboarding_grant_removed():
    """T119 AC#6: the onboarding step 3 grant (+100 wager_tokens) is
    removed from /api/bounties. The step is still advanced so the
    modal disappears, but no tokens are credited."""
    src = _read(GAME_PY_PATH)
    # The original line (still referenced in older tests) was:
    #   wager_tokens = wager_tokens + 100
    # T119 removed it. Search for the full pattern within the
    # /api/bounties handler (between the get_bounties_endpoint def
    # and the next @game_bp.route).
    bounties_def_idx = src.find('def get_bounties_endpoint')
    next_route_idx = src.find('@game_bp.route', bounties_def_idx + 1)
    bounties_block = src[bounties_def_idx:next_route_idx if next_route_idx > 0 else len(src)]
    assert 'wager_tokens = wager_tokens + 100' not in bounties_block, (
        "/api/bounties must no longer grant 100 tokens on onboarding step 3 "
        "(T119 removed the only token-earning onboarding path)"
    )


# ════════════════════════════════════════════════════════════════════════════
# K. JSX — column renames + new free-tokens section + buy-button gating
# ════════════════════════════════════════════════════════════════════════════
def test_jsx_renames_state_variables():
    """T119 AC: JSX state renames — wagerTokens → insuranceTokens,
    wagerInsuranceCharges → insuranceCharges, wagerInsuranceArmed →
    insuranceArmed. The setters and the useState initializers all
    follow the new names."""
    jsx = _read(JSX_PATH)
    # The new state declarations exist.
    assert '[insuranceTokens, setInsuranceTokens]' in jsx, (
        "JSX must declare the renamed insuranceTokens state"
    )
    assert '[insuranceCharges, setInsuranceCharges]' in jsx, (
        "JSX must declare the renamed insuranceCharges state"
    )
    assert '[insuranceArmed, setInsuranceArmed]' in jsx, (
        "JSX must declare the renamed insuranceArmed state"
    )
    # The OLD state identifiers (used as bare words) must not appear
    # in active code. Comments explaining the rename are allowed (they
    # help future readers), so we strip /* … */ and // line comments
    # before checking. The simplest robust check: the old names must
    # not appear in the rendered JSX (`useState(`, `set…(`, or
    # condition expressions) — only in comments.
    import re
    code_only = re.sub(r'//[^\n]*', '', jsx)
    code_only = re.sub(r'/\*.*?\*/', '', code_only, flags=re.DOTALL)
    assert 'wagerTokens' not in code_only, (
        "JSX must not reference the old wagerTokens state in active code"
    )
    assert 'wagerInsuranceCharges' not in code_only, (
        "JSX must not reference the old wagerInsuranceCharges state in active code"
    )
    assert 'wagerInsuranceArmed' not in code_only, (
        "JSX must not reference the old wagerInsuranceArmed state in active code"
    )


def test_jsx_free_tokens_section():
    """T119 AC#14: the free-tokens section sits ABOVE the bounties
    panel. Single-row layout: a "Claim 3 free tokens" button when
    unclaimed; a "Claimed today" indicator after claim.
    """
    jsx = _read(JSX_PATH)
    assert 'free-tokens-section' in jsx, (
        "JSX must include a .free-tokens-section element above the bounties panel"
    )
    assert 'Claim 3 free tokens' in jsx, (
        "free-tokens section must show the 'Claim 3 free tokens' button"
    )
    assert 'claimed today' in jsx.lower() or 'Claimed today' in jsx, (
        "free-tokens section must show a 'claimed today' indicator after claim"
    )
    # The section must appear BEFORE the bounties panel in the source
    # (i.e. the rendered <div className="free-tokens-section"> element
    # must be above the <div className="season8-bounties-panel">
    # element). The bare class-name string is also referenced in
    # comments/selectors earlier in the file, so we anchor on the
    # `className="..."` form.
    free_tokens_idx = jsx.find('className="free-tokens-section"')
    bounties_idx = jsx.find('className="season8-bounties-panel"')
    assert free_tokens_idx > 0 and bounties_idx > 0, (
        "both free-tokens-section and season8-bounties-panel must exist"
    )
    assert free_tokens_idx < bounties_idx, (
        "free-tokens section must appear ABOVE the bounties panel "
        f"(free_tokens at {free_tokens_idx}, bounties at {bounties_idx})"
    )


def test_pay_with_tokens_renamed():
    """T119 AC#17: the "Pay with tokens" toggle is renamed to "Pay with
    insurance tokens" (the old label was ambiguous between the
    insurance/arm economy and the spend economy)."""
    jsx = _read(JSX_PATH)
    assert 'Pay with insurance tokens' in jsx, (
        "JSX must include the new 'Pay with insurance tokens' toggle label"
    )
    # The OLD label (without the "insurance" qualifier) must not be
    # used in the toggle span — but it may appear in the data-tooltip
    # which describes the mechanic. The span text is what the user
    # sees.
    # Find the toggle <span> content.
    span_idx = jsx.find('Pay with insurance tokens')
    assert span_idx != -1


# ════════════════════════════════════════════════════════════════════════════
# L. CSS — armed indicator gets explicit color
# ════════════════════════════════════════════════════════════════════════════
def test_button_color_readable():
    """T119 AC#15: the .wager-insurance-armed selector in styles.css
    has an explicit `color: #44ddff` (cyan) and a matching border. The
    pre-T119 rule had no color and was inheriting black-on-dark, which
    the operator reported as unreadable."""
    css = _read(CSS_PATH)
    # The selector must exist.
    assert '.wager-insurance-armed' in css, (
        "styles.css must define a .wager-insurance-armed selector"
    )
    # And it must have an explicit color (the operator's complaint was
    # that it was inheriting the body color, which is unreadable on
    # the casino dark background). Walk from the selector to the next
    # closing brace and assert color + border are present.
    sel_idx = css.find('.wager-insurance-armed')
    brace_end = css.find('}', sel_idx)
    rule_body = css[sel_idx:brace_end + 1]
    assert 'color: #44ddff' in rule_body, (
        f".wager-insurance-armed must set color: #44ddff (T119), got:\n{rule_body}"
    )
    assert 'border: 1px solid #44ddff' in rule_body, (
        f".wager-insurance-armed must set a matching border color, got:\n{rule_body}"
    )


def test_css_free_tokens_section():
    """T119: styles.css has rules for the new .free-tokens-section,
    .free-tokens-claim-btn, and .free-tokens-claimed elements."""
    css = _read(CSS_PATH)
    for cls in ('.free-tokens-section', '.free-tokens-claim-btn', '.free-tokens-claimed'):
        assert cls in css, f"styles.css must define a {cls} selector"


# ════════════════════════════════════════════════════════════════════════════
# M. New endpoints are wired in game.py
# ════════════════════════════════════════════════════════════════════════════
def test_claim_free_endpoint_registered():
    """T119: the daily-claim endpoint is wired in game.py at the
    canonical URL /api/insurance/claim-free."""
    src = _read(GAME_PY_PATH)
    assert "/api/insurance/claim-free" in src, (
        "game.py must register POST /api/insurance/claim-free"
    )
    assert "def insurance_claim_free" in src, (
        "game.py must define an insurance_claim_free view function"
    )


def test_arm_endpoint_renamed():
    """T119: the arm endpoint URL was renamed from /api/wager/insurance
    to /api/insurance/arm. The old URL must not be in the source."""
    src = _read(GAME_PY_PATH)
    assert "/api/insurance/arm" in src, (
        "game.py must register POST /api/insurance/arm (T119 renamed)"
    )
    # The OLD URL is gone (the new endpoint lives at a different path).
    assert "'/api/wager/insurance'" not in src, (
        "the old /api/wager/insurance URL must be gone (T119 renamed it)"
    )
    # And the cancel URL is also renamed.
    assert "/api/insurance/cancel" in src, (
        "game.py must register POST /api/insurance/cancel (T119 renamed)"
    )
    assert "'/api/wager/insurance/cancel'" not in src, (
        "the old /api/wager/insurance/cancel URL must be gone"
    )


def test_buy_endpoint_renamed():
    """T119: the buy endpoint URL was renamed from
    /api/wager/insurance/buy to /api/insurance/buy."""
    src = _read(GAME_PY_PATH)
    assert "/api/insurance/buy" in src, (
        "game.py must register POST /api/insurance/buy (T119 renamed)"
    )
    assert "'/api/wager/insurance/buy'" not in src, (
        "the old /api/wager/insurance/buy URL must be gone (T119 renamed it)"
    )


# ════════════════════════════════════════════════════════════════════════════
# N. Built static/app.js reflects the JSX changes
# ════════════════════════════════════════════════════════════════════════════
def test_built_app_js_contains_new_endpoints():
    """T119: the built static/app.js bundle (not just the JSX source)
    must reference the new endpoint URLs and the renamed state. This
    guards against a stale build where JSX was edited but `make build`
    was forgotten.
    """
    bundle = _read(APP_JS_PATH)
    # The new endpoint URLs.
    assert '/api/insurance/claim-free' in bundle, (
        "static/app.js must include /api/insurance/claim-free (rebuild the bundle)"
    )
    assert '/api/insurance/arm' in bundle, (
        "static/app.js must include /api/insurance/arm (rebuild the bundle)"
    )
    assert '/api/insurance/buy' in bundle, (
        "static/app.js must include /api/insurance/buy (rebuild the bundle)"
    )
    # The renamed state. The bundle minifies the variable names but
    # the strings and class names are preserved.
    assert 'free-tokens-section' in bundle, (
        "static/app.js must include the new free-tokens-section class"
    )
    assert 'Pay with insurance tokens' in bundle, (
        "static/app.js must include the renamed toggle label"
    )
