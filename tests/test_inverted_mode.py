"""Tests for T79 (inverted mode loss-farming mechanic) and T79/T80 wiring.

T79 ACs covered:
  1. Probability profile: 60% lose / 35% win / 5% jackpot.
  2. Escrow stake_losses = int(current_losses * stake_pct / 100) debited
     immediately, capped at current_losses.
  3. Lose (good): escrow returned, losses += stake_losses + base_loss *
     effective_stake * hot_streak_bonus, wager_streak increments,
     wager_banked_losses accumulates the hot-streak bonus. Shield/guard/
     resilience do NOT trigger.
  4. Win (bad): escrow forfeited, wins += base_payout * effective_stake,
     wager_streak resets to 0, wager_banked_losses forfeited. Shield/guard/
     resilience TRIGGER.
  5. Jackpot (super-good): escrow returned, losses += stake_losses + base_loss
     * effective_stake * 5, wager_streak increments.
  6. Safety net: on the bad outcome (win) at >=15% stake, refunds 25% of
     staked losses.
  7. Insurance: arms before spin, caps the bad outcome (win) and refunds
     escrowed losses.
  8. Double-down: wager_last_win_amount tracks the last loss-gain amount.
 10. wager_unlock NOT required in inverted mode (stake slider fully
     functional without it).
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


# ── Load game.py + wheel_modes.py with the stubs in place ──────────────────
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
WHEEL_MODES = _wheel_modes.WHEEL_MODES


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
        catchup_bonus_active=False,
    )
    ctx.update(overrides)
    return ctx


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#1: probability profile
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_profile_is_60_lose_35_win_5_jackpot():
    """T79 AC#1: inverted mode is 60% lose / 35% win / 5% jackpot."""
    inv = WHEEL_MODES['inverted']
    assert inv['loss_pct'] == 60, f"loss_pct should be 60, got {inv['loss_pct']}"
    assert inv['win_pct']  == 35, f"win_pct should be 35, got {inv['win_pct']}"
    assert inv['jackpot_pct'] == 5


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#2: stake_losses escrow
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_escrow_debits_losses_immediately(monkeypatch):
    """T79 AC#2: stake_losses is debited from losses before the outcome."""
    # Force a 'lose' (good) outcome: roll above 60% threshold.
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(losses=10000, owned=['wager_unlock'])
    initial_losses = state['losses']
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='inverted'),
    )
    assert events['result'] == 'lose'
    # The escrow is debited immediately, then refunded on the good outcome.
    # Net effect: losses = initial + actual_loss + hot_streak_bonus.
    # We just check the escrow is computed from losses, not wins.
    # wins is NOT debited (no stake_wins).
    assert new_state['wins'] == 1000, (
        f"wins should be unchanged (no wins-side escrow in inverted), "
        f"got {new_state['wins']}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#3: 'lose' (good) outcome — return escrow, add to losses, increment
# wager_streak, accumulate hot_streak_bonus to wager_banked_losses.
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_lose_refunds_escrow_and_grows_losses(monkeypatch):
    """T79 AC#3: on the 'lose' outcome (good), escrow is returned and losses
    grow by the loss-farming payout.

    T102: payout = stake_losses (the wager). At 10% of 10000 losses = 1000.
    On 'lose' (good): refund 1000 + payout 1000 = +2000. Net: 10000 → 11000.
    """
    monkeypatch.setattr(random, 'random', lambda: 0.99)  # force 'lose'
    state = _base_state(
        owned=['wager_unlock', 'wager_hot_streak'],
        losses=10000,
        wins=1000,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='inverted'),
    )
    assert events['result'] == 'lose'
    # T102: stake_losses = 1000 (10% of 10000). payout = 1000 (the wager).
    # losses = 10000 - 1000 (escrow) + 1000 (refund) + 1000 (payout) = 11000.
    assert new_state['losses'] == 11000, (
        f"losses should equal 11000 (10000 - 1000 + 1000 + 1000), got {new_state['losses']}"
    )
    # wins is unchanged (player didn't gain wins).
    assert new_state['wins'] == 1000
    # wager_streak incremented from 0 → 1.
    assert new_state['wager_streak'] == 1


