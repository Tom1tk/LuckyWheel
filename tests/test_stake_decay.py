"""Tests for Season 9 stake decay (wealth-adaptive max stake)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wagers import compute_max_stake_pct, compute_payout_cap, STAKE_DECAY_FLOOR


def test_no_decay_below_1m():
    assert compute_max_stake_pct([], 0) == 30
    assert compute_max_stake_pct([], 999_999) == 30


def test_decay_bands():
    assert compute_max_stake_pct([], 1_000_000) == 25     # 1M-10M: −5
    assert compute_max_stake_pct([], 10_000_000) == 20    # 10M-100M: −10
    assert compute_max_stake_pct([], 100_000_000) == 15   # 100M-1B: −15
    assert compute_max_stake_pct([], 1_000_000_000) == 10 # >= 1B: −20 → floor 10


def test_decay_floor_at_any_scale():
    assert compute_max_stake_pct([], 1e40) == STAKE_DECAY_FLOOR


def test_decay_applies_on_top_of_extensions():
    # 35 base → 30 at the first band.
    assert compute_max_stake_pct(['wager_stake_extend_1'], 1_000_000) == 30
    # 45 base → 25 at max decay (the floor only kicks in below 25).
    assert compute_max_stake_pct(
        ['wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3'], 1e40
    ) == 25


def test_invalid_wins_treated_as_zero():
    assert compute_max_stake_pct([], None) == 30
    assert compute_max_stake_pct([], 'garbage') == 30


# ── Vault payout cap ──────────────────────────────────────────────────────────

def test_payout_cap_uncapped_below_1m():
    assert compute_payout_cap(0) is None
    assert compute_payout_cap(999_999) is None


def test_payout_cap_doubles_at_1m():
    assert compute_payout_cap(1_000_000) == 2_000_000
    assert compute_payout_cap(2_000_000) == 4_000_000


def test_payout_cap_scales_with_wins():
    assert compute_payout_cap(1e20) == 2e20
