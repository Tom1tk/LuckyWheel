"""T216: Auto-spin visibility / safety tests.

Covers the three T216 acceptance criteria that can be verified
in-process with stubs:

  1. No resume on page load — if the server says `auto_spin_active: true`
     on a fresh state fetch, the client-side handler must clear local
     state AND call /api/auto-spin/stop so the server's `auto_spin_since`
     becomes NULL.
  2. Stale session auto-stop — a /api/tick that arrives >60s after the
     last `last_spin_at` must return `auto_spin_active: false,
     auto_spin_stopped: 'stale'` and clear the server's `auto_spin_since`.
  3. Fresh session keeps running — a /api/tick that arrives within the
     60s window must process spins normally and leave `auto_spin_active`
     true.
  4. The `auto_spin_budget` column must not exist after migration 057.

The Playwright e2e variants (toast on resume prevention, no `.autospin-
budget` DOM element) are documented but not implemented here — they're
covered by the existing `test_mobile_*` suite on the staging server.
"""
import importlib.util
import os
import re
import sys
import types
import datetime as dt
from contextlib import contextmanager
from datetime import timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Module stubs (mirror test_auto_spin.py) ─────────────────────────────────

def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _StubUser:
    """Replacement for flask_login.current_user. id/username are unused
    by these tests but kept stable for the exception-path log lines."""
    id = 42
    username = 'alice'


class _UserMixinStub:
    pass


_psycopg2_extras_stub = _make_stub(
    'psycopg2.extras', RealDictCursor=type('RealDictCursor', (), {}))
_psycopg2_stub = _make_stub('psycopg2', extras=_psycopg2_extras_stub)

sys.modules.setdefault('flask', _make_stub(
    'flask',
    Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
    jsonify=lambda x: x,
    request=None,
))
sys.modules.setdefault('flask_login', _make_stub(
    'flask_login',
    current_user=_StubUser(),
    login_required=lambda f: f,
    UserMixin=_UserMixinStub,
))
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


# ── Fake DB plumbing ────────────────────────────────────────────────────────

class _FakeCursor:
    """Records every SQL + bound params, returns canned rows on fetchone.

    Tracks updates to `auto_spin_since` in a separate state dict so tests
    can assert the post-tick state of the `game_state` row."""

    def __init__(self, initial_gs, log=None, state=None):
        self._initial_gs = initial_gs
        # _load_game_state is patched in _install_fakes, so the cursor's
        # fetchone queue only needs to feed the `SELECT … FROM community_pot`
        # call made inside /api/tick. (See test_auto_spin.py:264-268 for the
        # equivalent setup.)
        pot_row = {'filled': False, 'filled_at': None, 'win_chance_pct': 50}
        self._fetchone_queue = [pot_row]
        self.log = log if log is not None else []
        # Mirror of the mutable columns: auto_spin_since, last_spin_at.
        # This is what /api/tick would have written.
        self.state = state if state is not None else {
            'auto_spin_since': initial_gs.get('auto_spin_since'),
            'last_spin_at':    initial_gs.get('last_spin_at'),
        }

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql.strip().split()[0], sql, params))
        s = sql.strip()
        s_lower = s.lower()

        # /api/tick heartbeat auto-stop: UPDATE game_state SET auto_spin_since = NULL
        if (s_lower.startswith('update')
                and 'auto_spin_since' in s_lower
                and '= null' in s_lower
                and 'where user_id' in s_lower):
            self.state['auto_spin_since'] = None

        # /api/tick final UPDATE: captures `last_spin_at = %s` from params
        if (s_lower.startswith('update')
                and 'last_spin_at = %s' in s_lower
                and 'where user_id' in s_lower
                and params):
            # `last_spin_at` is the 2nd-to-last param (auto_spin_budget is
            # gone in T216). The cursor's execute log is the only place
            # we can find it — the bind order is the source of truth.
            # The schema: (..., last_spin_at, user_id)
            self.state['last_spin_at'] = params[-2]

        # /api/auto-spin/start: UPDATE game_state SET auto_spin_since = NOW()
        if (s_lower.startswith('update')
                and 'auto_spin_since = now()' in s_lower
                and 'where user_id' in s_lower):
            self.state['auto_spin_since'] = dt.datetime.now(timezone.utc)

        # /api/auto-spin/stop: UPDATE game_state SET auto_spin_since = NULL
        # (already covered above; also fires for /api/auto-spin/stop)

    def fetchone(self):
        if not self._fetchone_queue:
            return None
        return self._fetchone_queue.pop(0)

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, initial_gs, log=None, state=None):
        self._cur = _FakeCursor(initial_gs, log=log, state=state)
        self.log = self._cur.log

    def cursor(self, cursor_factory=None):
        return self._cur

    def commit(self):
        pass