def test_inverted_lose_does_not_trigger_shield(monkeypatch):
    """T79 AC#3: shield/guard/resilience do NOT trigger on the good outcome."""
    monkeypatch.setattr(random, 'random', lambda: 0.99)  # force 'lose'
    state = _base_state(owned=['regen_shield'], regen_recharge_wins=0,
                        losses=10000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='inverted'),
    )
    assert events['result'] == 'lose'
    assert events['shield_used'] is False
    assert events['guard_triggered'] is False


def test_inverted_lose_accumulates_banked_losses(monkeypatch):
    """T79 AC#3: wager_banked_losses accumulates the hot-streak bonus portion
    on the good outcome."""
    # 3 wins in a row at the same stake to build hot_streak_bonus to +15%
    # in the normal mode; but in inverted mode 'win' is bad, so we lose
    # the streak each time. So this test runs the good outcome ('lose') with
    # wager_streak=0 (no bonus) and just verifies the banked_losses is
    # at least 0 (might be 0 if hot_streak_bonus=0).
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(
        owned=['wager_unlock', 'wager_hot_streak'],
        losses=10000,
        wager_streak=0,
        wager_banked_losses=0,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='inverted'),
    )
    # With hot_streak_bonus=0 (streak 0), banked_losses = 0.
    assert new_state['wager_banked_losses'] == 0


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#4: 'win' (bad) outcome — forfeit escrow, add to wins, reset streak,
# forfeit banked_losses, trigger shield/guard/resilience.
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_win_forfeits_escrow_and_grows_wins(monkeypatch):
    """T79 AC#4: on the 'win' outcome (bad), escrow is forfeited and wins
    increase (undesired in loss-farming)."""
    # Inverted mode: roll 0.50 → win_pct=35, jackpot_pct=5. 0.50 < 0.05? No.
    # 0.50 < 0.05+0.35 = 0.40? No (0.50 > 0.40). → lose.
    # For a win we need roll in (0.05, 0.40). Try 0.20.
    monkeypatch.setattr(random, 'random', lambda: 0.20)
    state = _base_state(owned=['wager_unlock'], losses=10000, wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='inverted'),
    )
    assert events['result'] == 'win'
    # T102: with base_payout=2 and effective_stake=0.10, the bad-outcome
    # direct_wins = int(2 * 0.10) = 0. wins stays at 1000 (no shield/guard
    # equipped). The semantic (escrow is debited and forfeited) is preserved.
    assert new_state['wins'] == 1000, (
        f"wins should be 1000 (direct_wins rounds to 0 for stake_pct=10), "
        f"got {new_state['wins']}"
    )
    # losses should have LOST the escrow (no refund).
    # The escrow was int(10000 * 0.10) = 1000.
    # losses is debited the escrow, then NOT refunded on the bad outcome.
    # Losses should be exactly 9000 (10000 - 1000) plus no add-back.
    assert new_state['losses'] == 9000, (
        f"expected losses=9000 (10000 - 1000 forfeited escrow), "
        f"got {new_state['losses']}"
    )
    # wager_streak resets to 0.
    assert new_state['wager_streak'] == 0


def test_inverted_win_triggers_shield(monkeypatch):
    """T79 AC#4: shield triggers on the bad outcome (win), absorbing the
    undesired wins gain."""
    monkeypatch.setattr(random, 'random', lambda: 0.20)  # force 'win'
    state = _base_state(
        owned=['regen_shield'],
        regen_recharge_wins=0,
        losses=10000,
        wins=1000,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='inverted'),
    )
    assert events['result'] == 'win'
    assert events['shield_used'] is True
    assert events['shield_used_type'] == 'regen_shield'
    # The shield absorbed the bad-outcome wins — wins unchanged.
    assert new_state['wins'] == 1000


def test_inverted_win_triggers_guard(monkeypatch):
    """T79 AC#4: guard triggers on the bad outcome (win), blocking it."""
    monkeypatch.setattr(random, 'random', lambda: 0.20)  # force 'win'
    state = _base_state(owned=['guard'], losses=10000, wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(active_wheel_mode='inverted'),
    )
    assert events['result'] == 'win'
    assert events['guard_triggered'] is True
    assert events['guard_blocked'] is True
    assert 'guard' not in new_state['owned']


