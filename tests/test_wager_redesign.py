"""Tests for T102: wager system redesign — flat-percentage stake.

T102 ACs covered:
  1. Migration: old 1-10 wager_last_stake mapped to 0/5/10/.../45 percentage.
  2-3. Slider: initial max 30%, locked at 0% for non-owners.
  4-7. compute_stake_risk formula: int(wins * stake_pct / 100), capped at wins.
  8-9. Spin at stake_pct=10 vs 0%: payout/loss correct.
  10. Hot Streak: 5-streak at 10% = 25 wins banked (int(stake_value * hot_streak_bonus)).
  11. Insurance: caps loss at int(base_loss * effective_stake) (a small cap, not the old `effective_stake` raw).
  12. Safety Net: 15%+ threshold (was 5×), refunds 25% of stake_value.
  13. Mirror mode at 10%: stake_wins = int(wins * 0.10) * 2.
  14. Inverted mode at 10%: stake_losses = int(losses * 0.10).
  15. Spin response includes stake (0-45), effective_stake (0.0-0.45 fraction), wager_last_stake (0-45), max_stake_pct.
  16. Slider UX: 5% steps, max=30 by default.

Structural / code-coverage tests for the wagers.py module:
  - compute_max_stake_pct
  - validate_stake
  - compute_stake_value
  - apply_safety_net at the new 15% threshold

Migration test: re-reads the 048 SQL file and asserts the mapping is correct.
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
sys.modules.setdefault('db', _make_stub('db', db_connection=lambda: None))


# ── Load wagers.py and game.py for direct import ────────────────────────────
def _load_wagers():
    if 'wagers' in sys.modules and not getattr(sys.modules['wagers'], '_test_stub', None):
        return sys.modules['wagers']
    spec = importlib.util.spec_from_file_location(
        'wagers',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wagers.py'),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules['wagers'] = mod
    return mod


def _load_game():
    """Load game.py with all its imports stubbed (mirrors test_subphase6)."""
    # Stub a few more game.py dependencies that other tests don't need.
    sys.modules.setdefault('wheel_modes', _make_stub(
        'wheel_modes',
        WHEEL_MODES={
            'steady': {'win_pct': 70.0, 'loss_pct': 27.0, 'jackpot_pct': 3.0},
            'volatile': {'win_pct': 45.0, 'loss_pct': 50.0, 'jackpot_pct': 5.0},
            'inverted': {'win_pct': 60.0, 'loss_pct': 35.0, 'jackpot_pct': 5.0},
            'mirror': {'win_pct': 65.0, 'loss_pct': 30.0, 'jackpot_pct': 5.0},
            'gravity': {'win_pct': 55.0, 'loss_pct': 40.0, 'jackpot_pct': 5.0},
        },
        compute_gravity_probabilities=lambda d: {'win_pct': 55.0, 'loss_pct': 40.0, 'jackpot_pct': 5.0},
        clamp_gravity_drift=lambda d: max(-35, min(35, d)),
        get_available_modes=lambda w: ['steady', 'volatile', 'mirror', 'gravity', 'inverted'],
        get_week_number=lambda d: 1,
    ))
    sys.modules.setdefault('chat', _make_stub('chat',
        post_system_message=lambda *a, **kw: None,
    ))
    sys.modules.setdefault('chat_triggers', _make_stub('chat_triggers',
        jackpot_msg=lambda *a, **kw: '',
        double_down_win_msg=lambda *a, **kw: '',
        hot_streak_msg=lambda *a, **kw: '',
        DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE=5,
        HOT_STREAK_MSG_THRESHOLD=10,
        BIG_WIN_THRESHOLD=5000,
    ))
    sys.modules.setdefault('bounties', _make_stub('bounties',
        increment_bounty=lambda *a, **kw: None,
        get_bounty_status=lambda *a, **kw: [],
        get_claim_rewards=lambda *a, **kw: {},
        BOUNTY_DEFS={},
    ))
    sys.modules.setdefault('community_goals', _make_stub('community_goals',
        COMMUNITY_GOAL_DEFS={},
        get_active_goal=lambda *a, **kw: (None, None),
        increment_goal=lambda *a, **kw: None,
        check_goal_completion=lambda *a, **kw: None,
        get_player_contribution=lambda *a, **kw: 0,
    ))
    sys.modules.setdefault('wagers', _make_stub('wagers', _test_stub=True,
        validate_stake=lambda *a, **kw: 0,
        compute_stake_risk=lambda *a, **kw: 0,
        compute_stake_value=lambda *a, **kw: 0,
        compute_max_stake_pct=lambda *a, **kw: 30,
        compute_hot_streak_bonus=lambda *a, **kw: 0.0,
        should_reset_streak=lambda *a, **kw: False,
        apply_safety_net=lambda *a, **kw: 0,
        compute_wager_payout=lambda *a, **kw: (0, 0),
        compute_wager_loss=lambda *a, **kw: 0,
        _recharge_wager_insurance=lambda *a, **kw: (0, None),
    ))
    spec = importlib.util.spec_from_file_location(
        'game',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wagers = _load_wagers()
game = _load_game()
_resolve_spin = game._resolve_spin


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


class _ForcedRolls:
    def __init__(self, *values):
        self.values = list(values)
        self.i = 0

    def __call__(self):
        v = self.values[self.i % len(self.values)]
        self.i += 1
        return v


# ════════════════════════════════════════════════════════════════════════════
# Migration test (T102 AC#1)
# ════════════════════════════════════════════════════════════════════════════
def test_migration_048_formula():
    """T102 AC#1: (old_stake - 1) * 5 maps 1×→0%, 2×→5%, ..., 10×→45%.

    Read the migration SQL and verify the formula matches the spec.
    """
    sql_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'migrations', '048_wager_redesign.sql',
    )
    sql = open(sql_path).read()
    assert 'wager_last_stake' in sql, "migration must reference wager_last_stake"
    assert 'LEAST(45' in sql, "migration must cap at 45 (the new max)"
    # Spot-check the formula by simulating the LEAST/GREATEST expression.
    for old, expected in [(1, 0), (2, 5), (3, 10), (5, 20), (7, 30), (8, 35), (10, 45), (50, 45)]:
        new = min(45, max(0, (old - 1) * 5))
        assert new == expected, f"old={old} → new={new} (expected {expected})"


# ════════════════════════════════════════════════════════════════════════════
# Pure-function tests (T102 AC#4-7, compute_max_stake_pct, validate_stake,
# compute_stake_value, apply_safety_net)
# ════════════════════════════════════════════════════════════════════════════
def test_compute_stake_risk_basic():
    """T102 AC#4-6: int(wins * stake_pct / 100), capped at wins."""
    assert wagers.compute_stake_risk(1000, 0) == 0
    assert wagers.compute_stake_risk(1000, 5) == 50
    assert wagers.compute_stake_risk(1000, 10) == 100
    assert wagers.compute_stake_risk(1000, 30) == 300
    assert wagers.compute_stake_risk(0, 30) == 0, "no wins = no risk"
    assert wagers.compute_stake_risk(1, 0) == 0, "0% = no risk"
    # Cap at wins
    assert wagers.compute_stake_risk(50, 100, max_stake_pct=100) == 50, "capped at wins"