_shared_conn = None


@contextmanager
def _fake_db_connection():
    yield _shared_conn


# Force-override (not setdefault) so this test file's `db_connection` stub
# wins when other test files in the same suite (e.g. test_auto_spin.py)
# have already registered their own `db` stub. Without this, tick() calls
# go to the FIRST-installed stub (test_auto_spin.py's) and our
# _shared_conn here is never used, which causes tests like
# test_fresh_session_keeps_running to fail with an empty SQL log.
sys.modules['db'] = _make_stub('db', db_connection=_fake_db_connection)


# ── Load game.py after stubs ────────────────────────────────────────────────
_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)


# ── Fixtures ────────────────────────────────────────────────────────────────

def _base_gs(*, auto_spin_since, last_spin_at, **overrides):
    """A game_state dict with all columns the tick() path reads."""
    g = {
        'wins': 0, 'losses': 0, 'streak': 0, 'best_streak': 0,
        'owned_items': ['auto_spin_unlock'], 'regen_recharge_wins': 0,
        'spin_count': 0, 'win_count': 0, 'loss_count': 0,
        'winmult_inf_level': 0, 'bonusmult_inf_level': 0,
        'streak_armor_level': 0, 'jackpot_resonance_level': 0,
        'echo_amp_level': 0, 'proc_streak_level': 0, 'proc_streak': 0,
        'lure_mastery_level': 0, 'equipped_class': None,
        'fish_clicks': 0, 'caught_species': [], 'active_cosmetics': [],
        'dice_charges': 1, 'dice_last_recharge': dt.datetime(2024, 1, 1, tzinfo=timezone.utc),
        'jackpot_echo_next': False, 'dice_rolled_since_spin': False,
        'pending_dice': None,
        'auto_spin_since': auto_spin_since,
        'last_spin_at':    last_spin_at,
        'active_tab_id': 1, 'tab_last_seen': dt.datetime(2024, 1, 1, tzinfo=timezone.utc),
        'auto_fish_enabled': False, 'auto_fish_last_tick': None,
        'prestige_level': 0, 'prestige_count': 0, 'legacy_wins': 0,
        'onboarding_step': 1,
        'wager_streak': 0, 'wager_last_stake': 0,
        'double_down_pending': False, 'wager_banked_wins': 0,
        'insurance_charges': 0, 'insurance_armed': False,
        'active_wheel_mode': 'steady',
        'insurance_tokens': 0, 'aquarium_species': [], 'cosmetic_fragments': 0,
        'guard_charges': 0, 'guard_last_regen_spin': 0,
        'resilience_last_use_spin': 0, 'bounty_claimed_date': None,
        'biggest_win_announced': 0,
    }
    g.update(overrides)
    return g


_BASE_NEW_STATE = {
    'owned':              [],
    'streak':             0,
    'best_streak':        0,
    'regen_recharge_wins': 0,
    'wins':               0,
    'losses':             0,
    'jackpot_echo_next':  False,
    'active_cosmetics':   [],
    'proc_streak':        0,
}


