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
sys.modules.setdefault('extensions', _make_stub('extensions', limiter=types.SimpleNamespace(limit=_noop)))
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
        shield_charges=0,
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


# ── Outcome determinism ───────────────────────────────────────────────────────

def test_singularity_always_wins():
    state = _base_state(owned=['singularity'])
    for _ in range(20):
        _, events = _resolve_spin(**state, **_base_ctx())
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


def test_catchup_bonus_higher_win_rate():
    """Over many trials, catchup=True should produce more wins than 50/50."""
    import random as _r
    _r.seed(42)
    wins_with = sum(
        1 for _ in range(1000)
        if _resolve_spin(**_base_state(), **_base_ctx(catchup_bonus_active=True))[1]['result'] == 'win'
    )
    assert wins_with > 520, f"Expected >520 wins/1000 with catchup, got {wins_with}"


# ── Win mechanics ─────────────────────────────────────────────────────────────

def test_win_increases_wins():
    state = _base_state(wins=100)
    # Force win via singularity
    new_state, events = _resolve_spin(**_base_state(owned=['singularity'], wins=100), **_base_ctx())
    assert new_state['wins'] > 100
    assert events['wins_delta'] > 0


def test_wins_delta_matches_state_change():
    state = _base_state(owned=['singularity'], wins=500)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert events['wins_delta'] == new_state['wins'] - 500


def test_win_streak_increments():
    state = _base_state(owned=['singularity'], streak=3)
    new_state, _ = _resolve_spin(**state, **_base_ctx())
    assert new_state['streak'] == 4


def test_win_from_loss_streak_resets_to_1():
    state = _base_state(owned=['singularity'], streak=-5)
    new_state, _ = _resolve_spin(**state, **_base_ctx())
    assert new_state['streak'] == 1


# ── Jackpot echo ──────────────────────────────────────────────────────────────

def test_jackpot_echo_triggers_on_next_win():
    state = _base_state(owned=['singularity', 'jackpot'], jackpot_echo_next=True, wins=100)
    new_state, events = _resolve_spin(**state, **_base_ctx(jackpot_chance=0.0))
    assert events['jackpot_echo_triggered'] is True
    assert events['jackpot_hit'] is True
    # Payout is (effective_win_mult + bonus) * 25
    assert new_state['wins'] > 100


# ── Guard mechanics ───────────────────────────────────────────────────────────

def test_guard_consumed_on_block(monkeypatch):
    import random
    monkeypatch.setattr(random, 'random', lambda: 0.0)  # always < 0.50 → guard blocks
    import secrets as _s
    monkeypatch.setattr(_s, 'choice', lambda seq: 'lose')
    state = _base_state(owned=['guard'])
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert events['guard_triggered'] is True
    assert events['guard_blocked'] is True
    assert 'guard' not in new_state['owned']
    assert events['losses_delta'] == 0


def test_regen_shield_absorbs_loss(monkeypatch):
    import secrets as _s
    monkeypatch.setattr(_s, 'choice', lambda seq: 'lose')
    state = _base_state(owned=['regen_shield'], regen_recharge_wins=0, losses=0)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert events['shield_used'] is True
    assert events['shield_used_type'] == 'regen_shield'
    assert new_state['losses'] == 0  # loss absorbed
    assert new_state['regen_recharge_wins'] > 0


# ── Auto-guard ────────────────────────────────────────────────────────────────

def test_auto_guard_buys_guard_when_affordable(monkeypatch):
    import secrets as _s
    monkeypatch.setattr(_s, 'choice', lambda seq: 'win')
    state = _base_state(owned=['auto_guard'], active_cosmetics=['auto_guard'], wins=1000)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    # Guard should have been bought and then available (not consumed on a win)
    assert events['auto_guard_failed'] is False


def test_auto_guard_fails_gracefully_when_broke(monkeypatch):
    import secrets as _s
    monkeypatch.setattr(_s, 'choice', lambda seq: 'win')
    state = _base_state(owned=['auto_guard'], active_cosmetics=['auto_guard'], wins=0)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert events['auto_guard_failed'] is True
    # Cosmetic stays active (should retry next time wins recover)
    assert 'auto_guard' in new_state['active_cosmetics']


# ── Wins cap ──────────────────────────────────────────────────────────────────

def test_wins_capped_at_max():
    import math
    huge = round(9.99e99) + 10**90
    state = _base_state(owned=['singularity'], wins=huge)
    new_state, _ = _resolve_spin(**state, **_base_ctx())
    assert new_state['wins'] <= round(9.99e99)


# ── Loss streak ──────────────────────────────────────────────────────────────

def test_loss_from_positive_streak_goes_to_negative_1(monkeypatch):
    import secrets as _s
    monkeypatch.setattr(_s, 'choice', lambda seq: 'lose')
    state = _base_state(streak=5)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert new_state['streak'] == -1

def test_loss_from_zero_streak_goes_to_negative_1(monkeypatch):
    import secrets as _s
    monkeypatch.setattr(_s, 'choice', lambda seq: 'lose')
    state = _base_state(streak=0)
    new_state, events = _resolve_spin(**state, **_base_ctx())
    assert new_state['streak'] == -1

def test_consecutive_losses_deepens_streak(monkeypatch):
    import secrets as _s
    monkeypatch.setattr(_s, 'choice', lambda seq: 'lose')
    state = _base_state(streak=-3)
    new_state, _ = _resolve_spin(**state, **_base_ctx())
    assert new_state['streak'] == -4
