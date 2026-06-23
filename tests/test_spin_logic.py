"""Tests for the _resolve_spin() helper extracted from game.py."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

# We need Flask app context to import game (blueprint import is lazy, but models are not)
# Import only _resolve_spin; avoid triggering blueprint registration.
import importlib.util, types
from contextlib import contextmanager


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


def _noop(*a, **kw):
    return lambda f: f


@contextmanager
def _fake_db(*a, **kw):
    yield None


# Register stubs before importing game.py
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
))
sys.modules.setdefault('psycopg2', _make_stub('psycopg2'))
sys.modules.setdefault('psycopg2.extras', _make_stub('psycopg2.extras', Json=lambda x: x))
sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db))
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

_spec = importlib.util.spec_from_file_location(
    'game',
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_resolve_spin = _mod._resolve_spin


# ── Helpers ───────────────────────────────────────────────────────────────────

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
    )
    ctx.update(overrides)
    return ctx


# ── Outcome determinism ───────────────────────────────────────────────────────

def test_pot_active_forces_win():
    """Pot active with 100% win chance always wins."""
    state = _base_state()
    ctx = _base_ctx(pot_active=True, pot_win_pct=1.0)
    for _ in range(20):
        _, events = _resolve_spin(**state, **ctx)
        assert events['result'] == 'win'


def test_lucky_seven_triggers_on_seventh():
    state = _base_state(owned=['lucky_seven'], spin_count=7)
    _, events = _resolve_spin(**state, **_base_ctx())
    assert events['result'] == 'win'
    assert events['lucky_seven_triggered'] is True


def test_lucky_seven_no_trigger_on_non_seventh():
    state = _base_state(owned=['lucky_seven'], spin_count=6)
    results = [_resolve_spin(**state, **_base_ctx())[1]['lucky_seven_triggered'] for _ in range(30)]
    assert not any(results)


def test_pot_active_uses_win_pct():
    # 100% win chance with pot active
    state = _base_state()
    ctx = _base_ctx(pot_active=True, pot_win_pct=1.0)
    for _ in range(20):
        _, ev = _resolve_spin(**state, **ctx)
        assert ev['result'] == 'win'


def test_catchup_bonus_removed_in_season_8():
    """S8: catch-up bonus for last-place players is no longer applied."""
    import inspect
    src = inspect.getsource(_resolve_spin)
    assert 'catchup_bonus_active' not in src, "catchup_bonus_active should be removed from _resolve_spin"
    assert '0.55' not in src, "Catch-up +5% win rate (0.55) should be removed"


# ── Win mechanics ─────────────────────────────────────────────────────────────

def test_win_increases_wins():
    state = _base_state(wins=100)
    # Force win via pot_active. Use effective_win_mult=16 (winmult_4) and
    # wager_unlock so the 10% stake produces a non-zero payout
    # (int(16 * 0.10) = 1).
    new_state, events = _resolve_spin(**_base_state(owned=['wager_unlock'], wins=100),
                                       **_base_ctx(pot_active=True, pot_win_pct=1.0,
                                                   stake_pct=10, effective_win_mult=16.0))
    assert new_state['wins'] > 100
    assert events['wins_delta'] > 0


def test_wins_delta_matches_state_change():
    state = _base_state(wins=500)
    new_state, events = _resolve_spin(**state, **_base_ctx(pot_active=True, pot_win_pct=1.0))
    assert events['wins_delta'] == new_state['wins'] - 500


def test_win_streak_increments():
    state = _base_state(streak=3)
    new_state, _ = _resolve_spin(**state, **_base_ctx(pot_active=True, pot_win_pct=1.0))
    assert new_state['streak'] == 4


def test_win_from_loss_streak_resets_to_1():
    state = _base_state(streak=-5)
    new_state, _ = _resolve_spin(**state, **_base_ctx(pot_active=True, pot_win_pct=1.0))
    assert new_state['streak'] == 1


# ── Jackpot echo ──────────────────────────────────────────────────────────────

def test_jackpot_echo_triggers_on_next_win():
    state = _base_state(owned=['jackpot', 'wager_unlock'], jackpot_echo_next=True, wins=100)
    # T102: use effective_win_mult=16 (winmult_4) so the 10% stake produces
    # a non-zero payout: int(16 * 25 * 0.10) = 40.
    new_state, events = _resolve_spin(**state, **_base_ctx(jackpot_chance=0.0, pot_active=True,
                                                           pot_win_pct=1.0, stake_pct=10,
                                                           effective_win_mult=16.0))
    assert events['jackpot_echo_triggered'] is True
    assert events['jackpot_hit'] is True
    # Payout is (effective_win_mult + bonus) * 25 * effective_stake
    assert new_state['wins'] > 100


# ── Guard mechanics ───────────────────────────────────────────────────────────

def test_guard_consumed_on_block(monkeypatch):
    import random
    # In Season 8, outcome is determined by random.random() for mode-based roll.
    # Force a lose outcome by making random.random() return a high value (above win_pct + jackpot_pct)
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(owned=['guard'])
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert events['guard_triggered'] is True
    assert events['guard_blocked'] is True
    assert 'guard' not in new_state['owned']
    assert events['losses_delta'] == 0


def test_regen_shield_absorbs_loss(monkeypatch):
    import random
    # Force a lose outcome
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(owned=['regen_shield'], regen_recharge_wins=0, losses=0)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert events['shield_used'] is True
    assert events['shield_used_type'] == 'regen_shield'
    assert new_state['losses'] == 0  # loss absorbed
    assert new_state['regen_recharge_wins'] > 0


# ── Wager insurance (regression: charge was consumed for zero effect) ──────────

def test_insurance_caps_loss_and_refunds_escrow(monkeypatch):
    import random
    monkeypatch.setattr(random, 'random', lambda: 0.99)  # force a loss
    # T102: use stake_pct=25 to get a non-zero loss. streak=-5 → loss_count=6
    # → loss_bonus=8 → base_loss=9. actual_loss = int(9 * 0.25) = 2.
    state = _base_state(owned=['wager_unlock'], streak=-5, wins=1000, losses=0)
    new_state, events = _resolve_spin(**state, **_base_ctx(stake_pct=25), insurance_active=True)
    assert events['insurance_used'] is True
    # T102: insurance cap at int(base_loss * effective_stake) = int(9 * 0.25) = 2.
    # The cap is essentially a no-op (actual_loss == cap with the new math).
    assert events['losses_delta'] == 2
    assert new_state['wins'] == 1000            # escrowed stake fully refunded

def test_loss_without_insurance_is_not_capped(monkeypatch):
    import random
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    # T102: use stake_pct=25. streak=-5 → loss_count=6 → loss_bonus=8 →
    # base_loss=9. actual_loss = int(9 * 0.25) = 2. losses_delta=2.
    state = _base_state(owned=['wager_unlock'], streak=-5, wins=1000, losses=0)
    new_state, events = _resolve_spin(**state, **_base_ctx(stake_pct=25))
    assert events['insurance_used'] is False
    assert events['losses_delta'] == 2
    # T102: stake_wins = int(1000 * 0.25) = 250. wins = 1000 - 250 = 750.
    assert new_state['wins'] == 750             # escrow forfeited, not refunded


# ── Wins cap ──────────────────────────────────────────────────────────────────

def test_wins_capped_at_max():
    huge = 5_000_001
    state = _base_state(wins=huge)
    new_state, _ = _resolve_spin(**state, **_base_ctx(pot_active=True, pot_win_pct=1.0))
    assert new_state['wins'] <= 5_000_000


# ── Loss streak ──────────────────────────────────────────────────────────────

def test_loss_from_positive_streak_goes_to_negative_1(monkeypatch):
    import random
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(streak=5)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert new_state['streak'] == -1

def test_loss_from_zero_streak_goes_to_negative_1(monkeypatch):
    import random
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(streak=0)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert new_state['streak'] == -1

def test_consecutive_losses_deepens_streak(monkeypatch):
    import random
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    state = _base_state(streak=-3)
    new_state, _ = _resolve_spin(**state, **_base_ctx())
    assert new_state['streak'] == -4


# ── Win/Bonus Power wiring (regression: was hardcoded to 1 regardless of owned items) ──

def _ctx(owned):
    gs = dict(equipped_class=None, prestige_level=0, aquarium_species=[], owned_items=owned)
    return _mod._build_spin_context(gs)

def test_winmult_level_0_is_1():
    assert _ctx([])['effective_win_mult'] == 1

def test_winmult_level_3_is_8():
    assert _ctx(['winmult_1', 'winmult_2', 'winmult_3'])['effective_win_mult'] == 8

def test_winmult_level_7_is_128():
    assert _ctx([f'winmult_{n}' for n in range(1, 8)])['effective_win_mult'] == 128

def test_bonusmult_level_0_is_1():
    assert _ctx([])['bonus_mult'] == 1

def test_bonusmult_level_6_is_70():
    assert _ctx([f'bonusmult_{n}' for n in range(1, 7)])['bonus_mult'] == 70