def _make_events(result='win', wins_delta=0, mode='steady', wager_streak=0):
    return {
        'result':                    result,
        'wins_delta':                wins_delta,
        'losses_delta':              0,
        'streak':                    0,
        'owned_items':               [],
        'regen_recharge_wins':       0,
        'shield_used':               False,
        'shield_used_type':          None,
        'shield_broke':              False,
        'guard_triggered':           False,
        'guard_blocked':             False,
        'bonus_earned':              False,
        'echo_triggered':            False,
        'jackpot_hit':               result == 'jackpot',
        'jackpot_echo_triggered':    False,
        'jackpot_echo_next':         False,
        'resilience_triggered':      False,
        'lucky_seven_triggered':     False,
        'fortune_charm_triggered':   False,
        'active_cosmetics':          [],
        'auto_guard_failed':         False,
        'proc_streak':               0,
        'wager_streak':              wager_streak,
        'stake':                     1,
        'wager_banked_wins':         0,
        'wager_last_win_amount':     0,
        'double_down_active':        False,
        'insurance_used':            False,
        'active_wheel_mode':         mode,
        'segment_angle':             100.0,
    }


def _install_fakes(gs, events, *, now=None):
    """Install gs/events mocks and reset per-test state.

    `now` is the simulated current UTC time for the heartbeat
    staleness calculation. Defaults to the real wall-clock time so
    callers can express a `last_spin_at` in terms of "real now minus N
    seconds". A `now` arg that's not real wall-clock lets tests
    force a specific staleness window.

    NOTE: we do NOT monkey-patch `dt.datetime.now()` — that would
    leak into subsequent test files (e.g. test_auto_spin.py) and
    break their timestamp-relative assertions. Instead, we use the
    real clock and stage gs columns with a relative offset."""
    global _shared_conn
    if now is None:
        now = dt.datetime.now(timezone.utc)
    _game._now_override = now

    def fake_load_game_state(cur, user_id, *, for_update=False):
        return gs
    _game._load_game_state = fake_load_game_state

    def fake_build_spin_context(g):
        return {
            'effective_win_mult': 1.0,
            'bonus_mult':         1.0,
            'jackpot_chance':     0.01,
            'echo_chance':        0.05,
            'charm_chance':       0.05,
            'resilience_chance':  0.05,
            'proc_streak_level':  0,
            'aquarium_luck':      0.0,
        }
    _game._build_spin_context = fake_build_spin_context

    def fake_resolve_spin(**kwargs):
        return dict(_BASE_NEW_STATE), events
    _game._resolve_spin = fake_resolve_spin

    # Single shared conn; the cursor's fetchone queue feeds the
    # `SELECT … FROM community_pot` call. (See test_auto_spin.py:264-268
    # for the equivalent setup — _load_game_state is patched so the gs
    # row doesn't come from the queue.)
    _shared_conn = _FakeConn(initial_gs=gs)
    return _shared_conn


# ── Source-level guard: game.py must not reference `auto_spin_budget` ───────

def test_game_py_does_not_reference_auto_spin_budget():
    """T216: the `auto_spin_budget` column was dropped. game.py must
    contain no SQL or business-logic reference to it (comments
    explaining the removal are fine)."""
    game_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')
    with open(game_path) as f:
        src = f.read()
    # Strip comment lines so the explanatory T216 comments are allowed.
    code_lines = [
        line for line in src.splitlines()
        if line.strip() and not line.strip().startswith('#')
    ]
    code_only = '\n'.join(code_lines)
    assert 'auto_spin_budget' not in code_only, (
        "game.py code still references auto_spin_budget after the column "
        "was dropped (migration 057). The reference must be removed from "
        "all SQL, dict keys, and conditional logic. Comments are fine."
    )


