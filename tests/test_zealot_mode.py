"""Tests for the Season 9 "Zealot" wheel mode.

Season 9 ACs covered:
  1. WHEEL_MODES['zealot'] has the spec values (50/42/8, multiplier 100).
  2. Zealot is part of the weekly rotation (index % 5).
  3. Probabilities sum to 100.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import wheel_modes


def test_zealot_mode_values():
    z = wheel_modes.WHEEL_MODES['zealot']
    assert z['win_pct'] == 50, f"zealot win_pct should be 50, got {z['win_pct']}"
    assert z['loss_pct'] == 42, f"zealot loss_pct should be 42, got {z['loss_pct']}"
    assert z['jackpot_pct'] == 8, f"zealot jackpot_pct should be 8, got {z['jackpot_pct']}"
    assert z['jackpot_multiplier'] == 100, (
        f"zealot jackpot_multiplier should be 100, got {z['jackpot_multiplier']}"
    )
    assert z['description'], "zealot mode must have a description"


def test_zealot_probabilities_sum_to_100():
    z = wheel_modes.WHEEL_MODES['zealot']
    total = z['win_pct'] + z['loss_pct'] + z['jackpot_pct']
    assert total == 100, f"zealot probabilities must sum to 100, got {total}"


def test_zealot_in_rotation():
    assert 'zealot' in wheel_modes._ROTATING_MODES, (
        "zealot must be in the weekly rotation"
    )
    assert wheel_modes.get_rotating_mode(week_number=4) == 'zealot', (
        "week % 5 == 4 should yield 'zealot'"
    )
