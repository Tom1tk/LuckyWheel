"""Season 8 prestige system.

Replaces the Season 7 infinite upgrade axes with a flat, non-compounding
bonus capped at level 20. Each prestige level gives +2% base win value.

T121 (2026-06-26): operator removed ``prestige_efficiency`` and
``prestige_legacy`` from the shop. Wins are no longer retained on prestige
(``compute_wins_kept`` returns 0) and no functional upgrades are carried
over (``get_legacy_keep_count`` returns 0).
"""

# Maximum prestige level (hard cap).
MAX_PRESTIGE_LEVEL = 20

# The win threshold is a fixed 1,000,000. T86 removed efficiency's ability
# to shorten it; T121 removed efficiency from the shop entirely.
PRESTIGE_WIN_THRESHOLD = 1_000_000

PRESTIGE_LEVEL_MULTIPLIER = 1.05


def get_prestige_bonus(level):
    """Flat +2% per level. Level 0 → 1.0, Level 20 → 1.40."""
    return level * 0.02


def get_prestige_threshold(owned_items, prestige_level=0):
    """Return the win threshold needed to prestige at ``prestige_level``.

    T111: threshold scales by ``PRESTIGE_LEVEL_MULTIPLIER`` per current
    level, so reaching higher levels costs more wins. Level 0 stays at
    the T86 base of 1,000,000 (unchanged for new players). The
    multiplier value is preliminary and will be tuned after playtesting.
    """
    return round(PRESTIGE_WIN_THRESHOLD * (PRESTIGE_LEVEL_MULTIPLIER ** prestige_level))


def get_legacy_keep_count(owned_items):
    """T121: retired. No functional upgrades are kept on prestige —
    players must re-buy their items after each prestige.
    """
    return 0


def compute_wins_kept(wins, owned_items):
    """T121: retired. ``prestige_efficiency`` no longer exists, so wins
    are fully reset to 0 on prestige. The ``legacy_wins`` column carries
    the prior total forward (see game.py:prestige_reset).
    """
    return 0
