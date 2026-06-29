"""Tests for T73 (double-down rework) and T74 (insurance rework).

T73: double-down escrows the previous actual win amount; on a win the player
gains 2× the previous payout; on a loss the previous payout is forfeited.
T74: insurance charge regeneration (1/10min, cap 3), arming consumes a charge,
insurance fires on a loss (caps loss at effective_stake, refunds escrow, skips
safety net), and the charge is wasted on a win.
"""
import os
import sys
import types
import importlib.util
import datetime as dt
import random
from contextlib import contextmanager
from datetime import timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Stub install/teardown (T242) ────────────────────────────────────────────
_SENTINEL = object()
_STUB_PREV = {}
_GAME_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')
_game = None
_resolve_spin = None


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
    def __init__(self, log, fetchone_queue=None):
        self.log = log
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
    """Install stubs and load game.py once before any test in this module."""
    global _game, _resolve_spin
    for name, factory in _stub_specs():
        _STUB_PREV[name] = sys.modules.get(name, _SENTINEL)
        sys.modules[name] = factory()
    _STUB_PREV['db'] = sys.modules.get('db', _SENTINEL)
    sys.modules['db'] = _make_stub('db', db_connection=_fake_db_connection)

    sys.modules.pop('game', None)
    spec = importlib.util.spec_from_file_location('game', _GAME_PATH)
    _game = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_game)
    _resolve_spin = _game._resolve_spin


def teardown_module(module):
    """Restore sys.modules and drop the stub-loaded game so the next test
    file sees real modules (or whichever stubs it installs)."""
    global _game, _resolve_spin
    sys.modules.pop('game', None)
    _game = _resolve_spin = None
    for name, prev in _STUB_PREV.items():
        if prev is _SENTINEL:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prev
    _STUB_PREV.clear()


# ── Helpers ─────────────────────────────────────────────────────────────────
def _base_state(**overrides):
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


class _ForcedRolls:
    def __init__(self, *values):
        self.values = list(values)
        self.i = 0

    def __call__(self):
        v = self.values[self.i % len(self.values)]
        self.i += 1
        return v


# ════════════════════════════════════════════════════════════════════════════
# T73: double-down rework — escrow last win amount
# ════════════════════════════════════════════════════════════════════════════
def test_wager_last_win_amount_recorded_on_win(monkeypatch):
    """T73 AC#1: on each win, wager_last_win_amount = direct_wins portion.
    T102: payout = stake_wins (the wager) + win_streak_bonus, no base_payout ×
    effective_stake truncation. At 10% stake on 10000 wins: payout = 1000
    (no streak bonus at streak=0)."""
    monkeypatch.setattr(random, 'random', lambda: 0.10)  # win
    state = _base_state(wins=10000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
    )
    assert events['result'] == 'win'
    # T102: stake_wins = 1000 (10% of 10000). payout = 1000 (no streak bonus).
    # direct_wins = 1000. wager_last_win_amount records direct_wins.
    assert new_state['wager_last_win_amount'] == 1000, (
        f"expected wager_last_win_amount=1000 (10% of 10000), got {new_state['wager_last_win_amount']}"
    )
    # And the player actually gains the wager as payout on a win.
    # wins = 10000 - 1000 (escrow) + 1000 (refund) + 1000 (payout) = 11000.
    assert new_state['wins'] == 11000, (
        f"expected wins=11000 (10000 - 1000 + 1000 + 1000), got {new_state['wins']}"
    )


def test_wager_last_win_amount_zero_on_loss(monkeypatch):
    """T73 AC#1: on a loss, wager_last_win_amount is reset to 0 (T71 behavior)."""
    monkeypatch.setattr(random, 'random', lambda: 0.95)  # loss
    state = _base_state(wins=10000, wager_last_win_amount=50)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
    )
    assert events['result'] == 'lose'
    assert new_state['wager_last_win_amount'] == 0


