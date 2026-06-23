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


# ── Fake DB plumbing ────────────────────────────────────────────────────────
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


sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


# ── Load game.py with the stubs in place ────────────────────────────────────
_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)
_resolve_spin = _game._resolve_spin
_recharge_wager_insurance = _game._recharge_wager_insurance


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


# ════════════════════════════════════════════════════════════════════════════
# T74: insurance rework — dice-charge model
# ════════════════════════════════════════════════════════════════════════════
def test_recharge_wager_insurance_awards_one_charge_per_10_min():
    """T74 AC#4: 1 charge per 10 min (600s), capped at 3."""
    now = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    last = now
    # 0 elapsed → no new charge.
    charges, new_last = _recharge_wager_insurance(0, last, 3, now)
    assert charges == 0
    # 9 minutes → still 0.
    charges, _ = _recharge_wager_insurance(0, now - dt.timedelta(seconds=9*60), 3, now)
    assert charges == 0
    # 10 minutes → 1.
    charges, _ = _recharge_wager_insurance(0, now - dt.timedelta(seconds=10*60), 3, now)
    assert charges == 1
    # 25 minutes → 2 (bulk award, no offline accrual cap of 1).
    charges, _ = _recharge_wager_insurance(0, now - dt.timedelta(seconds=25*60), 3, now)
    assert charges == 2
    # 30 minutes → 3 (cap).
    charges, _ = _recharge_wager_insurance(0, now - dt.timedelta(seconds=30*60), 3, now)
    assert charges == 3
    # 1 hour → still 3 (capped).
    charges, _ = _recharge_wager_insurance(0, now - dt.timedelta(hours=1), 3, now)
    assert charges == 3


def test_recharge_wager_insurance_pauses_at_cap():
    """T74 AC#4: timer pauses at cap."""
    now = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # At cap, last_recharge should NOT advance (so the next call after more
    # elapsed time still gives 0 — prevents offline accrual stacking).
    last = now - dt.timedelta(hours=1)
    charges, new_last = _recharge_wager_insurance(3, last, 3, now)
    assert charges == 3
    assert new_last == last, (
        f"expected last_recharge unchanged at cap, got {new_last} (was {last})"
    )


def test_recharge_wager_insurance_partial_progress():
    """Bulk-award partial progress: 15 min from 0 → 1, with last_recharge
    advanced by 10 min (not 15), so a second 10 min later yields another 1."""
    now = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    last = now - dt.timedelta(seconds=15*60)
    charges, new_last = _recharge_wager_insurance(0, last, 3, now)
    assert charges == 1
    # new_last = last + 10min = now - 5min. So if we call again at now,
    # elapsed is 5 min → no new charge. But 5 more minutes → 1.
    future = now + dt.timedelta(seconds=5*60)
    charges2, _ = _recharge_wager_insurance(charges, new_last, 3, future)
    assert charges2 == 2


