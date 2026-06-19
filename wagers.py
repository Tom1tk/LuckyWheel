"""Season 8 wager resolution helpers.

These functions are called from ``game.py`` ``_resolve_spin()`` and the
wager API endpoints (bank, double-down, insurance). They implement:
- Stake validation (1-10 int)
- Hot-streak calculation (+5% per consecutive same-stake win, cap +50%)
- Safety net (25% loss recovery at >=5x stake)
"""

MAX_STAKE = 10
MIN_STAKE = 1


def validate_stake(stake, owns_wager_unlock):
    """Validate and clamp the stake to 1-10.

    If the player doesn't own ``wager_unlock``, stake is forced to 1.
    """
    if not owns_wager_unlock:
        return 1
    if not isinstance(stake, int):
        try:
            stake = int(stake)
        except (TypeError, ValueError):
            return 1
    return max(MIN_STAKE, min(MAX_STAKE, stake))


def compute_hot_streak_bonus(wager_streak, owns_hot_streak):
    """Return the hot-streak multiplier bonus as a fraction.

    +5% per consecutive same-stake win, capped at +50% (10 streak).
    Returns 0.0 if ``wager_hot_streak`` is not owned.
    """
    if not owns_hot_streak:
        return 0.0
    return min(wager_streak * 0.05, 0.50)


def should_reset_streak(current_stake, last_stake):
    """Whether the wager streak resets because the stake changed."""
    return last_stake != 0 and current_stake != last_stake


def apply_safety_net(base_loss, stake, owns_safety_net):
    """Reduce loss by 25% if safety_net is owned and stake >= 5."""
    if owns_safety_net and stake >= 5:
        return int(base_loss * 0.75)
    return base_loss


def compute_wager_payout(base_payout, stake, hot_streak_bonus):
    """Return (direct_wins, banked_wins).

    The base payout (no hot-streak bonus) goes to wins directly.
    The hot-streak bonus portion goes to wager_banked_wins (at risk).
    """
    total = int(base_payout * stake * (1 + hot_streak_bonus))
    base = int(base_payout * stake)
    return base, total - base


def compute_wager_loss(base_loss, stake):
    """Multiply base loss by stake."""
    return base_loss * stake