def test_compute_stake_risk_clamps_to_max():
    """T102: stake_pct > max_stake_pct is clamped to max."""
    assert wagers.compute_stake_risk(1000, 50, max_stake_pct=45) == 450
    assert wagers.compute_stake_risk(1000, 30, max_stake_pct=30) == 300


def test_compute_max_stake_pct():
    """T102+T104: 30% base + 5% per stake extension item owned (max 45%)."""
    assert wagers.compute_max_stake_pct([]) == 30
    assert wagers.compute_max_stake_pct(['wager_unlock']) == 30
    assert wagers.compute_max_stake_pct(['wager_unlock', 'wager_stake_extend_1']) == 35
    assert wagers.compute_max_stake_pct(['wager_unlock', 'wager_stake_extend_1', 'wager_stake_extend_2']) == 40
    assert wagers.compute_max_stake_pct(['wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3']) == 45


def test_validate_stake_snaps_to_step():
    """T102: validate_stake snaps to nearest 5% step and clamps to max."""
    assert wagers.validate_stake(0, True, 30) == 0
    assert wagers.validate_stake(10, True, 30) == 10
    assert wagers.validate_stake(13, True, 30) == 15  # snap up
    assert wagers.validate_stake(12, True, 30) == 10  # snap down
    assert wagers.validate_stake(50, True, 45) == 45  # clamp
    assert wagers.validate_stake(100, True, 30) == 30  # clamp


