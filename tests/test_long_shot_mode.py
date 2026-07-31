"""Tests for T115: "Long Shot" wheel mode.

T115 ACs covered:
  1. WHEEL_MODES['long_shot'] has the spec values (20/60/20, multiplier 10,
     exact description).
  2. _ROTATING_MODES is ['inverted', 'gravity', 'long_shot'].
  3. get_rotating_mode(week_number=2) returns 'long_shot' (slot 2 of the
     weekly rotation).
  4. Probabilities sum to 100 and a 10,000-spin sample in long_shot mode
     resolves within ±3% of the expected 20/60/20 distribution.
"""
import os
import sys
import types
import importlib.util
import random
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Stub install/teardown (T242) ────────────────────────────────────────────
_SENTINEL = object()
_STUB_PREV = {}
_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
_GAME_PATH = os.path.join(_REPO_ROOT, 'game.py')
_WHEEL_MODES_PATH = os.path.join(_REPO_ROOT, 'wheel_modes.py')
_game = None
_wheel_modes = None
_resolve_spin = None
WHEEL_MODES = None  # set in setup_module
_ROTATING_MODES = None
get_rotating_mode = None
get_available_modes = None


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


def _stub_specs():
    """Return (name, factory) pairs for every module this test stubs."""
    _psycopg2_extras_stub = _make_stub(
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
            current_user=None,
            login_required=lambda f: f,
            UserMixin=_UserMixinStub,
        )),
        ('psycopg2', lambda: _make_stub('psycopg2', extras=_psycopg2_extras_stub)),
        ('psycopg2.extras', lambda: _psycopg2_extras_stub),
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
    ]


class _FakeCursor:
    def __init__(self, log=None, fetchone_queue=None):
        self.log = log if log is not None else []
        self._fetchone_queue = fetchone_queue or []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql, params))

    def fetchone(self):
        if not self._fetchone_queue:
            return None
        return self._fetchone_queue.pop(0)

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, fetchone_queue=None):
        self.log = []
        self._fetchone_queue = fetchone_queue or []
        self._cursors = [_FakeCursor(self.log, self._fetchone_queue)]

    def cursor(self, cursor_factory=None):
        return self._cursors[0]

    def commit(self):
        pass


@contextmanager
def _fake_db_connection():
    conn = _FakeConn()
    yield conn


def setup_module(module):
    """Install stubs and load wheel_modes.py + game.py once before any
    test in this module."""
    global _game, _wheel_modes, _resolve_spin, WHEEL_MODES
    global _ROTATING_MODES, get_rotating_mode, get_available_modes
    for name, factory in _stub_specs():
        _STUB_PREV[name] = sys.modules.get(name, _SENTINEL)
        sys.modules[name] = factory()
    _STUB_PREV['db'] = sys.modules.get('db', _SENTINEL)
    sys.modules['db'] = _make_stub('db', db_connection=_fake_db_connection)

    sys.modules.pop('wheel_modes', None)
    wheel_spec = importlib.util.spec_from_file_location('wheel_modes', _WHEEL_MODES_PATH)
    _wheel_modes = importlib.util.module_from_spec(wheel_spec)
    wheel_spec.loader.exec_module(_wheel_modes)

    sys.modules.pop('game', None)
    spec = importlib.util.spec_from_file_location('game', _GAME_PATH)
    _game = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_game)
    _resolve_spin = _game._resolve_spin

    WHEEL_MODES         = _wheel_modes.WHEEL_MODES
    _ROTATING_MODES     = _wheel_modes._ROTATING_MODES
    get_rotating_mode   = _wheel_modes.get_rotating_mode
    get_available_modes = _wheel_modes.get_available_modes


