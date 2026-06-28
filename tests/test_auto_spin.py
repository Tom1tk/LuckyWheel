"""T90: Auto-post messages to auto-spin path (B5) tests.

The /api/tick endpoint must post jackpot, big-win, and hot-streak messages
when the corresponding events happen in the auto-spin loop, and persist
biggest_win_announced so the threshold escalates correctly across ticks.
"""
import os
import sys
import types
import importlib.util
import datetime as dt
from contextlib import contextmanager
from datetime import timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Stub install/teardown (T231) ────────────────────────────────────────────
# The stub `flask` / `flask_login` / `psycopg2` / `extensions` / `seasons` /
# `security` / `db` modules were previously installed at module-import time.
# That leaked the stubs into other test files collected in the same pytest
# process (e.g. tests/test_mobile_e2e.py — `module 'psycopg2' has no
# attribute 'connect'`). The fix: install the stubs only during this
# module's tests (via setup_module) and restore whatever was in sys.modules
# before in teardown_module, so other test files see the real modules.
#
# We do NOT use setdefault semantics: another test file in the same
# invocation (e.g. tests/test_auto_spin_visibility.py) installs its own
# `db` stub at module-import time and, if we used setdefault, our
# `game.py` reload would resolve `from db import db_connection` to *that*
# file's `_fake_db_connection` — meaning our tests would feed the cursor
# log into the *other* test file's `_shared_conn`, not our own, and the
# test assertions on `_shared_conn.log` would all be empty. We must
# override whatever is in sys.modules for the duration of the test run
# and restore it in teardown so the rest of the suite is unaffected.
_SENTINEL = object()
_STUB_PREV = {}  # name -> previous sys.modules entry (or _SENTINEL)
_GAME = None     # the loaded game.py module, set in setup_module
_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
_GAME_PATH = os.path.join(_REPO_ROOT, 'game.py')


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


def _noop(*a, **kw):
    def _inner(f):
        return f
    return _inner


class _UserMixinStub:
    pass


class _StubUser:
    """Replaces flask_login.current_user for the duration of the test."""
    username = 'alice'
    id = 42


# ── Fake DB plumbing ────────────────────────────────────────────────────────
class _FakeCursor:
    def __init__(self, fetchone_queue=None, log=None):
        self._fetchone_queue = fetchone_queue if fetchone_queue is not None else []
        self.log = log if log is not None else []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        # Log (op_first_word, full_sql, params) so tests can introspect
        # both the SQL string and the bound parameters.
        self.log.append((sql.strip().split()[0], sql, params))

    def fetchone(self):
        if not self._fetchone_queue:
            return None
        return self._fetchone_queue.pop(0)

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, fetchone_queue=None, log=None):
        self.log = log if log is not None else []
        self._fetchone_queue = fetchone_queue if fetchone_queue is not None else []

    def cursor(self, cursor_factory=None):
        # All cursors share the same fetchone queue so a single _FakeConn
        # backs the whole tick() transaction.
        return _FakeCursor(fetchone_queue=self._fetchone_queue, log=self.log)

    def commit(self):
        pass


# Single shared conn across `with db_connection() as conn:` blocks in tick().
_shared_conn = None


@contextmanager
def _fake_db_connection():
    yield _shared_conn


# ── Capture post_system_message / post_dedup_system_message calls ───────────
_posted = []


def _fake_post_system_message(conn, message, message_type='system', event_kind=None):
    _posted.append({'message': message, 'event_kind': event_kind})


def _fake_post_dedup_system_message(
    conn, message, user_id, event_kind, *, message_type='system',
):
    _posted.append({'message': message, 'event_kind': event_kind, 'user_id': user_id})


def _stub_specs():
    """Return (name, factory) pairs for every module the auto-spin tests stub.

    Factories are called only when a name is not already in sys.modules, so
    we don't churn work for names that another test file has already loaded
    (and that we will therefore leave alone).
    """
    psycopg2_extras_stub = _make_stub(
        'psycopg2.extras', RealDictCursor=type('RealDictCursor', (), {}))
    return [
        ('flask', lambda: _make_stub(
            'flask',
            Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
            jsonify=lambda x: x,
            request=None,
        )),
        ('flask_login', lambda: _make_stub(
            'flask_login',
            current_user=_StubUser(),
            login_required=lambda f: f,
            UserMixin=_UserMixinStub,
        )),
        ('psycopg2', lambda: _make_stub('psycopg2', extras=psycopg2_extras_stub)),
        ('psycopg2.extras', lambda: psycopg2_extras_stub),
        ('extensions', lambda: _make_stub(
            'extensions',
            limiter=types.SimpleNamespace(limit=_noop),
            csrf=types.SimpleNamespace(exempt=lambda f: f),
        )),
        ('seasons', lambda: _make_stub('seasons',
            ensure_current_season=lambda c: None,
            get_season_info=lambda c: {},
            get_latest_winners=lambda c, n: [],
            advance_season=lambda c: None,
        )),
        ('security', lambda: _make_stub('security', require_json=lambda: None)),
        ('db', lambda: _make_stub('db', db_connection=_fake_db_connection)),
    ]