def test_migration_057_exists():
    """The drop-column migration must be present at the canonical name."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'migrations', '057_drop_auto_spin_budget.sql',
    )
    assert os.path.exists(path), f"missing migration: {path}"
    with open(path) as f:
        sql = f.read()
    assert re.search(
        r'ALTER\s+TABLE\s+game_state\s+DROP\s+COLUMN\s+IF\s+EXISTS\s+auto_spin_budget',
        sql, re.IGNORECASE,
    ), (
        f"migration 057 must contain `ALTER TABLE game_state DROP COLUMN "
        f"IF EXISTS auto_spin_budget` — got:\n{sql}"
    )


# ── Source-level guard: heartbeat threshold = 60s ────────────────────────────

def test_tick_heartbeat_threshold_is_60_seconds():
    """T216: the heartbeat auto-stop must fire after 60s of no /api/tick.
    The literal `60` (or a named constant) must appear in /api/tick's
    stale-detection branch, with a comment naming T216."""
    game_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')
    with open(game_path) as f:
        src = f.read()
    # Locate /api/tick endpoint body
    tick_block = re.search(
        r"@game_bp\.route\('/api/tick'.*?(?=\n@game_bp\.route\()",
        src, re.DOTALL,
    )
    assert tick_block, "could not locate /api/tick endpoint body in game.py"
    body = tick_block.group(0)
    # The stale-check must compare against 60 (literal or named constant).
    assert re.search(r'>\s*60\b', body), (
        "/api/tick must include a `> 60` (or named constant) stale threshold"
    )
    # The block must mention T216 so the magic number is traceable.
    assert 'T216' in body, (
        "/api/tick stale-check must reference ticket T216 in a comment"
    )
    # The block must also explain WHY 60s was chosen.
    assert re.search(r'60s', body), (
        "/api/tick stale-check must include a comment explaining the 60s choice"
    )


# ── /api/state: auto_spin_active is derived from auto_spin_since alone ───────

def test_state_does_not_reference_auto_spin_budget():
    """T216: /api/state's `auto_spin_active` field is now derived from
    `auto_spin_since` alone — no `auto_spin_budget` reference."""
    game_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')
    with open(game_path) as f:
        src = f.read()
    state_block = re.search(
        r"@game_bp\.route\('/api/state'.*?(?=\n@game_bp\.route\()",
        src, re.DOTALL,
    )
    assert state_block, "could not locate /api/state endpoint body in game.py"
    body = state_block.group(0)
    code_lines = [
        line for line in body.splitlines()
        if line.strip() and not line.strip().startswith('#')
    ]
    code_only = '\n'.join(code_lines)
    assert 'auto_spin_budget' not in code_only, (
        "/api/state code still references auto_spin_budget — it should be "
        "dropped from the response per T216."
    )


# ── /api/auto-spin/start: no budget request parsing ─────────────────────────

def test_start_endpoint_does_not_read_budget_from_request():
    """T216: /api/auto-spin/start must not parse a `budget` field from
    the request body. Auto-spin is now binary on/off."""
    game_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')
    with open(game_path) as f:
        src = f.read()
    start_block = re.search(
        r"@game_bp\.route\('/api/auto-spin/start'.*?(?=\n@game_bp\.route\()",
        src, re.DOTALL,
    )
    assert start_block, "could not locate /api/auto-spin/start endpoint body"
    body = start_block.group(0)
    assert "request.json" not in body or "budget" not in body, (
        "/api/auto-spin/start still reads the `budget` field from the "
        "request body — T216 requires the per-activation budget to be "
        "dropped entirely."
    )
    # The endpoint must set auto_spin_since = NOW() (no budget column).
    assert re.search(r'auto_spin_since\s*=\s*NOW\(\)', body, re.IGNORECASE), (
        "/api/auto-spin/start must set `auto_spin_since = NOW()` (without "
        "touching the dropped auto_spin_budget column)."
    )


# ── /api/auto-spin/stop: SQL must not reference the dropped column ──────────

def test_stop_endpoint_sql_drops_auto_spin_budget():
    """T216: /api/auto-spin/stop's UPDATE must set only auto_spin_since.
    Touching the dropped auto_spin_budget column would crash with
    `column "auto_spin_budget" does not exist`."""
    game_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')
    with open(game_path) as f:
        src = f.read()
    stop_block = re.search(
        r"@game_bp\.route\('/api/auto-spin/stop'.*?(?=\n@game_bp\.route\()",
        src, re.DOTALL,
    )
    assert stop_block, "could not locate /api/auto-spin/stop endpoint body"
    body = stop_block.group(0)
    code_lines = [
        line for line in body.splitlines()
        if line.strip() and not line.strip().startswith('#')
    ]
    code_only = '\n'.join(code_lines)
    assert 'auto_spin_budget' not in code_only, (
        "/api/auto-spin/stop code still references auto_spin_budget — "
        "the column was dropped (migration 057) and any UPDATE touching "
        "it would fail at runtime."
    )


# ── /api/tick: heartbeat auto-stop behavior ────────────────────────────────

def test_stale_session_auto_stopped():
    """T216: when a /api/tick arrives >60s after `last_spin_at`, the
    handler must auto-stop auto-spin, set `auto_spin_since = NULL`, and
    return `auto_spin_active: false, auto_spin_stopped: 'stale'`."""
    now = dt.datetime.now(timezone.utc)
    last_spin = now - dt.timedelta(seconds=90)
    gs = _base_gs(
        auto_spin_since=now - dt.timedelta(seconds=120),
        last_spin_at=last_spin,
    )
    events = _make_events()
    conn = _install_fakes(gs, events, now=now)

    response = _game.tick()
    response_payload = response.json if hasattr(response, 'json') else response

    # 1) Response must signal the auto-stop.
    assert response_payload.get('auto_spin_active') is False, (
        f"stale /api/tick must return auto_spin_active=False, got: {response_payload}"
    )
    assert response_payload.get('auto_spin_stopped') == 'stale', (
        f"stale /api/tick must return auto_spin_stopped='stale', got: "
        f"{response_payload}"
    )
    # No spins should be returned — the session is stopped, not advanced.
    assert response_payload.get('spins') == [], (
        f"stale /api/tick must not return spins, got: {response_payload}"
    )

    # 2) Server state must have auto_spin_since = NULL.
    assert conn._cur.state['auto_spin_since'] is None, (
        f"stale /api/tick must set auto_spin_since=NULL on the server; "
        f"state was: {conn._cur.state}"
    )

    # 3) The auto-stop UPDATE must appear in the SQL log.
    auto_stop_ups = [
        (sql, params) for op, sql, params in conn.log
        if op == 'UPDATE'
        and 'auto_spin_since = NULL' in sql
        and 'where user_id' in sql.lower()
    ]
    assert auto_stop_ups, (
        f"stale /api/tick must execute `UPDATE game_state SET "
        f"auto_spin_since = NULL`; got log: {[s for _, s, _ in conn.log]}"
    )


def test_fresh_session_keeps_running():
    """T216: a /api/tick that arrives within the 60s window (last_spin_at
    only 5s ago) must process spins normally and leave auto_spin_since
    set."""
    now = dt.datetime.now(timezone.utc)
    last_spin = now - dt.timedelta(seconds=5)
    gs = _base_gs(
        auto_spin_since=now - dt.timedelta(seconds=30),
        last_spin_at=last_spin,
    )
    events = _make_events(result='win', wins_delta=50)
    conn = _install_fakes(gs, events, now=now)

    response = _game.tick()
    response_payload = response.json if hasattr(response, 'json') else response

    # 1) The response must NOT signal a stop.
    assert response_payload.get('auto_spin_stopped') != 'stale', (
        f"fresh /api/tick must NOT auto-stop; got: {response_payload}"
    )
    # 2) auto_spin_since must still be set on the server (or at least
    #    the auto-stop UPDATE must not have fired).
    auto_stop_ups = [
        sql for op, sql, params in conn.log
        if op == 'UPDATE'
        and 'auto_spin_since = NULL' in sql
        and 'where user_id' in sql.lower()
    ]
    assert not auto_stop_ups, (
        f"fresh /api/tick must not auto-stop; auto-stop UPDATEs found: "
        f"{auto_stop_ups}"
    )

    # 3) The final tick UPDATE must NOT touch the dropped
    #    `auto_spin_budget` column (it would crash with `column does
    #    not exist`).
    final_ups = [
        sql for op, sql, params in conn.log
        if op == 'UPDATE'
        and 'last_spin_at = %s' in sql
        and 'where user_id' in sql.lower()
    ]
    assert final_ups, "expected a final /api/tick UPDATE in the SQL log"
    for sql in final_ups:
        assert 'auto_spin_budget' not in sql.lower(), (
            f"final /api/tick UPDATE still references auto_spin_budget; "
            f"the column was dropped. SQL: {sql}"
        )


def test_tick_no_session_returns_inactive():
    """T216: if `auto_spin_since` is NULL, /api/tick must return
    `auto_spin_active: false` without touching any spin state."""
    now = dt.datetime.now(timezone.utc)
    gs = _base_gs(auto_spin_since=None, last_spin_at=None)
    events = _make_events()
    conn = _install_fakes(gs, events, now=now)

    response = _game.tick()
    response_payload = response.json if hasattr(response, 'json') else response

    assert response_payload.get('auto_spin_active') is False
    assert response_payload.get('spins') == []
    # The heartbeat UPDATE must not fire when there's no session.
    auto_stop_ups = [
        sql for op, sql, params in conn.log
        if op == 'UPDATE'
        and 'auto_spin_since = NULL' in sql
        and 'where user_id' in sql.lower()
    ]
    assert not auto_stop_ups, (
        f"/api/tick with no auto-spin must not run the heartbeat UPDATE; "
        f"got: {auto_stop_ups}"
    )


# ── Static / app.jsx guards ────────────────────────────────────────────────

def test_app_jsx_does_not_reference_auto_spin_budget():
    """T216: the client must not read or set `autoSpinBudget` /
    `auto_spin_budget` anywhere. The state declaration, the
    setAutoSpinBudget() calls, and the start-POST body must all be
    gone."""
    app_jsx_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )
    with open(app_jsx_path) as f:
        src = f.read()
    assert 'autoSpinBudget' not in src, (
        "static/app.jsx still references `autoSpinBudget` — the T216 "
        "removal of the per-activation budget requires this state and "
        "all its setX() calls to be gone."
    )
    assert 'auto_spin_budget' not in src, (
        "static/app.jsx still references `auto_spin_budget` — the "
        "server-side column is gone (migration 057); the client must "
        "stop reading and posting the field."
    )


def test_app_jsx_start_body_does_not_send_budget():
    """T216: the handleStartAutoSpin body must be `{}` (no `budget: 100`)."""
    app_jsx_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )
    with open(app_jsx_path) as f:
        src = f.read()
    m = re.search(
        r"handleStartAutoSpin\s*=\s*useCallback\(async\s*\(\)\s*=>\s*\{(.+?)\}",
        src, re.DOTALL,
    )
    assert m, "could not locate handleStartAutoSpin body"
    body = m.group(1)
    assert "budget" not in body, (
        f"handleStartAutoSpin body still references `budget`; T216 "
        f"requires the per-activation budget to be removed from the "
        f"start POST. body:\n{body}"
    )


def test_app_jsx_shop_desc_dropped_100_spins_wording():
    """T216: the `auto_spin_unlock` shop desc must not claim "100 spins
    per activation" — that text is a stale description of the dropped
    budget."""
    app_jsx_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )
    with open(app_jsx_path) as f:
        src = f.read()
    assert '100 spins per activation' not in src, (
        "the `auto_spin_unlock` shop desc still says `100 spins per "
        "activation` — the per-activation budget was dropped in T216."
    )


def test_app_jsx_resume_prevention_toast_present():
    """T216: the state-sync useEffect must include the resume-prevention
    block — when the server reports `auto_spin_active: true` on a fresh
    page load, the client must call /api/auto-spin/stop and show a
    toast telling the player to click the checkbox to restart."""
    app_jsx_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )
    with open(app_jsx_path) as f:
        src = f.read()
    # The toast string must appear.
    assert "Auto-spin was running on the server" in src, (
        "static/app.jsx must include the resume-prevention toast "
        "string. See T216 acceptance criterion #3."
    )
    # The block must call /api/auto-spin/stop on a true active response.
    assert re.search(
        r"if\s*\(\s*gameState\.auto_spin_active\s*===\s*true\s*\).+?"
        r"apiGame\('/api/auto-spin/stop'",
        src, re.DOTALL,
    ), (
        "static/app.jsx must call /api/auto-spin/stop from the "
        "resume-prevention block when the server reports "
        "auto_spin_active=true."
    )