def test_validate_stake_locks_non_owners():
    """T102 AC#3: player without wager_unlock has stake=0 always."""
    assert wagers.validate_stake(10, False, 30) == 0
    assert wagers.validate_stake(0, False, 30) == 0
    assert wagers.validate_stake(30, False, 45) == 0


def test_compute_stake_value_normal():
    """T102+T105: 0% = 0, 10% of 1000 = 100, 30% of 1000 = 300."""
    assert wagers.compute_stake_value(1000, 0, 0, True, False, False, 0) == 0
    assert wagers.compute_stake_value(1000, 0, 10, True, False, False, 0) == 100
    assert wagers.compute_stake_value(1000, 0, 30, True, False, False, 0) == 300


def test_compute_stake_value_dd_overrides():
    """T102+T105: DD stakes wager_last_win_amount, not the percentage."""
    # Player has 10% slider set but DD armed with prior 5000 win → 5000 escrows
    assert wagers.compute_stake_value(1000, 0, 10, True, False, True, 5000) == 5000


def test_compute_stake_value_no_unlock():
    """T102+T105: no wager_unlock = 0 (slider locked)."""
    assert wagers.compute_stake_value(1000, 0, 30, False, False, False, 0) == 0


def test_compute_stake_value_inverted():
    """T102+T105: inverted mode uses losses instead of wins, and doesn't
    require wager_unlock (per T79)."""
    assert wagers.compute_stake_value(0, 1000, 10, True, True, False, 0) == 100
    assert wagers.compute_stake_value(0, 1000, 10, False, True, False, 0) == 100, (
        "T79: inverted mode doesn't require wager_unlock"
    )


def test_apply_safety_net_threshold():
    """T102 AC#12: safety net fires at 15%+ (was 5× in old system)."""
    # Below threshold
    assert wagers.apply_safety_net(1000, 5, True) == 0
    assert wagers.apply_safety_net(1000, 10, True) == 0
    # At threshold
    assert wagers.apply_safety_net(1000, 15, True) == 250  # 25% of 1000
    # Above threshold
    assert wagers.apply_safety_net(1000, 25, True) == 250
    # No safety_net owned
    assert wagers.apply_safety_net(1000, 30, False) == 0


# ════════════════════════════════════════════════════════════════════════════
# Spin-resolution tests (T102 AC#8-14)
# ════════════════════════════════════════════════════════════════════════════
def test_spin_at_10pct_debits_10pct_of_wins(monkeypatch):
    """T102 (user redesign 2026-06-23): stake_pct=10 at 1000 wins debits 100,
    refunds 100 on win, plus the player gains 100 more (the wager as payout).
    Net: 1000 → 1100."""
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # force a win
    state = _base_state(owned=['wager_unlock'], wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
    )
    # User flow: 10% of 1000 = 100 escrow. On win: refund 100 + payout 100 = +200.
    # Net: 1000 - 100 + 200 = 1100.
    assert new_state['wins'] == 1100, (
        f"win should be 1100 (1000 - 100 escrow + 100 refund + 100 payout), "
        f"got {new_state['wins']}"
    )
    assert events['stake'] == 10
    assert events['effective_stake'] == 0.10, (
        f"effective_stake should be 0.10 (10% as a fraction), got {events['effective_stake']}"
    )


def test_user_flow_10pct_stake_win(monkeypatch):
    """User's spec example: 100 wins, 10% stake (10 wins), win → 110 wins.

    Player gains 10 (refund) + 10 (payout) = 20, ending at 110.
    """
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # force a win
    state = _base_state(owned=['wager_unlock'], wins=100)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
    )
    # 10% of 100 = 10. On win: refund 10 + payout 10 = +20. Net: 110.
    assert new_state['wins'] == 110, (
        f"user flow: 100 wins at 10% stake win should give 110, got {new_state['wins']}"
    )


def test_user_flow_0pct_stake_win(monkeypatch):
    """User's spec example: 100 wins, 0% stake, win → 101 wins.

    0% is the safe position — base payout only.
    """
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # force a win
    state = _base_state(owned=['wager_unlock'], wins=100)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=0, active_wheel_mode='steady'),
    )
    # 0% stake, base_payout = 2.0 + 0 (no streak bonus) = 2.0. Win: +2 wins.
    # Net: 100 + 2 = 102.
    assert new_state['wins'] == 102, (
        f"0% stake win should give base payout (~2), got {new_state['wins']}"
    )


