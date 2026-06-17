"""Season 8 prestige system.

Replaces the Season 7 infinite upgrade axes with a flat, non-compounding
bonus capped at level 20. Each prestige level gives +2% base win value.

Starting prestige at Season 8 rollover is derived from the player's
all-time wins across Seasons 1–7 (stored in ``user_season_history``).
"""

# Maximum prestige level (hard cap).
MAX_PRESTIGE_LEVEL = 20


def get_prestige_bonus(level):
    """Flat +2% per level. Level 0 → 1.0, Level 20 → 1.40."""
    return level * 0.02


def get_starting_prestige(legacy_wins):
    """Map all-time wins to a starting prestige level at Season 8 rollover.

    | All-time wins | Starting prestige |
    | 0             | 0                 |
    | < 1M          | 1                 |
    | < 100M        | 2                 |
    | < 1B          | 3                 |
    | < 10B         | 4                 |
    | >= 10B        | 5                 |
    """
    if legacy_wins <= 0:
        return 0
    if legacy_wins < 1_000_000:
        return 1
    if legacy_wins < 100_000_000:
        return 2
    if legacy_wins < 1_000_000_000:
        return 3
    if legacy_wins < 10_000_000_000:
        return 4
    return 5


def can_prestige(wins, owned_items, prestige_level):
    """Check whether the player can perform the prestige action.

    Requires ``prestige_unlock`` owned, wins >= 1,000,000 (or 500,000 with
    prestige_efficiency), and prestige_level < MAX_PRESTIGE_LEVEL.
    """
    if 'prestige_unlock' not in owned_items:
        return False, 'Requires Prestige Unlock upgrade'
    if prestige_level >= MAX_PRESTIGE_LEVEL:
        return False, 'Maximum prestige level reached'

    # prestige_efficiency reduces the threshold by 10% per level (max 5 → 50% off)
    efficiency_level = _count_owned(owned_items, 'prestige_efficiency')
    threshold = max(500_000, int(1_000_000 * (1 - 0.10 * efficiency_level)))
    if wins < threshold:
        return False, f'Requires {threshold:,} wins to prestige'

    return True, None


def get_prestige_threshold(owned_items):
    """Return the win threshold needed to prestige, given owned items."""
    efficiency_level = _count_owned(owned_items, 'prestige_efficiency')
    return max(500_000, int(1_000_000 * (1 - 0.10 * efficiency_level)))


def get_legacy_keep_count(owned_items):
    """How many functional upgrades the player can keep on prestige."""
    return _count_owned(owned_items, 'prestige_legacy')


def _count_owned(owned_items, item_id):
    """Count occurrences of item_id in owned_items (for level-based items)."""
    return sum(1 for item in owned_items if item == item_id)