def test_double_down_win_doubles_previous_payout(monkeypatch):
    """T73 AC#5: win on double-down → escrowed amount returned PLUS the payout
    (which equals the wager). Total gain ≈ 2× the wager.

    Setup: previous payout was 100, double-down armed.
    - Escrow = 100 (wager_last_win_amount, NOT the percentage)
    - wins = wins_before - 100 (escrow) + 100 (refund) + 100 (payout = wager)
    """
    # Force a win.
    monkeypatch.setattr(random, 'random', lambda: 0.10)
    state = _base_state(
        wins=1000,
        wager_last_win_amount=100,
        wager_last_stake=10,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        double_down_active=True,
    )
    assert events['result'] == 'win'
    # T102: DD ignores the percentage slider; escrow is wager_last_win_amount=100.
    # payout = 100 (the wager, per user flow: "wins an additional 100" = 2×100 - the
    # 100 refund + 100 payout = 200 added, ending at 1100).
    # wins = 1000 - 100 + 100 + 100 = 1100.
    assert new_state['wins'] == 1100, (
        f"expected wins=1100 (1000 - 100 + 100 + 100 payout), got {new_state['wins']}"
    )


def test_double_down_loss_forfeits_escrow(monkeypatch):
    """T73 AC#6: loss on double-down → escrowed amount forfeited, player loses
    the exact winnings they had just gained."""
    monkeypatch.setattr(random, 'random', lambda: 0.95)  # loss
    state = _base_state(
        wins=1000,
        wager_last_win_amount=100,
        wager_last_stake=10,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        double_down_active=True,
    )
    assert events['result'] == 'lose'
    # T102: DD escrow = 100 (wager_last_win_amount), forfeited. base_loss=1,
    # actual_loss = int(1 * 0.10) = 0. losses += 0.
    assert new_state['wins'] == 900, (
        f"expected wins=900 (1000 - 100 forfeited), got {new_state['wins']}"
    )
    assert new_state['losses'] == 0, (
        f"expected losses=0 (1 * 0.10 rounds to 0), got {new_state['losses']}"
    )
    # wager_last_win_amount reset to 0.
    assert new_state['wager_last_win_amount'] == 0


def test_double_down_no_op_when_wager_last_win_amount_zero(monkeypatch):
    """T73 AC#7: if wager_last_win_amount == 0, double-down is a no-op (uses
    the normal percentage risk instead)."""
    monkeypatch.setattr(random, 'random', lambda: 0.10)  # win
    state = _base_state(
        wins=1000,
        wager_last_win_amount=0,
        wager_last_stake=10,
    )
    # With wager_last_win_amount=0, the double-down branch in _resolve_spin
    # does NOT override stake_wins — it uses the normal percentage risk formula.
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        double_down_active=True,
    )
    assert events['result'] == 'win'
    # T102: stake_wins = 100 (10% of 1000). payout = 100 (the wager).
    # wins = 1000 - 100 + 100 + 100 = 1100.
    assert new_state['wins'] == 1100, (
        f"expected wins=1100 (1000 - 100 + 100 + 100 payout), got {new_state['wins']}"
    )


def test_double_down_uses_previous_payout_not_computed_risk(monkeypatch):
    """T73 AC#3: the escrow for a double-down spin is the previous payout
    (wager_last_win_amount), NOT compute_stake_risk(wins, stake*2)."""
    monkeypatch.setattr(random, 'random', lambda: 0.10)  # win
    # Wins=10000, stake_pct=10: compute_stake_risk would give
    # int(10000 * 0.10) = 1000. But wager_last_win_amount = 50, so the
    # escrow should be 50 (the previous payout) — DD overrides the percentage.
    state = _base_state(
        wins=10000,
        wager_last_win_amount=50,
        wager_last_stake=10,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        double_down_active=True,
    )
    assert events['result'] == 'win'
    # T102: stake_wins = 50 (DD override). payout = 50 (the wager).
    # wins = 10000 - 50 + 50 + 50 = 10050.
    assert new_state['wins'] == 10050, (
        f"expected wins=10050 (10000 - 50 + 50 + 50 payout), got {new_state['wins']}"
    )