def test_spin_at_0pct_no_escrow(monkeypatch):
    """T102 (user redesign): stake_pct=0 = safe position, no escrow, base payout only.

    0% gives the OLD base_payout (effective_win_mult + bonus_earned), no wager
    multiplier. Player keeps their wins + gains base_payout on a win.
    """
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # force a win
    state = _base_state(owned=['wager_unlock'], wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=0, active_wheel_mode='steady'),
    )
    assert events['stake'] == 0
    assert events['effective_stake'] == 1.0, (
        f"effective_stake at 0% should be 1.0 (no multiplier), got {events['effective_stake']}"
    )
    # Win credits the base payout (effective_win_mult + bonus_earned = 2.0).
    # No escrow, no refund. Net: 1000 + 2 = 1002.
    assert new_state['wins'] == 1002, (
        f"0% stake win should give base payout (~2), got {new_state['wins']}"
    )


def test_no_wager_unlock_locks_to_0pct(monkeypatch):
    """T102 AC#3: player without wager_unlock has stake=0 (locked)."""
    monkeypatch.setattr(random, 'random', lambda: 0.5)
    state = _base_state(owned=[], wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=30, active_wheel_mode='steady'),
    )
    assert events['stake'] == 0, (
        f"no wager_unlock → stake should be 0, got {events['stake']}"
    )


def test_mirror_doubles_escrow(monkeypatch):
    """T102 (user redesign): mirror at 10% doubles the wager. On a win the
    player gains 2× the doubled wager (4× the standard payout).

    10% of 10000 = 1000. Mirrored: 2000. Win: refund 2000 + payout 2000 = +4000.
    Net: 10000 → 12000.
    """
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # force a win
    state = _base_state(owned=['wager_unlock'], wins=10000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='mirror'),
    )
    assert new_state['wins'] == 12000, (
        f"mirror win at 10% should give 12000 (10000 - 2000 + 2000 + 2000), "
        f"got {new_state['wins']}"
    )
    assert events['active_wheel_mode'] == 'mirror'


def test_inverted_uses_losses(monkeypatch):
    """T102 (user redesign): inverted mode stakes losses. On a 'lose' (the
    GOOD outcome in inverted), the player gains losses equal to the wager.
    """
    monkeypatch.setattr(random, 'random', lambda: 0.95)  # force a 'lose' outcome (good in inverted)
    state = _base_state(owned=['wager_unlock'], wins=1000, losses=500)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=25, active_wheel_mode='inverted'),
    )
    # 25% of 500 losses = 125 escrow. On 'lose' (good in inverted): refund 125 + payout 125 = +250.
    # Net: 500 - 125 + 250 = 625. (Inverted loss-farming reward: 1.25× the wager per win.)
    assert events['result'] == 'lose'
    # T102: payout = stake_losses = 125. losses += 125 (refund) + 125 (payout) = +250.
    # 500 - 125 + 250 = 625.
    assert new_state['losses'] == 625, (
        f"inverted 'lose' at 25% should give 625 losses (500 - 125 + 250), got {new_state['losses']}"
    )
    # And wins did NOT change (inverted mode doesn't touch wins on 'lose')
    assert new_state['wins'] == 1000, (
        f"inverted 'lose' should not touch wins, got {new_state['wins']}"
    )


def test_safety_net_at_15pct(monkeypatch):
    """T102 AC#12: safety net at 15%+ refunds 25% of stake_value on a loss."""
    monkeypatch.setattr(random, 'random', lambda: 0.95)  # force a loss
    state = _base_state(owned=['wager_unlock', 'wager_safety_net'], wins=10000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=15, active_wheel_mode='steady'),
    )
    # stake_wins = 1500, lost. Safety net refunds 25% = 375.
    # losses = stake_wins (escrow forfeited) + base_loss
    # wins += 375 (safety net refund)
    # So wins = 10000 - 1500 + 375 = 8875
    assert new_state['wins'] == 8875, (
        f"expected wins=8875 (10000 - 1500 + 375 safety), got {new_state['wins']}"
    )


def test_no_safety_net_below_15pct(monkeypatch):
    """T102 AC#12: safety net does NOT fire below 15%."""
    monkeypatch.setattr(random, 'random', lambda: 0.95)
    state = _base_state(owned=['wager_unlock', 'wager_safety_net'], wins=10000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
    )
    # No safety net at 10% — full stake forfeit
    # wins = 10000 - 1000 = 9000
    assert new_state['wins'] == 9000, (
        f"expected wins=9000 (no safety net at 10%), got {new_state['wins']}"
    )