def setup_module(module):
    """Install stubs and load game.py once before any test in this module.

    Runs after pytest has finished collecting all test files in this
    invocation, so sys.modules may already contain another test file's
    stubs (e.g. tests/test_auto_spin_visibility.py installs a `db` stub
    at import time). We override whatever is there for the duration of
    this module's tests, remembering the previous entry so teardown
    can restore it.
    """
    global _GAME
    for name, factory in _stub_specs():
        _STUB_PREV[name] = sys.modules.get(name, _SENTINEL)
        sys.modules[name] = factory()

    # Force-reload game.py from source under the now-stubbed environment
    # so its `from flask_login import current_user` etc. bindings pick up
    # OUR stubs (not another test file's).
    sys.modules.pop('game', None)
    spec = importlib.util.spec_from_file_location('game', _GAME_PATH)
    _GAME = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_GAME)

    _GAME.post_system_message = _fake_post_system_message
    _GAME.post_dedup_system_message = _fake_post_dedup_system_message


def teardown_module(module):
    """Restore sys.modules and drop the stub-loaded game so the next test
    file (e.g. tests/test_mobile_e2e.py) sees real modules and a fresh
    `game` (or no `game` at all, if nothing else loads it)."""
    global _GAME
    sys.modules.pop('game', None)
    _GAME = None
    for name, prev in _STUB_PREV.items():
        if prev is _SENTINEL:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prev
    _STUB_PREV.clear()


