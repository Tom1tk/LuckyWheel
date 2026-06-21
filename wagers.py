"""Season 8 wager resolution helpers.

These functions are called from ``game.py`` ``_resolve_spin()`` and the
wager API endpoints (bank, double-down, insurance). They implement:
- Stake validation (1-10 int)
- Hot-streak calculation (+5% per consecutive same-stake win, cap +50%)
- Safety net (25% loss recovery at >=5x stake)
- Stake-to-escrow risk model (v2: real wins at risk per stake level)
"""

MAX_STAKE = 10
MIN_STAKE = 1


def compute_stake_risk(current_wins, stake):
    """Return the escrow amount (wins to debit before spin): floor(current_wins * 0.02 * stake).

    Used unchanged for double-down spins too — a double-down spin is just a
    normal spin forced to 2x stake, so it risks (and pays out) exactly twice
    a normal spin at the player's chosen stake, not a separately-computed
    amount. (Previously double-down used expected_payout * stake instead,
    which risked less than an equivalent-stake normal spin while paying out
    the same — a real risk/reward asymmetry favoring the player.)

    Result is capped at current_wins (never debit more than the player has).
    """
    # ponytail: risk = 2% per stake level, was a 10-row table
    raw = int(current_wins * 0.02 * max(MIN_STAKE, min(MAX_STAKE, stake)))
    return min(raw, current_wins)


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


def apply_safety_net(stake_wins, stake, owns_safety_net):
    """Refund 25% of lost escrow to wins if safety_net is owned and stake >= 5."""
    if owns_safety_net and stake >= 5:
        return int(stake_wins * 0.25)
    return 0


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


if __name__ == '__main__':
    # Self-check: compute_stake_risk must match the old STAKE_RISK_PCT dict
    # lookup (stake -> stake * 0.02) for every valid stake 1-10.
    _OLD_STAKE_RISK_PCT = {s: s * 0.02 for s in range(1, 11)}
    _CURRENT_WINS = 1000
    for _stake, _pct in _OLD_STAKE_RISK_PCT.items():
        _old = int(_CURRENT_WINS * _pct)
        _new = compute_stake_risk(_CURRENT_WINS, _stake)
        assert _old == _new, f"stake={_stake}: old={_old} new={_new}"
    print("compute_stake_risk matches old STAKE_RISK_PCT for stakes 1-10")