def teardown_module(module):
    """Restore sys.modules and drop the stub-loaded modules."""
    global _game, _wheel_modes, _resolve_spin, WHEEL_MODES
    global _ROTATING_MODES, get_rotating_mode, get_available_modes
    sys.modules.pop('game', None)
    sys.modules.pop('wheel_modes', None)
    _game = _wheel_modes = _resolve_spin = WHEEL_MODES = None
    _ROTATING_MODES = get_rotating_mode = get_available_modes = None
    for name, prev in _STUB_PREV.items():
        if prev is _SENTINEL:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prev
    _STUB_PREV.clear()


# ── Helpers ─────────────────────────────────────────────────────────────────
def _base_state(**overrides):
    state = dict(
        owned=[],
        streak=0,
        best_streak=0,
        regen_recharge_wins=0,
        wins=1000,
        losses=1000,
        jackpot_echo_next=False,
        spin_count=1,
        active_cosmetics=[],
        proc_streak=0,
    )
    state.update(overrides)
    return state


def _base_ctx(**overrides):
    ctx = dict(
        effective_win_mult=2.0,
        bonus_mult=1,
        jackpot_chance=0.0,
        echo_chance=0.0,
        charm_chance=0.0,
        resilience_chance=0.5,
        proc_streak_level=0,
        pot_active=False,
        pot_win_pct=0.505,
    )
    ctx.update(overrides)
    return ctx