def test_insurance_endpoint_consumes_charge_and_resets_recharge():
    """T74 AC#5: arming insurance decrements charges and resets recharge to NOW
    if resulting charges < max."""
    # Use a recent last_recharge (just now) so the recharge helper doesn't add
    # a charge — the test focuses on the arming decrement behavior.
    now = dt.datetime.now(timezone.utc)
    gs = {
        'owned_items': ['wager_insurance'],
        'wager_insurance_charges': 2,
        'wager_insurance_armed': False,
        'wager_insurance_last_recharge': now,
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_insurance()
    assert isinstance(result, dict)
    assert result['wager_insurance_charges'] == 1
    # The UPDATE should set wager_insurance_charges = 1 and reset last_recharge.
    update = next((s for s, _ in conn.log if s.lstrip().upper().startswith('UPDATE')), None)
    assert update is not None
    assert 'wager_insurance_charges = %s' in update
    assert 'wager_insurance_armed = TRUE' in update
    assert 'wager_insurance_last_recharge = %s' in update
    # Bind params: (new_charges, new_last_recharge, user_id) = (1, NOW-ish, 1).
    sql_params = next(p for s, p in conn.log if s.lstrip().upper().startswith('UPDATE'))
    assert sql_params[0] == 1


def test_insurance_fires_on_loss_caps_loss_and_refunds_escrow(monkeypatch):
    """T74 AC#6: insurance fires on a loss → cap actual_loss at effective_stake,
    refund escrowed stake_wins. Skip safety net (AC#7)."""
    monkeypatch.setattr(random, 'random', lambda: 0.95)  # loss
    state = _base_state(
        owned=['wager_unlock', 'wager_safety_net'],
        wins=10000,
        wager_last_stake=10,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        insurance_active=True,
    )
    assert events['result'] == 'lose'
    assert events['insurance_used'] is True
    # T102: stake_wins = int(10000 * 0.10) = 1000. base_loss=1, effective_stake=0.10,
    # actual_loss = int(1 * 0.10) = 0. The insurance cap is essentially a no-op
    # (actual_loss is already 0 at this stake). wins = 10000 - 1000 + 1000 = 10000.
    assert new_state['wins'] == 10000, (
        f"expected wins=10000 (escrow refunded, no safety net), got {new_state['wins']}"
    )
    # losses += 0 (base_loss=1 rounds to 0 at stake_pct=10).
    assert new_state['losses'] == 0, (
        f"expected losses=0 (actual_loss rounds to 0), got {new_state['losses']}"
    )


def test_insurance_does_not_apply_safety_net(monkeypatch):
    """T74 AC#7: when insurance fires, safety net is skipped entirely."""
    monkeypatch.setattr(random, 'random', lambda: 0.95)  # loss
    # Without insurance, safety net would refund 25% of stake_wins.
    # T102: safety net threshold is 15%, so use stake_pct=25 to trigger it.
    state = _base_state(
        owned=['wager_unlock', 'wager_safety_net'],
        wins=10000,
        wager_last_stake=10,
    )
    # Without insurance (stake_pct=25): stake_wins = 2500 (forfeited).
    # Safety net refunds 25% = 625. wins = 10000 - 2500 + 625 = 8125.
    new_no_ins, _ = _resolve_spin(
        **state, **_base_ctx(stake_pct=25, active_wheel_mode='steady'),
        insurance_active=False,
    )
    assert new_no_ins['wins'] == 8125, (
        f"baseline (no insurance, safety net): expected 8125, got {new_no_ins['wins']}"
    )
    # With insurance: wins = 10000 (full refund of the 2500 escrow).
    new_with_ins, _ = _resolve_spin(
        **state, **_base_ctx(stake_pct=25, active_wheel_mode='steady'),
        insurance_active=True,
    )
    assert new_with_ins['wins'] == 10000, (
        f"with insurance: expected 10000 (full escrow refund), "
        f"got {new_with_ins['wins']}"
    )


def test_insurance_charge_wasted_on_win(monkeypatch):
    """T74 AC#6: insurance on a win → charge wasted, no payout change beyond
    the normal win path. insurance_used stays False (it only fires on loss)."""
    monkeypatch.setattr(random, 'random', lambda: 0.10)  # win
    state = _base_state(
        owned=['wager_unlock'],
        wins=10000,
        wager_last_stake=10,
    )
    # Without insurance: normal win path.
    new_no_ins, ev_no = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        insurance_active=False,
    )
    # With insurance: identical win result (insurance does nothing on win).
    new_with_ins, ev_with = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        insurance_active=True,
    )
    assert ev_no['result'] == 'win'
    assert ev_with['result'] == 'win'
    assert ev_with['insurance_used'] is False
    assert new_no_ins['wins'] == new_with_ins['wins'], (
        f"insurance on win should not affect payout: "
        f"no_ins={new_no_ins['wins']} vs with_ins={new_with_ins['wins']}"
    )


def test_insurance_armed_field_in_state_response():
    """T74 AC#9: /api/state response includes wager_insurance_armed."""
    # Smoke-test: verify the column is read in /api/state.
    # We don't drive the full endpoint (it's heavy), just verify the SQL.
    state_sql = _game._GAME_STATE_SQL
    assert 'wager_insurance_armed' in state_sql
    assert 'wager_insurance_last_recharge' in state_sql
    assert 'wager_last_win_amount' in state_sql


def test_wager_insurance_arm_already_armed_returns_409():
    """T74: arming insurance when already armed returns 409."""
    gs = {
        'owned_items': ['wager_insurance'],
        'wager_insurance_charges': 2,
        'wager_insurance_armed': True,
        'wager_insurance_last_recharge': dt.datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_insurance()
    assert isinstance(result, tuple)
    body, status = result
    assert status == 409
    assert body == {'error': 'Insurance already armed'}


def test_wager_insurance_no_charges_returns_403():
    """T74: arming insurance with 0 charges returns 403."""
    # Use a recent last_recharge so the recharge helper doesn't add a charge.
    now = dt.datetime.now(timezone.utc)
    gs = {
        'owned_items': ['wager_insurance'],
        'wager_insurance_charges': 0,
        'wager_insurance_armed': False,
        'wager_insurance_last_recharge': now,
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_insurance()
    assert isinstance(result, tuple)
    body, status = result
    assert status == 403
    assert 'No insurance charges' in body['error']


def test_wager_insurance_unowned_returns_403():
    """T74: arming insurance without owning the item returns 403."""
    gs = {
        'owned_items': [],  # no wager_insurance
        'wager_insurance_charges': 2,
        'wager_insurance_armed': False,
        'wager_insurance_last_recharge': dt.datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_insurance()
    assert isinstance(result, tuple)
    body, status = result
    assert status == 403
    assert 'not unlocked' in body['error']
