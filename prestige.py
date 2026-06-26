"""Season 8 prestige system.

Replaces the Season 7 infinite upgrade axes with a flat, non-compounding
bonus capped at level 20. Each prestige level gives +2% base win value.

Starting prestige at Season 8 rollover is derived from the player's
all-time wins across Seasons 1–7 (stored in ``user_season_history``).

T121 (2026-06-26): operator removed ``prestige_efficiency`` and
``prestige_legacy`` from the shop. Wins are no longer retained on prestige
(``compute_wins_kept`` returns 0) and no functional upgrades are carried
over (``get_legacy_keep_count`` returns 0). Players must re-buy their items
after each prestige.
"""

# Maximum prestige level (hard cap).
MAX_PRESTIGE_LEVEL = 20

# The win threshold is a fixed 1,000,000. T86 removed efficiency's ability
# to shorten it; T121 removed efficiency from the shop entirely.
PRESTIGE_WIN_THRESHOLD = 1_000_000

PRESTIGE_LEVEL_MULTIPLIER = 1.05

# Items reset on prestige (subset of the v1 spec). Centralised here so the
# SQL builder and any future tests can read the same source of truth.
# T85 AC#1: every column in this list is zeroed/cleared on prestige.
PRESTIGE_RESET_COLUMNS = (
    'wins',
    'losses',
    'streak',
    'best_streak',
    'spin_count',
    'win_count',
    'loss_count',
    # Infinite-upgrade levels — all retired in favour of flat + Prestige.
    'winmult_inf_level',
    'bonusmult_inf_level',
    'clickmult_inf_level',
    'streak_armor_level',
    'jackpot_resonance_level',
    'echo_amp_level',
    'proc_streak_level',
    'proc_streak',
    'lure_mastery_level',
    # Wager state.
    'wager_streak',
    'wager_last_stake',
    'double_down_pending',
    'wager_banked_wins',
    'wager_banked_losses',
    'wager_insurance_charges',
    'wager_insurance_armed',
    'wager_insurance_last_recharge',
    'wager_last_win_amount',
    # Protection rework state (Season 8).
    'guard_charges',
    'guard_last_regen_spin',
    'resilience_last_use_spin',
    # Dice state.
    'dice_charges',
    'dice_last_recharge',
    'dice_rolled_since_spin',
    'pending_dice',
    # Fishing state.
    'fish_clicks',
    'fishing_cast_at',
    'fishing_bite_at',
    'fishing_lucky_next',
    'caught_species',
    'fastest_catch_pct',
    'fish_exchange_total',
    # Build / mode state.
    'equipped_class',
    'active_wheel_mode',
    'gravity_drift',
    'biggest_win_announced',
    # Bounty tracking (full reset lives in bounty_progress table;
    # bounty_claimed_date is the per-user progress gate).
    'bounty_claimed_date',
)


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

    Requires ``prestige_unlock`` owned, wins >= the level-scaled threshold,
    and prestige_level < MAX_PRESTIGE_LEVEL. T111 makes the threshold scale
    with the player's current prestige level.
    """
    if 'prestige_unlock' not in owned_items:
        return False, 'Requires Prestige Unlock upgrade'
    if prestige_level >= MAX_PRESTIGE_LEVEL:
        return False, 'Maximum prestige level reached'

    threshold = get_prestige_threshold(owned_items, prestige_level)
    if wins < threshold:
        return False, f'Requires {threshold:,} wins to prestige'

    return True, None


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


# Item IDs that are wager-related and must be removed on prestige even if
# they would otherwise qualify as a kept functional upgrade. The spec lists
# the wager subsystem as fully reset on prestige; prestige_legacy only carries
# other functional categories through.
WAGER_ITEM_IDS = frozenset({
    'wager_unlock', 'wager_safety_net', 'wager_hot_streak',
    'wager_double_down', 'wager_insurance',
})


def filter_kept_items(owned_items, keep_count):
    """T85: build the new owned_items list for a prestige reset.

    Keep:
      - every cosmetic item (currency = 'losses'), and
      - up to ``keep_count`` functional items (currency = 'wins'), preserving
        array order so a player who bought items in a deliberate sequence
        sees that sequence carried through.

    Wager-related items are always dropped (they're reset on prestige
    regardless of keep_count). All other functional items are dropped once
    ``keep_count`` slots are filled. The result is suitable to pass straight
    to the ``owned_items`` parameter of the prestige UPDATE.
    """
    if not isinstance(owned_items, (list, tuple)):
        owned_items = list(owned_items or [])
    keep_count = max(0, int(keep_count or 0))
    result = []
    functional_kept = 0
    for item in owned_items:
        if item in WAGER_ITEM_IDS:
            continue
        if _is_cosmetic_item(item):
            result.append(item)
        elif functional_kept < keep_count:
            result.append(item)
            functional_kept += 1
    return result


def _is_cosmetic_item(item_id):
    """True if the item is a cosmetic (fish skin, theme, trail, etc.).

    Uses the ITEM_CURRENCY table from ``models`` to keep the cosmetics set
    in lock-step with the rest of the codebase. T121 retired items
    (prestige_efficiency, prestige_legacy) are explicitly treated as
    functional so they don't accidentally survive a prestige reset if a
    staging player already owns them. Falling back to ``True`` for unknown
    items is intentional — unknown IDs are never purchased so they
    shouldn't survive a reset, but treating them as cosmetic is the safer
    default (a stray cosmetic dropped is invisible; a stray functional
    upgrade kept could be exploited for cheap power).
    """
    try:
        from models import ITEM_CURRENCY, RETIRED_ITEMS
    except Exception:
        return True
    if item_id in RETIRED_ITEMS:
        return False
    return ITEM_CURRENCY.get(item_id, 'losses') == 'losses'
