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


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


class _StubUser:
    """Replaces flask_login.current_user for the duration of the test."""
    username = 'alice'
    id = 42


# Stubs must be registered BEFORE game.py is imported so the
# `from flask_login import current_user` binding picks up our user.
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
    advance_season=lambda c: None,
))
sys.modules.setdefault('security', _make_stub('security', require_json=lambda: None))


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


sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


# Load game.py after stubs are in place so its imports resolve.
_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)


# ── Capture post_system_message / post_dedup_system_message calls ───────────
_posted = []


def _fake_post_system_message(conn, message, message_type='system', event_kind=None):
    _posted.append({'message': message, 'event_kind': event_kind})


def _fake_post_dedup_system_message(
    conn, message, user_id, event_kind, *, message_type='system',
):
    _posted.append({'message': message, 'event_kind': event_kind, 'user_id': user_id})


_game.post_system_message = _fake_post_system_message
_game.post_dedup_system_message = _fake_post_dedup_system_message


# ── Fixtures ────────────────────────────────────────────────────────────────
def _base_gs(**overrides):
    """A game_state dict with all columns the tick() path reads."""
    now = dt.datetime(2024, 1, 1, tzinfo=timezone.utc)
    # last_spin_at one interval in the past so elapsed // AUTO_SPIN_INTERVAL_SECONDS = 1
    last_spin = now - dt.timedelta(seconds=4)
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
        'auto_spin_since': now, 'last_spin_at': last_spin,
        'active_tab_id': 1, 'tab_last_seen': now,
        'auto_fish_enabled': False, 'auto_fish_last_tick': None,
        'prestige_level': 0, 'prestige_count': 0, 'legacy_wins': 0,
        'onboarding_step': 1,  # skip first-spin path
        'auto_spin_budget': 1,
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
    _game._load_game_state = fake_load_game_state

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
    _game._build_spin_context = fake_build_spin_context

    # _resolve_spin returns a fixed (new_state, events) pair.
    def fake_resolve_spin(**kwargs):
        return dict(_BASE_NEW_STATE), events
    _game._resolve_spin = fake_resolve_spin

    # Single shared conn; the cursor's fetchone queue feeds pot_row + rank_row
    # (gs is short-circuited by the _load_game_state patch above).
    pot_row = {'filled': False, 'filled_at': None, 'win_chance_pct': 50}
    rank_row = {'min_wins': None, 'active_count': 0}
    _shared_conn = _FakeConn(fetchone_queue=[pot_row, rank_row])
    _posted.clear()


# ── T90 acceptance criteria ────────────────────────────────────────────────

def test_tick_jackpot_posts_message():
    """T90.1/2: An auto-spin jackpot must post the jackpot chat message."""
    _posted.clear()
    gs = _base_gs()
    events = _make_events(result='jackpot', wins_delta=12345, mode='mirror')
    _install_fakes(gs, events)

    _game.tick()

    jackpots = [m for m in _posted if m['event_kind'] == 'jackpot']
    assert len(jackpots) == 1, f"Expected 1 jackpot message, got: {_posted}"
    msg = jackpots[0]['message']
    assert 'alice' in msg
    assert 'JACKPOT' in msg
    assert 'mirror' in msg
    assert '12345' in msg


def test_tick_big_win_posts_message_and_persists_value():
    """T90.3: An auto-spin big win must post the big-win chat message and
    persist biggest_win_announced in the final UPDATE so the threshold
    escalates across the loop and across ticks."""
    _posted.clear()
    gs = _base_gs(biggest_win_announced=0)
    events = _make_events(result='win', wins_delta=6000)
    _install_fakes(gs, events)

    _game.tick()

    big_wins = [m for m in _posted if m['event_kind'] == 'big_win']
    assert len(big_wins) == 1, f"Expected 1 big_win message, got: {_posted}"
    assert 'alice' in big_wins[0]['message']
    assert '6000' in big_wins[0]['message']

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


def test_tick_hot_streak_10_posts_message():
    """T90.4: An auto-spin hot-streak-10 must post the hot-streak message."""
    _posted.clear()
    gs = _base_gs()
    events = _make_events(result='win', wins_delta=10, wager_streak=10)
    _install_fakes(gs, events)

    _game.tick()

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

    _game.tick()

    big_wins = [m for m in _posted if m['event_kind'] == 'big_win']
    assert big_wins == [], f"Did not expect big_win, got: {_posted}"