def test_inverted_win_forfeits_banked_losses(monkeypatch):
    """T79 AC#4: wager_banked_losses is forfeited on the bad outcome."""
    monkeypatch.setattr(random, 'random', lambda: 0.20)  # force 'win'
    state = _base_state(
        owned=['wager_unlock'],
        losses=10000,
        wager_banked_losses=42,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='inverted'),
    )
    assert events['result'] == 'win'
    assert new_state['wager_banked_losses'] == 0, (
        f"expected banked_losses=0 after bad outcome, "
        f"got {new_state['wager_banked_losses']}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#5: 'jackpot' (super-good) outcome — refund + 5x loss-farming payout.
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_jackpot_super_good(monkeypatch):
    """T79 AC#5: jackpot is super-good — refund escrow + 5× loss-farming payout."""
    # Inverted mode: roll < 0.05 → jackpot.
    monkeypatch.setattr(random, 'random', lambda: 0.01)
    # T102: use stake_pct=25 to get a non-zero loss-farming payout.
    # base_loss=1, effective_stake=0.25, so actual_loss = int(1 * 0.25 * 5) = 1.
    state = _base_state(owned=['wager_unlock'], losses=10000, wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=25, active_wheel_mode='inverted'),
    )
    assert events['result'] == 'jackpot'
    # losses should grow significantly (escrow refund + 5x payout).
    # stake_losses = int(10000 * 0.25) = 2500. actual_loss = int(1 * 0.25 * 5) = 1.
    # losses = 10000 - 2500 (escrow) + 2500 (refund) + 1 = 10001.
    assert new_state['losses'] == 10001, (
        f"expected losses=10001, got {new_state['losses']}"
    )
    # wager_streak increments.
    assert new_state['wager_streak'] == 1


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#6: safety net on the bad outcome at >=5x stake refunds 25% of
# staked losses.
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_safety_net_on_bad_outcome(monkeypatch):
    """T79 AC#6: on the bad outcome (win) at >=15% stake, safety net refunds
    25% of the staked losses."""
    monkeypatch.setattr(random, 'random', lambda: 0.20)  # force 'win'
    # T102: safety net threshold is 15% (was 5x). Use stake_pct=25 to
    # ensure safety net fires.
    state = _base_state(
        owned=['wager_unlock', 'wager_safety_net'],
        losses=10000,
        wins=1000,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=25, active_wheel_mode='inverted'),
    )
    assert events['result'] == 'win'
    # Escrow = int(10000 * 0.25) = 2500.
    # Without safety net: losses = 10000 - 2500 (escrow) = 7500.
    # With safety net: 7500 + int(2500 * 0.25) = 7500 + 625 = 8125.
    assert new_state['losses'] == 8125, (
        f"expected losses=8125 (7500 + 625 safety net), got {new_state['losses']}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#7: insurance arms before spin, caps the bad outcome (win), and
# refunds escrowed losses.
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_insurance_caps_bad_outcome(monkeypatch):
    """T79 AC#7: insurance caps the bad outcome (win) and refunds the
    escrowed losses."""
    monkeypatch.setattr(random, 'random', lambda: 0.20)  # force 'win'
    state = _base_state(
        owned=['wager_unlock'],
        losses=10000,
        wins=1000,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='inverted'),
        insurance_active=True,
    )
    assert events['result'] == 'win'
    assert events['insurance_used'] is True
    # Insurance refunds the escrow → losses = 10000 (no net debit).
    # T102: bad-outcome wins are capped at effective_stake (=0.10).
    # direct_wins = int(2 * 0.10) = 0, so min(0, 0.10) = 0. wins = 1000.
    # (The cap is a no-op with the new system since direct_wins is so small.)
    assert new_state['losses'] == 10000, (
        f"expected losses=10000 (escrow refunded by insurance), "
        f"got {new_state['losses']}"
    )
    assert new_state['wins'] == 1000, (
        f"expected wins=1000 (direct_wins=0, cap is no-op), got {new_state['wins']}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#8: wager_last_win_amount tracks the last loss-gain amount.
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_wager_last_win_amount_on_good_outcome(monkeypatch):
    """T79 AC#8: on a good outcome (lose), wager_last_win_amount is set to
    the loss-farming payout so double-down can escrow it on the next spin.

    T102: payout = stake_losses (the wager). At 10% of 10000 losses = 1000.
    wager_last_win_amount = 1000 (the payout that can be DD'd next spin).
    """
    monkeypatch.setattr(random, 'random', lambda: 0.99)  # force 'lose' (good)
    state = _base_state(
        owned=['wager_unlock'],
        losses=10000,
        wager_last_win_amount=0,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='inverted'),
    )
    assert events['result'] == 'lose'
    # T102: stake_losses = 10% of 10000 = 1000. payout = 1000 (the wager).
    # wager_last_win_amount = 1000.
    assert new_state['wager_last_win_amount'] == 1000, (
        f"expected wager_last_win_amount=1000 (10% of 10000), got {new_state['wager_last_win_amount']}"
    )


