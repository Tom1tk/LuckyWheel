"""Unit tests for models.py — pure functions with no DB or Flask needed."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from models import (
    FISH_CATALOG, FISH_SKINS, SHOP_ITEMS, ALL_ITEMS,
    roll_fish, fish_value, lure_bite_delay_seconds, lure_value_multiplier,
    autofisher_catch_rate, streak_bonus, dice_max_charges,
    inf_upgrade_cost, INFINITE_UPGRADES,
    lure_mastery_mult,
    AUTO_FISH_EXCLUDED, _AUTO_FISH_LEGENDARY,
)


# ── FISH_CATALOG integrity ────────────────────────────────────────────────────

def test_fish_catalog_weights_approx_100():
    # random.choices normalises automatically; weights just need to be positive and ~100
    total = sum(v['weight'] for v in FISH_CATALOG.values())
    assert 99.0 < total < 102.0, f"weights sum to {total}, expected roughly 100"


def test_all_items_keys_disjoint():
    shared = set(FISH_SKINS) & set(SHOP_ITEMS)
    assert not shared, f"FISH_SKINS and SHOP_ITEMS share keys: {shared}"


def test_all_items_coverage():
    assert set(ALL_ITEMS) == set(FISH_SKINS) | set(SHOP_ITEMS)


# ── roll_fish ─────────────────────────────────────────────────────────────────

def test_roll_fish_manual_returns_valid_id():
    for _ in range(50):
        sid = roll_fish(auto_mode=False)
        assert sid in FISH_CATALOG


def test_roll_fish_auto_excludes_legendary():
    for _ in range(200):
        sid = roll_fish(auto_mode=True, allow_rare=False)
        assert sid not in AUTO_FISH_EXCLUDED


def test_roll_fish_auto_rare_excludes_legendary_only():
    seen = set()
    for _ in range(500):
        seen.add(roll_fish(auto_mode=True, allow_rare=True))
    assert not seen & _AUTO_FISH_LEGENDARY, "legendary appeared in auto+allow_rare rolls"


def test_roll_fish_master_lure_and_happy_hour_valid():
    for _ in range(50):
        sid = roll_fish(auto_mode=False, master_lure=True, happy_hour=True)
        assert sid in FISH_CATALOG


# ── fish_value ────────────────────────────────────────────────────────────────

def test_fish_value_lure_0():
    val = fish_value('minnow', 0)
    assert val == 1  # base value 1, multiplier 1.0

def test_fish_value_lure_5():
    val = fish_value('minnow', 5)
    assert val == 20  # base 1 * 20.0

def test_fish_value_minimum_1():
    for sid in FISH_CATALOG:
        assert fish_value(sid, 0) >= 1


# ── lure_bite_delay_seconds ───────────────────────────────────────────────────

def test_lure_delay_shrinks_with_level():
    prev_min, prev_max = lure_bite_delay_seconds(0)
    for lvl in range(1, 6):
        lo, hi = lure_bite_delay_seconds(lvl)
        assert lo <= prev_min
        assert hi <= prev_max
        prev_min, prev_max = lo, hi

def test_lure_delay_min_less_than_max():
    for lvl in range(6):
        lo, hi = lure_bite_delay_seconds(lvl)
        assert lo < hi


# ── streak_bonus ──────────────────────────────────────────────────────────────

def test_streak_bonus_below_3_is_zero():
    assert streak_bonus(0) == 0
    assert streak_bonus(1) == 0
    assert streak_bonus(2) == 0

def test_streak_bonus_3_is_1():
    assert streak_bonus(3) == 1

def test_streak_bonus_strictly_increasing():
    prev = streak_bonus(3)
    for n in range(4, 100):
        cur = streak_bonus(n)
        assert cur >= prev, f"streak_bonus({n}) < streak_bonus({n-1})"
        prev = cur

def test_streak_bonus_hard_cap():
    assert streak_bonus(150) == streak_bonus(200) == 113096


# ── inf_upgrade_cost ──────────────────────────────────────────────────────────

def test_inf_upgrade_cost_tier_levels():
    cfg = INFINITE_UPGRADES['clickmult_inf']
    for i, cost in enumerate(cfg['tier_costs']):
        assert inf_upgrade_cost('clickmult_inf', i) == cost

def test_inf_upgrade_cost_beyond_tiers_increases():
    n = len(INFINITE_UPGRADES['clickmult_inf']['tier_costs'])
    cost_n   = inf_upgrade_cost('clickmult_inf', n)
    cost_n1  = inf_upgrade_cost('clickmult_inf', n + 1)
    assert cost_n1 > cost_n

def test_inf_upgrade_cost_only_clickmult_remains():
    # Season 8: only clickmult_inf remains in INFINITE_UPGRADES
    assert set(INFINITE_UPGRADES.keys()) == {'clickmult_inf'}


# ── dice_max_charges ──────────────────────────────────────────────────────────

def test_dice_max_charges_defaults():
    assert dice_max_charges([]) == 1

def test_dice_max_charges_with_upgrades():
    assert dice_max_charges(['dice_charge_2']) == 2
    assert dice_max_charges(['dice_charge_2', 'dice_charge_3']) == 3
    assert dice_max_charges(['dice_charge_2', 'dice_charge_3', 'dice_charge_4']) == 4


# ── proc-rate helpers ─────────────────────────────────────────────────────────

def test_lure_mastery_mult_level_0():
    assert lure_mastery_mult(0) == pytest.approx(1.0)

def test_lure_mastery_mult_level_1():
    assert lure_mastery_mult(1) == pytest.approx(1.10)