# ════════════════════════════════════════════════════════════════════════════
# T115 AC#1: WHEEL_MODES['long_shot'] has the spec values
# ════════════════════════════════════════════════════════════════════════════
def test_long_shot_profile_matches_spec():
    """T115 AC#1: long_shot mode matches the operator-confirmed spec exactly.

    win_pct=20, loss_pct=60, jackpot_pct=20, jackpot_multiplier=10,
    description='Most spins lose. Jackpots hit often but pay less.'
    """
    assert 'long_shot' in WHEEL_MODES, (
        f"WHEEL_MODES must include 'long_shot'; keys: {sorted(WHEEL_MODES)}"
    )
    ls = WHEEL_MODES['long_shot']
    assert ls['win_pct']        == 20, f"win_pct should be 20, got {ls['win_pct']}"
    assert ls['loss_pct']       == 60, f"loss_pct should be 60, got {ls['loss_pct']}"
    assert ls['jackpot_pct']    == 20, f"jackpot_pct should be 20, got {ls['jackpot_pct']}"
    assert ls['jackpot_multiplier'] == 10, (
        f"jackpot_multiplier should be 10, got {ls['jackpot_multiplier']}"
    )
    assert ls['description'] == 'Most spins lose. Jackpots hit often but pay less.', (
        f"description mismatch: {ls['description']!r}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T115 AC#2: _ROTATING_MODES slot layout
# ════════════════════════════════════════════════════════════════════════════
def test_rotating_modes_replaces_mirror_with_long_shot():
    """T115 AC#2: weekly rotation is [inverted, gravity, long_shot].
    Mirror stays in WHEEL_MODES (T78 backend complete) but is removed from
    the rotation since the two-wheels frontend is deferred to 8.X.
    """
    assert _ROTATING_MODES == ['inverted', 'gravity', 'long_shot'], (
        f"expected ['inverted', 'gravity', 'long_shot'], got {_ROTATING_MODES}"
    )
    # Sanity: mirror is still defined as a mode (just not rotating).
    assert 'mirror' in WHEEL_MODES, "mirror mode entry must still exist in WHEEL_MODES"


# ════════════════════════════════════════════════════════════════════════════
# T115 AC#3: get_rotating_mode() slot 2
# ════════════════════════════════════════════════════════════════════════════
def test_get_rotating_mode_slot_2_returns_long_shot():
    """T115 AC#3: week_number % 3 == 2 → 'long_shot' (was 'mirror' pre-T115)."""
    assert get_rotating_mode(week_number=2) == 'long_shot', (
        f"week_number=2 should yield 'long_shot', got {get_rotating_mode(week_number=2)!r}"
    )
    # Cover all three slots to lock in the rotation order.
    assert get_rotating_mode(week_number=0) == 'inverted'
    assert get_rotating_mode(week_number=1) == 'gravity'
    assert get_rotating_mode(week_number=2) == 'long_shot'
    # And one full cycle later, the order is the same.
    assert get_rotating_mode(week_number=3) == 'inverted'
    assert get_rotating_mode(week_number=4) == 'gravity'
    assert get_rotating_mode(week_number=5) == 'long_shot'


def test_get_available_modes_includes_long_shot_in_slot_2():
    """T115 AC#2/#3: get_available_modes() exposes long_shot on slot-2 weeks
    (steady + volatile + the rotating mode)."""
    modes = get_available_modes(week_number=2)
    assert modes == ['steady', 'volatile', 'long_shot'], (
        f"slot-2 available modes should be ['steady', 'volatile', 'long_shot'], "
        f"got {modes}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T115 AC#4: probabilities sum to 100 and a 10,000-spin distribution check
# ════════════════════════════════════════════════════════════════════════════
def test_long_shot_probabilities_sum_to_100():
    """T115 AC#4: win_pct + loss_pct + jackpot_pct must total 100 for
    long_shot (required for any probability-based mode)."""
    ls = WHEEL_MODES['long_shot']
    total = ls['win_pct'] + ls['loss_pct'] + ls['jackpot_pct']
    assert total == 100, f"long_shot probabilities must sum to 100, got {total}"


def test_long_shot_spin_distribution_within_3_percent():
    """T115 AC#4: 10,000 spins in long_shot mode should land within ±3% of
    the spec's 20% win / 60% loss / 20% jackpot distribution.

    Standard deviation for n=10000, p=0.20 is ~40 outcomes (0.4%), so a
    ±3% band is roughly 7-8σ — extremely safe. This guards against
    off-by-one in the _resolve_spin roll threshold (e.g. a swap of win
    and jackpot ordering would still pass a less forgiving test).
    """
    random.seed(20260626)  # deterministic for CI
    n = 10_000
    state = {
        'owned': [], 'streak': 0, 'best_streak': 0, 'regen_recharge_wins': 0,
        'wins': 1000, 'losses': 1000, 'jackpot_echo_next': False,
        'spin_count': 1, 'active_cosmetics': [], 'proc_streak': 0,
    }
    ctx = {
        'effective_win_mult': 2.0, 'bonus_mult': 1, 'jackpot_chance': 0.0,
        'echo_chance': 0.0, 'charm_chance': 0.0, 'resilience_chance': 0.5,
        'proc_streak_level': 0, 'pot_active': False, 'pot_win_pct': 0.505,
        'active_wheel_mode': 'long_shot', 'stake_pct': 0,
    }

    counts = {'win': 0, 'lose': 0, 'jackpot': 0}
    for _ in range(n):
        _, events = _resolve_spin(**state, **ctx)
        counts[events['result']] += 1
        # NOTE: don't reuse new_state — long_shot has no stateful mechanic
        # (no drift like gravity), and _resolve_spin's returned state omits
        # spin_count, so reusing it would break the next iteration's call.

    # ±3% of n=10000 = ±300 outcomes per bucket.
    win_pct_actual     = 100.0 * counts['win']     / n
    lose_pct_actual    = 100.0 * counts['lose']    / n
    jackpot_pct_actual = 100.0 * counts['jackpot'] / n

    assert abs(win_pct_actual     - 20) <= 3, (
        f"win_pct {win_pct_actual:.2f}% outside [17, 23] "
        f"(counts: {counts})"
    )
    assert abs(lose_pct_actual    - 60) <= 3, (
        f"lose_pct {lose_pct_actual:.2f}% outside [57, 63] "
        f"(counts: {counts})"
    )
    assert abs(jackpot_pct_actual - 20) <= 3, (
        f"jackpot_pct {jackpot_pct_actual:.2f}% outside [17, 23] "
        f"(counts: {counts})"
    )