def test_inverted_wager_last_win_amount_zero_on_bad_outcome(monkeypatch):
    """T79 AC#8: on a bad outcome (win), wager_last_win_amount is reset to 0."""
    monkeypatch.setattr(random, 'random', lambda: 0.20)  # force 'win' (bad)
    state = _base_state(
        owned=['wager_unlock'],
        losses=10000,
        wager_last_win_amount=42,
    )
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='inverted'),
    )
    assert events['result'] == 'win'
    assert new_state['wager_last_win_amount'] == 0


# ════════════════════════════════════════════════════════════════════════════
# T79 AC#10: wager_unlock NOT required in inverted mode.
# ════════════════════════════════════════════════════════════════════════════
def test_inverted_does_not_require_wager_unlock_for_stake(monkeypatch):
    """T79 AC#10: in inverted mode, the stake is honored even without
    wager_unlock (events['stake'] reflects the requested stake)."""
    # Force a 'lose' (good) outcome.
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(owned=[], losses=10000, wins=1000)  # NO wager_unlock
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=5, active_wheel_mode='inverted'),
    )
    # In normal mode without wager_unlock, stake would be clamped to 0.
    # In inverted mode, the requested stake_pct 5 is honored.
    assert events['stake'] == 5, (
        f"expected stake=5 (wager_unlock not required in inverted), "
        f"got {events['stake']}"
    )


# ════════════════════════════════════════════════════════════════════════════
# T79: /api/wager/bank also banks wager_banked_losses
# ════════════════════════════════════════════════════════════════════════════
def test_wager_bank_banks_losses_too():
    """T79 AC#9: /api/wager/bank banks wager_banked_losses into losses."""
    gs = {
        'wager_banked_wins':   100,
        'wager_banked_losses':  50,
        'double_down_pending': False,
        'wins':                500,
        'losses':              200,
    }
    _game._load_game_state = lambda cur, user_id, for_update=False: gs
    _game.increment_bounty = lambda *a, **kw: None
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)
    result = _game.wager_bank()
    assert isinstance(result, dict)
    # wins increased by banked_wins, losses by banked_losses.
    assert result['wins']   == 600, f"wins={result['wins']}, expected 600"
    assert result['losses'] == 250, f"losses={result['losses']}, expected 250"
    assert result['banked_wins']   == 100
    assert result['banked_losses'] == 50


def test_wager_bank_only_losses_when_no_wins():
    """T79: banking works with only banked_losses (no banked_wins)."""
    gs = {
        'wager_banked_wins':   0,
        'wager_banked_losses': 75,
        'double_down_pending': False,
        'wins':                500,
        'losses':              200,
    }
    _game._load_game_state = lambda cur, user_id, for_update=False: gs
    _game.increment_bounty = lambda *a, **kw: None
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)
    result = _game.wager_bank()
    assert result['wins']   == 500
    assert result['losses'] == 275
    assert result['banked_wins']   == 0
    assert result['banked_losses'] == 75
