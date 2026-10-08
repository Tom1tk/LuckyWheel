"""Tests for T86 (prestige_efficiency wins retention).

T86 AC#1–3: ``compute_wins_kept`` returns ``int(wins * 0.1 * level)`` where
``level = count(prestige_efficiency)``. The 1,000,000 threshold is fixed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ════════════════════════════════════════════════════════════════════════════
# T86: prestige_efficiency — wins retention only
# ════════════════════════════════════════════════════════════════════════════
def test_get_prestige_threshold_is_always_one_million():
    """T86 AC#2: the prestige threshold is always 1,000,000 regardless of
    prestige_efficiency level."""
    from prestige import get_prestige_threshold, PRESTIGE_WIN_THRESHOLD
    assert PRESTIGE_WIN_THRESHOLD == 1_000_000
    assert get_prestige_threshold([]) == 1_000_000
    assert get_prestige_threshold(['prestige_efficiency'] * 5) == 1_000_000
    assert get_prestige_threshold(['prestige_efficiency']) == 1_000_000


def test_compute_wins_kept_zero_at_level_0():
    """T86 AC#1 / T121: at level 0, new_wins = 0 (always, even before T121)."""
    from prestige import compute_wins_kept
    assert compute_wins_kept(2_000_000, ['prestige_unlock']) == 0
    assert compute_wins_kept(5_000_000, []) == 0


def test_compute_wins_kept_half_at_level_5():
    """T86 AC#1 / T121: prestige_efficiency was retired — even at level 5,
    wins_kept is 0. The level no longer has any effect."""
    from prestige import compute_wins_kept
    owned = ['prestige_unlock'] + ['prestige_efficiency'] * 5
    assert compute_wins_kept(2_000_000, owned) == 0


def test_compute_wins_kept_uses_floor():
    """T86 AC#1 / T121: result is always 0 (the floor behaviour is moot)."""
    from prestige import compute_wins_kept
    assert compute_wins_kept(1_500_000, ['prestige_efficiency']) == 0
    assert compute_wins_kept(7, ['prestige_efficiency']) == 0
    assert compute_wins_kept(9, ['prestige_efficiency']) == 0
    assert compute_wins_kept(10, ['prestige_efficiency']) == 0
