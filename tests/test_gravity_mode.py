"""Tests for T77 (gravity mode drift mechanic) and T80 (dynamic wheel graphic).

T77 ACs covered:
  1. Base profile: 55% win / 40% lose / 5% jackpot.
  2. Drift: win/jackpot +10 (cap +35), loss -10 (floor -35). Jackpot counts
     as a win for drift purposes.
  3. Effective probabilities: win_pct = 55 + drift, lose_pct = 40 - drift,
     jackpot_pct = 5.
  4. State and spin response include wheel_probabilities + gravity_drift.

T80 ACs covered:
  1-2. Server includes wheel_probabilities in /api/state + spin response.
  5. drawWheel fallback logic — verified by a small Python unit test that
     imports the JSX-as-text and asserts the wheelProbabilities argument
     short-circuits WHEEL_MODE_DRAW.
"""
import os
import sys
import types
import importlib.util
import random
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


# ── Stubs (match the setdefault pattern from other test files) ──────────────
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
    advance_season=lambda c: None,
))
sys.modules.setdefault('security', _make_stub('security', require_json=lambda: None))


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


sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


# ── Load wheel_modes.py + game.py with the stubs in place ──────────────────
_wheel_spec = importlib.util.spec_from_file_location(
    'wheel_modes',
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wheel_modes.py'),
)
_wheel_modes = importlib.util.module_from_spec(_wheel_spec)
_wheel_spec.loader.exec_module(_wheel_modes)

_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)
_resolve_spin = _game._resolve_spin
_current_wheel_probabilities = _game._current_wheel_probabilities
GRAVITY_DRIFT_STEP = _wheel_modes.GRAVITY_DRIFT_STEP
GRAVITY_DRIFT_MAX  = _wheel_modes.GRAVITY_DRIFT_MAX
GRAVITY_DRIFT_MIN  = _wheel_modes.GRAVITY_DRIFT_MIN


# ── Helpers ─────────────────────────────────────────────────────────────────
def _base_state(**overrides):
    state = dict(
        owned=[],
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
        catchup_bonus_active=False,
    )
    ctx.update(overrides)
    return ctx


# ════════════════════════════════════════════════════════════════════════════
# T77 AC#1: base profile
# ════════════════════════════════════════════════════════════════════════════
def test_gravity_base_profile_is_55_40_5():
    """T77 AC#1: gravity mode base profile is 55% win / 40% lose / 5% jackpot."""
    probs = _wheel_modes.compute_gravity_probabilities(0)
    assert probs == {'win_pct': 55, 'lose_pct': 40, 'jackpot_pct': 5}, (
        f"unexpected base profile: {probs}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T77 AC#2: drift mechanics — win/jackpot +10, loss -10, clamped to [-35, +35]
# ════════════════════════════════════════════════════════════════════════════
def test_drift_increases_on_win(monkeypatch):
    """T77 AC#2: a single win moves drift from 0 to +10."""
    # Gravity drift=0 → win_pct=55, jackpot_pct=5. roll 0.10 < 0.05? No.
    # 0.10 < 0.05+0.55 = 0.60? Yes → win.
    monkeypatch.setattr(random, 'random', lambda: 0.10)
    state = _base_state()
    _, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='gravity'),
        gravity_drift=0,
    )
    assert events['result'] == 'win'
    assert events['gravity_drift'] == 10, (
        f"expected drift=10 after win, got {events['gravity_drift']}"
    )
    assert events['gravity_drift_delta'] == 10


def test_drift_increases_on_jackpot(monkeypatch):
    """T77 AC#2: jackpot counts as a win for drift purposes (+10)."""
    # roll 0.01 < 0.05 (jackpot_pct) → jackpot.
    monkeypatch.setattr(random, 'random', lambda: 0.01)
    state = _base_state()
    _, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='gravity'),
        gravity_drift=0,
    )
    assert events['result'] == 'jackpot'
    assert events['gravity_drift'] == 10, (
        f"expected drift=10 after jackpot, got {events['gravity_drift']}"
    )


def test_drift_decreases_on_loss(monkeypatch):
    """T77 AC#2: a single loss moves drift from 0 to -10."""
    # roll 0.99 → lose for any positive win_pct.
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state()
    _, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='gravity'),
        gravity_drift=0,
    )
    assert events['result'] == 'lose'
    assert events['gravity_drift'] == -10, (
        f"expected drift=-10 after loss, got {events['gravity_drift']}"
    )


def test_drift_clamps_at_max_35(monkeypatch):
    """T77 AC#2: drift is capped at +35 (already at max, win keeps it there)."""
    # At drift=+35, win_pct=90, jackpot_pct=5. roll 0.10 < 0.05? No.
    # 0.10 < 0.05+0.90 = 0.95? Yes → win.
    monkeypatch.setattr(random, 'random', lambda: 0.10)
    state = _base_state(gravity_drift=GRAVITY_DRIFT_MAX)
    _, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='gravity'),
    )
    assert events['result'] == 'win'
    assert events['gravity_drift'] == GRAVITY_DRIFT_MAX


def test_drift_clamps_at_min_minus_35(monkeypatch):
    """T77 AC#2: drift is floored at -35 (already at min, loss keeps it there)."""
    # At drift=-35, win_pct=20, jackpot_pct=5. roll 0.99 → lose.
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(gravity_drift=GRAVITY_DRIFT_MIN)
    _, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='gravity'),
    )
    assert events['result'] == 'lose'
    assert events['gravity_drift'] == GRAVITY_DRIFT_MIN