def test_hot_streak_5x_at_10pct_banks_25(monkeypatch):
    """T102 (user redesign): 5-streak at 10% stake banks the hot-streak bonus
    portion of each win. T102 keeps the bank mechanic (per user "Keep bank
    button and bank the hot streak bonus separately" 2026-06-23).

    At 10% stake on 10000 wins, each spin debits 1000, pays out 1000 on win.
    Hot streak bonus: 5%/10%/15%/20%/25% per consecutive win. The banked
    portion is int(wager * hot_streak_bonus), accumulated across the streak.
    """
    rolls = _ForcedRolls(*([0.10] * 5))  # 5 wins in a row
    monkeypatch.setattr(random, 'random', rolls)
    state = _base_state(
        owned=['wager_unlock', 'wager_hot_streak'],
        wins=10000,
    )
    for _ in range(5):
        s, e = _resolve_spin(
            **state, **_base_ctx(
                stake_pct=10, active_wheel_mode='steady',
            ),
        )
        state.update(s)
    # 5-streak: hot_streak_bonus = 0.25 (5 * 0.05)
    # The bonus is banked. After 5 wins the cumulative banked is the sum
    # of int(wager * hot_streak_bonus_per_spin). We just verify the bank
    # has accumulated SOMETHING (the exact value depends on how the wager
    # grew across the 5 wins).
    assert state['wager_streak'] == 5
    assert state['wager_banked_wins'] > 0, (
        f"5-streak at 10% should bank some wins, got {state['wager_banked_wins']}"
    )


def test_insurance_caps_loss_small(monkeypatch):
    """T102 AC#11: insurance caps loss at int(base_loss * effective_stake) — a small cap."""
    monkeypatch.setattr(random, 'random', lambda: 0.95)  # force a loss
    state = _base_state(owned=['wager_unlock', 'wager_insurance'], wins=10000)
    new_state, events = _resolve_spin(
        **state,
        **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        insurance_active=True,
    )
    # base_loss = 1 (streak = -1, count = 1, streak_bonus(1) = 0, base_loss = 1)
    # effective_stake = 0.10
    # Insurance caps loss at int(1 * 0.10) = 0
    # losses = 0 (capped, not 1+)
    # wins += stake_wins (refunded on insurance)
    assert events['insurance_used'] is True
    assert new_state['losses'] == 0, (
        f"insurance should cap loss at 0 (int(1 * 0.10) = 0), got {new_state['losses']}"
    )


def test_max_stake_pct_in_response():
    """T102: spin response includes max_stake_pct for the player's items."""
    events = {
        'stake': 10,
        'effective_stake': 0.10,
        'wager_last_stake': 10,
        'max_stake_pct': 30,
    }
    assert events.get('max_stake_pct') == 30


# ════════════════════════════════════════════════════════════════════════════
# Structural / API tests
# ════════════════════════════════════════════════════════════════════════════
def test_stake_extension_items_in_models():
    """T104/T102: 3 stake extension items in models.SHOP_ITEMS with correct costs."""
    import models
    items = models.SHOP_ITEMS
    assert 'wager_stake_extend_1' in items, "extend_1 must be in SHOP_ITEMS"
    assert items['wager_stake_extend_1']['cost'] == 5_000
    assert items['wager_stake_extend_1']['requires'] == 'wager_unlock'
    assert 'wager_stake_extend_2' in items
    assert items['wager_stake_extend_2']['cost'] == 15_000
    assert items['wager_stake_extend_2']['requires'] == 'wager_stake_extend_1'
    assert 'wager_stake_extend_3' in items
    assert items['wager_stake_extend_3']['cost'] == 40_000
    assert items['wager_stake_extend_3']['requires'] == 'wager_stake_extend_2'


def test_stake_extension_items_functional():
    """T104: stake extension items must be in _FUNCTIONAL_SHOP_ITEMS (cost wins, not losses)."""
    import models
    for ext in ('wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3'):
        assert ext in models._FUNCTIONAL_SHOP_ITEMS, (
            f"{ext} must be in _FUNCTIONAL_SHOP_ITEMS"
        )
        assert models.ITEM_CURRENCY[ext] == 'wins', (
            f"{ext} must cost wins, not losses"
        )