# ── Fixtures ────────────────────────────────────────────────────────────────
def _base_gs(**overrides):
    """A game_state dict with all columns the tick() path reads."""
    # T216: use the current wall-clock time as the reference so the
    # heartbeat auto-stop in /api/tick (which compares `last_spin_at`
    # against the handler's now_utc with a 60s threshold) treats the
    # session as fresh. A static 2024-01-01 timestamp would now look
    # years-stale and the heartbeat would auto-stop before the test
    # can run its assertions.
    now = dt.datetime.now(timezone.utc)
    # Stage the session so exactly 1 spin is due and the heartbeat
    # doesn't fire:
    #   cursor   = max(auto_spin_since, last_spin_at) = auto_spin_since
    #   elapsed  = now_utc - cursor ≈ 5s  ->  spins_due = 1
    #   stale    = now_utc - last_spin_at ≈ 9s  < 60s  ->  no heartbeat
    last_spin = now - dt.timedelta(seconds=9)
    g = {
        'wins': 0, 'losses': 0, 'streak': 0, 'best_streak': 0,
        'owned_items': [], 'regen_recharge_wins': 0,
        'spin_count': 0, 'win_count': 0, 'loss_count': 0,
        'winmult_inf_level': 0, 'bonusmult_inf_level': 0,
        'streak_armor_level': 0, 'jackpot_resonance_level': 0,
        'echo_amp_level': 0, 'proc_streak_level': 0, 'proc_streak': 0,
        'lure_mastery_level': 0, 'equipped_class': None,
        'fish_clicks': 0, 'caught_species': [], 'active_cosmetics': [],
        'dice_charges': 1, 'dice_last_recharge': last_spin,
        'jackpot_echo_next': False, 'dice_rolled_since_spin': False,
        'pending_dice': None,
        'auto_spin_since': now - dt.timedelta(seconds=5),
        'last_spin_at':    last_spin,
        'active_tab_id': 1, 'tab_last_seen': now,
        'auto_fish_enabled': False, 'auto_fish_last_tick': None,
        'prestige_level': 0, 'prestige_count': 0, 'legacy_wins': 0,
        'onboarding_step': 1,  # skip first-spin path
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
    """Build an events dict that satisfies _events_to_response()."""
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


def _install_fakes(gs, events):
    """Install gs/events mocks and reset per-test state."""
    global _shared_conn

    # _load_game_state is patched so the cursor's fetchone queue is *not*
    # consumed for the gs row; the queue only feeds pot_row and rank_row.
    def fake_load_game_state(cur, user_id, *, for_update=False):
        return gs
    _GAME._load_game_state = fake_load_game_state

    # _build_spin_context isn't on the hot path for these tests — return
    # a minimal valid context with the keys _resolve_spin() reads.
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
    _GAME._build_spin_context = fake_build_spin_context

    # _resolve_spin returns a fixed (new_state, events) pair.
    def fake_resolve_spin(**kwargs):
        return dict(_BASE_NEW_STATE), events
    _GAME._resolve_spin = fake_resolve_spin

    # Single shared conn; the cursor's fetchone queue feeds pot_row + rank_row
    # (gs is short-circuited by the _load_game_state patch above).
    pot_row = {'filled': False, 'filled_at': None, 'win_chance_pct': 50}
    rank_row = {'min_wins': None, 'active_count': 0}
    _shared_conn = _FakeConn(fetchone_queue=[pot_row, rank_row])
    _posted.clear()


# ── T90 acceptance criteria ────────────────────────────────────────────────

def test_tick_jackpot_posts_no_message():
    """T221: jackpot spins no longer post a chat message. Neither the
    old "JACKPOT in M mode at Nx stake" format, the was_jackpot big_win
    format, nor any other event_kind is posted. The win is still
    tallied in wins; only the chat announcement is suppressed."""
    _posted.clear()
    gs = _base_gs()
    events = _make_events(result='jackpot', wins_delta=12345, mode='mirror')
    _install_fakes(gs, events)

    _GAME.tick()

    assert _posted == [], (
        f"T221: jackpot spins must not post any chat message. Got: {_posted}"
    )


def test_tick_big_win_posts_message_and_persists_value():
    """T90.3: An auto-spin big win must post the big-win chat message and
    persist biggest_win_announced in the final UPDATE so the threshold
    escalates across the loop and across ticks."""
    from format_wins import format_wins
    _posted.clear()
    gs = _base_gs(biggest_win_announced=0)
    events = _make_events(result='win', wins_delta=6000)
    _install_fakes(gs, events)

    _GAME.tick()

    big_wins = [m for m in _posted if m['event_kind'] == 'big_win']
    assert len(big_wins) == 1, f"Expected 1 big_win message, got: {_posted}"
    assert 'alice' in big_wins[0]['message']
    assert format_wins(6000) in big_wins[0]['message']

    # The final UPDATE must persist biggest_win_announced = 6000 so a second
    # tick (or a later spin in this loop) can detect the escalation.
    final_updates = [
        (sql, params) for op, sql, params in _shared_conn.log
        if op == 'UPDATE' and 'biggest_win_announced = %s' in sql
        and 'WHERE user_id = %s' in sql
    ]
    assert final_updates, (
        "Expected the final UPDATE to include 'biggest_win_announced = %s' "
        "(T90 acceptance criterion #3)"
    )
    assert any(6000 in params for _, params in final_updates), (
        f"biggest_win_announced=6000 not in UPDATE params: {final_updates}"
    )


def test_tick_double_down_path_does_not_post_big_win():
    """T230 + auto-spin note: the auto-spin path uses stake_pct=0 and
    never posts a double-down chat message. The duplication the T230
    fix targets only arises in the manual /api/spin path (where the
    spin handler can read the player's stake). This test pins the
    auto-spin behavior: a big win in the auto-spin path still posts
    exactly one big_win message, unaffected by the new skip_message
    plumbing."""
    from format_wins import format_wins
    _posted.clear()
    gs = _base_gs(biggest_win_announced=0)
    # double_down_pending doesn't trigger anything in the auto-spin loop
    # (stake_pct=0, no wager). Set it to confirm it doesn't matter.
    gs['double_down_pending'] = True
    events = _make_events(
        result='win', wins_delta=12000, mode='steady', wager_streak=0,
    )
    _install_fakes(gs, events)

    _GAME.tick()

    big_wins = [m for m in _posted if m['event_kind'] == 'big_win']
    assert len(big_wins) == 1, f"Expected 1 big_win, got: {_posted}"
    assert format_wins(12000) in big_wins[0]['message']
    dd = [m for m in _posted if m['event_kind'] == 'double_down_win']
    assert dd == [], (
        f"Auto-spin path must not post a double_down_win message "
        f"(it uses stake_pct=0). Got: {dd}"
    )


def test_tick_hot_streak_10_posts_message():
    """T90.4: An auto-spin hot-streak-10 must post the hot-streak message."""
    _posted.clear()
    gs = _base_gs()
    events = _make_events(result='win', wins_delta=10, wager_streak=10)
    _install_fakes(gs, events)

    _GAME.tick()

    streaks = [m for m in _posted if m['event_kind'] == 'hot_streak']
    assert len(streaks) == 1, f"Expected 1 hot_streak message, got: {_posted}"
    assert 'alice' in streaks[0]['message']


def test_tick_big_win_does_not_fire_below_previous_biggest():
    """T83 escalation: a big win that doesn't strictly exceed the previous
    biggest must not re-announce. Verifies the new_auto-spin path threads the
    updated biggest_win_announced through the loop, not just the gs snapshot."""
    _posted.clear()
    gs = _base_gs(biggest_win_announced=10000)
    events = _make_events(result='win', wins_delta=7500)
    _install_fakes(gs, events)

    _GAME.tick()

    big_wins = [m for m in _posted if m['event_kind'] == 'big_win']
    assert big_wins == [], f"Did not expect big_win, got: {_posted}"