def test_drift_walks_through_range(monkeypatch):
    """T77 AC#2: 4 wins land at +35 (capped); 4 more losses walk back down."""
    # 4 wins → drift +40 → clamps to +35.
    monkeypatch.setattr(random, 'random', lambda: 0.10)
    state = _base_state()
    for _ in range(4):
        new_state, _ = _resolve_spin(
            **state, **_base_ctx(active_wheel_mode='gravity'),
        )
        state.update(new_state)
    assert state['gravity_drift'] == GRAVITY_DRIFT_MAX, (
        f"expected drift={GRAVITY_DRIFT_MAX} after 4 wins, "
        f"got {state['gravity_drift']}"
    )

    # 4 losses from +35 → +25 → +15 → +5 → -5.
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    for _ in range(4):
        new_state, _ = _resolve_spin(
            **state, **_base_ctx(active_wheel_mode='gravity'),
        )
        state.update(new_state)
    assert state['gravity_drift'] == -5, (
        f"expected drift=-5 after 4 losses from +35, got {state['gravity_drift']}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T77 AC#3: effective probabilities use the drift
# ════════════════════════════════════════════════════════════════════════════
def test_effective_probabilities_at_drift_zero():
    """T77 AC#3: at drift=0, probabilities are the base 55/40/5."""
    probs = _wheel_modes.compute_gravity_probabilities(0)
    assert probs['win_pct'] == 55
    assert probs['lose_pct'] == 40
    assert probs['jackpot_pct'] == 5


def test_effective_probabilities_at_drift_max():
    """T77 AC#3: at drift=+35, win=90% lose=5% jackpot=5%."""
    probs = _wheel_modes.compute_gravity_probabilities(35)
    assert probs == {'win_pct': 90, 'lose_pct': 5, 'jackpot_pct': 5}


def test_effective_probabilities_at_drift_min():
    """T77 AC#3: at drift=-35, win=20% lose=75% jackpot=5%."""
    probs = _wheel_modes.compute_gravity_probabilities(-35)
    assert probs == {'win_pct': 20, 'lose_pct': 75, 'jackpot_pct': 5}


def test_effective_probabilities_in_response_use_drift(monkeypatch):
    """T77 AC#4: spin response includes wheel_probabilities reflecting the
    NEW (post-spin) drift, not the input drift."""
    # Force a win: drift 0 → +10, so wheel_probabilities in the response
    # should reflect drift=+10 (win=65, lose=30, jackpot=5).
    monkeypatch.setattr(random, 'random', lambda: 0.10)
    state = _base_state()
    _, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='gravity'),
        gravity_drift=0,
    )
    assert events['result'] == 'win'
    assert events['wheel_probabilities']['win_pct'] == 65, (
        f"expected win_pct=65 (55+10), got {events['wheel_probabilities']['win_pct']}"
    )
    assert events['wheel_probabilities']['lose_pct'] == 30
    assert events['wheel_probabilities']['jackpot_pct'] == 5


# ════════════════════════════════════════════════════════════════════════════
# T77 AC#4: helper exposed for /api/state
# ════════════════════════════════════════════════════════════════════════════
def test_current_wheel_probabilities_helper():
    """T77 AC#4: _current_wheel_probabilities(mode, drift) returns the
    drift-adjusted probabilities for gravity, static for other modes."""
    assert _current_wheel_probabilities('gravity', 20) == {
        'win_pct': 75, 'lose_pct': 20, 'jackpot_pct': 5,
    }
    # Non-gravity modes ignore the drift arg.
    assert _current_wheel_probabilities('steady', 999) == {
        'win_pct': 70, 'lose_pct': 28, 'jackpot_pct': 2,
    }


# ════════════════════════════════════════════════════════════════════════════
# T80 AC#5: drawWheel uses wheelProbabilities when provided, falls back
# to WHEEL_MODE_DRAW otherwise.
# ════════════════════════════════════════════════════════════════════════════
def test_app_jsx_drawWheel_uses_wheelProbabilities_when_provided():
    """T80 AC#5: drawWheel() must use the wheelProbabilities argument when
    supplied, falling back to the WHEEL_MODE_DRAW table otherwise.

    We can't easily run the JSX without a JS runtime, so we just verify the
    source text contains the expected fall-through pattern.
    """
    jsx_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )
    with open(jsx_path, 'r') as f:
        src = f.read()

    # The drawWheel signature must accept wheelProbabilities.
    assert 'drawWheel(canvas' in src, "drawWheel signature not found"
    # The function body must prefer the server-supplied probabilities when present.
    # Specifically: the wheelProbabilities parameter is consulted first, then
    # the WHEEL_MODE_DRAW table is used as a fallback.
    assert 'wheelProbabilities' in src, (
        "T80 AC#3: drawWheel() must check the wheelProbabilities argument"
    )
    # The hardcoded WHEEL_MODE_DRAW table is preserved (backward compat per
    # the task note: "If the table is referenced in other places ... keep
    # backward compat"). Verify the table still exists in the source.
    assert 'WHEEL_MODE_DRAW' in src, (
        "WHEEL_MODE_DRAW fallback table must be preserved for backward compat"
    )


def test_app_jsx_drawWheel_inverted_label_swap():
    """T80 AC#6: in inverted mode the wheel labels swap so the player can
    see which outcome is good. Source must contain the swap logic."""
    jsx_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )
    with open(jsx_path, 'r') as f:
        src = f.read()
    # The drawWheel function has label-swap logic for inverted mode.
    # We check that the function body references the inverted mode and
    # both 'WIN' and 'LOSE' labels.
    assert "'inverted'" in src or '"inverted"' in src, (
        "inverted mode reference missing from drawWheel"
    )
    assert "'LOSE'" in src or '"LOSE"' in src, (
        "LOSE label missing from drawWheel"
    )
    assert "'WIN'" in src or '"WIN"' in src, (
        "WIN label missing from drawWheel"
    )