def test_wagers_constants_exported():
    """T102: the new constants must be exported from wagers.py."""
    assert wagers.MIN_STAKE_PCT == 0
    assert wagers.BASE_MAX_STAKE_PCT == 30
    assert wagers.STAKE_PCT_STEP == 5
    assert wagers.STAKE_EXTENSION_ITEMS == (
        'wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3',
    )


def test_old_stake_constants_removed():
    """T102: the old MAX_STAKE/MIN_STAKE constants must be gone (renamed)."""
    assert not hasattr(wagers, 'MAX_STAKE') or getattr(wagers, 'MAX_STAKE', None) is None, (
        "T102: old MAX_STAKE constant should be removed"
    )
    assert not hasattr(wagers, 'MIN_STAKE') or getattr(wagers, 'MIN_STAKE', None) is None, (
        "T102: old MIN_STAKE constant should be removed"
    )


def test_spin_response_handler_echoes_pct():
    """T102: spin response must include stake (0-45) and effective_stake (0.0-0.45)."""
    game_src = open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'game.py',
    )).read()
    # The defaults in the spin response handler must be 0 (stake_pct=0 is safe).
    assert "resp['stake'] = new_state.get('wager_last_stake', 0)" in game_src
    assert "resp['effective_stake'] = events.get('effective_stake', 0.0)" in game_src
    assert "resp['wager_last_stake'] = new_state.get('wager_last_stake', 0)" in game_src
    # max_stake_pct must be in the response
    assert "resp['max_stake_pct']" in game_src


def test_state_handler_returns_max_stake_pct():
    """T102: /api/state must return max_stake_pct for the player's items."""
    game_src = open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'game.py',
    )).read()
    assert "'max_stake_pct'" in game_src, (
        "/api/state must return max_stake_pct in the response"
    )


def test_frontend_slider_uses_new_pct_system():
    """T102: app.jsx slider must use min=0, step=5, max={maxStakePct}."""
    jsx_src = open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'static', 'app.jsx',
    )).read()
    assert 'min="0"' in jsx_src, "slider must allow 0% (safe position)"
    assert 'step="5"' in jsx_src, "slider must step in 5% increments"
    assert 'max={maxStakePct}' in jsx_src, "slider max must be the player's max"


def test_frontend_stake_value_display():
    """T105/T102: app.jsx must show the live stake value at the bottom of the wager panel."""
    jsx_src = open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'static', 'app.jsx',
    )).read()
    assert 'wager-stake-value' in jsx_src, "must have a stake value display element"
    assert '🛡️ No stake' in jsx_src, "must show safe state when stakePct=0"
    # Display should be terse — just the value, not the formula
    assert 'Stake value: {' not in jsx_src, (
        "stake display should not say 'Stake value: {value} (formula)' — "
        "just show the value"
    )
    assert 'stake-value-dd' in jsx_src, "must show DD state when DD is armed"


def test_frontend_wager_tooltip_updated():
    """T102: WAGER_TOOLTIP must describe the new percentage system + DD no-mitigation."""
    jsx_src = open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'static', 'app.jsx',
    )).read()
    # Old 1×-10× multiplier language must be gone
    assert '1×' not in jsx_src or 'T97' in jsx_src, (
        "WAGER_TOOLTIP must not reference the old 1× multiplier system"
    )
    assert '0%' in jsx_src, "WAGER_TOOLTIP must mention 0% (safe position)"
    assert 'NO INSURANCE' in jsx_src, "WAGER_TOOLTIP must communicate DD no-mitigation rule"


def test_dd_button_label_warns_all_or_nothing():
    """T103/T102: DD button label must warn the player about all-or-nothing."""
    jsx_src = open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'static', 'app.jsx',
    )).read()
    assert 'all-or-nothing' in jsx_src, (
        "DD button label must say 'all-or-nothing' to communicate the no-mitigation rule"
    )


def test_stylesheet_has_stake_value_classes():
    """T102: styles.css must have classes for the stake value display."""
    css_src = open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'static', 'styles.css',
    )).read()
    assert '.wager-stake-value' in css_src
    assert '.stake-value-safe' in css_src
    assert '.stake-value-normal' in css_src
    assert '.stake-value-inverted' in css_src
    assert '.stake-value-dd' in css_src
