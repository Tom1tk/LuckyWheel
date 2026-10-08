"""Tests for Season 9 prestige titles."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prestige import get_prestige_title, MAX_PRESTIGE_LEVEL


def test_title_ladder_basics():
    assert get_prestige_title(0) == 'Novice'
    assert get_prestige_title(4) == 'High Roller'
    assert get_prestige_title(10) == 'Grandmaster'
    assert get_prestige_title(20) == 'Legend'


def test_title_clamps_above_max():
    assert get_prestige_title(MAX_PRESTIGE_LEVEL + 1) == 'Legend'


def test_title_clamps_below_zero():
    assert get_prestige_title(-1) == 'Novice'


def test_title_clamps_non_numeric():
    assert get_prestige_title(None) == 'Novice'
    assert get_prestige_title('abc') == 'Novice'


def test_every_level_has_a_title():
    for level in range(0, MAX_PRESTIGE_LEVEL + 1):
        title = get_prestige_title(level)
        assert title, f"level {level} must have a non-empty title"
