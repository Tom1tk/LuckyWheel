"""Focused tests for T86: prestige_efficiency as win retention only.

T86 AC#1: ``compute_wins_kept(wins, owned_items)`` returns
``int(wins * 0.1 * level)`` where ``level = count(prestige_efficiency)``.

T86 AC#2: the 1,000,000 wins cost threshold is NOT reduced by efficiency.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ════════════════════════════════════════════════════════════════════════════
# T86 AC#1 (retired by T121): compute_wins_kept now always returns 0
# ════════════════════════════════════════════════════════════════════════════
def test_efficiency_level_0_keeps_zero_wins():
    from prestige import compute_wins_kept
    # T121: prestige_efficiency is retired — the helper is now a no-op.
    # 2,000,000 wins with no prestige_efficiency → 0 retained.
    assert compute_wins_kept(2_000_000, ['prestige_unlock']) == 0
    assert compute_wins_kept(2_000_000, []) == 0
    # 5,000,000 wins with no efficiency → 0 retained.
    assert compute_wins_kept(5_000_000, ['prestige_unlock']) == 0


def test_efficiency_level_5_keeps_zero_wins():
    """T121: even at level 5, wins are fully reset to 0 (operator removed
    the prestige_efficiency retention mechanic entirely)."""
    from prestige import compute_wins_kept
    owned = ['prestige_unlock'] + ['prestige_efficiency'] * 5
    assert compute_wins_kept(2_000_000, owned) == 0
    assert compute_wins_kept(4_000_000, owned) == 0
    assert compute_wins_kept(1_000_000, owned) == 0


def test_efficiency_intermediate_levels():
    """T121: every level returns 0 (operator removed the level scaling)."""
    from prestige import compute_wins_kept
    for level in (1, 2, 3, 4, 5):
        owned = ['prestige_unlock'] + ['prestige_efficiency'] * level
        result = compute_wins_kept(1_000_000, owned)
        assert result == 0, (
            f"level {level}: T121 retired retention, expected 0, got {result}"
        )


def test_efficiency_floor_behavior():
    """T121: floor behaviour is moot because the function always returns 0
    — but the regression guard stays so anyone re-introducing the formula
    notices immediately."""
    from prestige import compute_wins_kept
    assert compute_wins_kept(1_500_000, ['prestige_efficiency']) == 0
    assert compute_wins_kept(7, ['prestige_efficiency']) == 0
    assert compute_wins_kept(11, ['prestige_efficiency']) == 0


# ════════════════════════════════════════════════════════════════════════════
# T86 AC#2: 1,000,000 threshold is not reduced
# ════════════════════════════════════════════════════════════════════════════
def test_threshold_is_always_one_million():
    """T86 AC#2: get_prestige_threshold returns 1,000,000 for any owned set."""
    from prestige import get_prestige_threshold
    for owned in [
        [],
        ['prestige_unlock'],
        ['prestige_unlock', 'prestige_efficiency'],
        ['prestige_unlock'] + ['prestige_efficiency'] * 5,
        ['prestige_unlock', 'prestige_efficiency', 'prestige_legacy'],
    ]:
        assert get_prestige_threshold(owned) == 1_000_000, (
            f"threshold changed for owned={owned}"
        )
