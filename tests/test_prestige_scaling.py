"""T111: prestige threshold scales with the player's current prestige level.

The threshold to advance from level N to N+1 is:

    round(PRESTIGE_WIN_THRESHOLD * PRESTIGE_LEVEL_MULTIPLIER ** N)

Level 0 stays at 1,000,000 (unchanged from T86). Each subsequent level
multiplies the cost by 1.05 (preliminary value).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ════════════════════════════════════════════════════════════════════════════
# AC#1, AC#2, AC#3: threshold scales by PRESTIGE_LEVEL_MULTIPLIER per level
# ════════════════════════════════════════════════════════════════════════════
def test_prestige_threshold_scales_with_level():
    from prestige import get_prestige_threshold, PRESTIGE_LEVEL_MULTIPLIER, PRESTIGE_WIN_THRESHOLD

    # Level 0: unchanged from T86.
    assert get_prestige_threshold([], 0) == 1_000_000
    # Level 1: 1.05x.
    assert get_prestige_threshold([], 1) == 1_050_000
    # Level 5: round(1M * 1.05^5) = 1,276,282.
    assert get_prestige_threshold([], 5) == round(PRESTIGE_WIN_THRESHOLD * PRESTIGE_LEVEL_MULTIPLIER ** 5)
    assert get_prestige_threshold([], 5) == 1_276_282
    # Level 19: round(1M * 1.05^19) = 2,526,950.
    assert get_prestige_threshold([], 19) == round(PRESTIGE_WIN_THRESHOLD * PRESTIGE_LEVEL_MULTIPLIER ** 19)
    assert get_prestige_threshold([], 19) == 2_526_950

    # Formula holds for every level 0..MAX_PRESTIGE_LEVEL.
    for level in range(21):
        expected = round(PRESTIGE_WIN_THRESHOLD * PRESTIGE_LEVEL_MULTIPLIER ** level)
        assert get_prestige_threshold([], level) == expected, (
            f"level {level}: expected {expected}, "
            f"got {get_prestige_threshold([], level)}"
        )


def test_prestige_threshold_ignores_owned_items():
    """AC#1: only prestige_level matters. owned_items is accepted for
    signature compat with can_prestige but doesn't influence the value."""
    from prestige import get_prestige_threshold

    for level in (0, 1, 5, 19):
        baseline = get_prestige_threshold([], level)
        for owned in (
            ['prestige_unlock'],
            ['prestige_unlock', 'prestige_efficiency'] * 5,
            ['prestige_unlock', 'prestige_legacy'],
        ):
            assert get_prestige_threshold(owned, level) == baseline, (
                f"owned_items changed threshold at level {level}: {owned}"
            )


def test_prestige_threshold_default_level_is_zero():
    """The default keeps the old single-arg call sites working."""
    from prestige import get_prestige_threshold
    assert get_prestige_threshold(['prestige_unlock']) == 1_000_000
    assert get_prestige_threshold([]) == 1_000_000


# ════════════════════════════════════════════════════════════════════════════
# AC#6: get_prestige_bonus is unchanged (still +2% per level, +40% cap)
# ════════════════════════════════════════════════════════════════════════════
def test_prestige_bonus_unchanged():
    from prestige import get_prestige_bonus, MAX_PRESTIGE_LEVEL

    assert get_prestige_bonus(0) == 0.0
    assert get_prestige_bonus(1) == 0.02
    assert get_prestige_bonus(5) == 0.10
    assert get_prestige_bonus(10) == 0.20
    assert get_prestige_bonus(19) == 0.38
    # Level 20 (the cap) is +40% win multiplier.
    assert get_prestige_bonus(MAX_PRESTIGE_LEVEL) == 0.40

    # Linear, no compounding.
    for level in range(0, 21):
        assert get_prestige_bonus(level) == level * 0.02


# ════════════════════════════════════════════════════════════════════════════
# Regression: T86 invariants still hold
# ════════════════════════════════════════════════════════════════════════════
def test_efficiency_does_not_shorten_threshold():
    """T86 AC#2: prestige_efficiency never shortens the threshold. T111 keeps
    that property — efficiency only affects win retention, not the cost."""
    from prestige import get_prestige_threshold

    bare = ['prestige_unlock']
    with_eff = ['prestige_unlock'] + ['prestige_efficiency'] * 5
    for level in (0, 1, 5, 19):
        assert get_prestige_threshold(bare, level) == get_prestige_threshold(with_eff, level)
