"""Season 8 wager resolution helpers (T102: flat-percentage redesign).

These functions are called from ``game.py`` ``_resolve_spin()`` and the
wager API endpoints (bank, double-down, insurance). They implement:
- Stake validation (0-45 percentage in 5% steps, 0% = safe)
- Hot-streak calculation (+5% per consecutive same-stake win, cap +50%)
- Safety net (25% loss recovery at >=15% stake)
- Stake-to-escrow risk model (T102: flat percentage of current wins/losses)
- DD-aware loss-mitigation gating (T103 placeholder, NO-OP for T102)
"""
from datetime import timezone, timedelta


# T102: flat-percentage system
MIN_STAKE_PCT = 0
BASE_MAX_STAKE_PCT = 30
STAKE_PCT_STEP = 5
STAKE_EXTENSION_ITEMS = ('wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3')

# T110: wager tokens are spent on "high-stake" spins (above 5x in the
# original spec, mapped to >= 30% in the flat-percentage system — the
# baseline max). The Pay-with-tokens toggle is only available at this
# stake or above.
HIGH_STAKE_TOKEN_THRESHOLD = 30

# ── Season 9: stake decay ──────────────────────────────────────────────────────
# As a player's balance grows, their max stake % decays so the compounding
# wager engine can't run away (Season 8 postmortem: dylan hit 1e38 wins).
# The decay is tiered by current wins; each band subtracts from the item-based
# max (30 base + 5 per extension = 30/35/40/45). A floor of 10% keeps the
# wager system usable at any balance.
STAKE_DECAY_TABLE = (
    (1_000_000,        0),   # < 1M:   no decay
    (10_000_000,       5),   # 1M-10M:  −5
    (100_000_000,     10),   # 10M-100M: −10
    (1_000_000_000,   15),   # 100M-1B: −15
    (float('inf'),    20),   # >= 1B:   −20 (floor 10)
)
STAKE_DECAY_FLOOR = 10


def compute_max_stake_pct(owned_items, wins=0):
    """T102+T104: 30% base + 5% per stake extension item owned (max 45%).

    Season 9 (T4): the item-based max decays as the player's current wins
    grow (see STAKE_DECAY_TABLE) so runaway compounding is bounded. `wins`
    defaults to 0 → no decay (preserves the pre-S9 behaviour for callers
    that don't pass a balance).

    Args:
        owned_items: list/iterable of item ids the player owns.
        wins: current wins balance (0 = no decay).

    Returns:
        int — the max stake percentage this player can set (10..45).
    """
    owned = set(owned_items) if owned_items else set()
    extend_count = sum(1 for item in STAKE_EXTENSION_ITEMS if item in owned)
    base = BASE_MAX_STAKE_PCT + (extend_count * STAKE_PCT_STEP)
    try:
        wins = int(wins)
    except (TypeError, ValueError):
        wins = 0
    if wins <= 0:
        return base
    decay = 0
    for threshold, penalty in STAKE_DECAY_TABLE:
        if wins < threshold:
            decay = penalty
            break
    else:
        decay = STAKE_DECAY_TABLE[-1][1]
    return max(STAKE_DECAY_FLOOR, base - decay)


# ── Season 9: vault payout cap ────────────────────────────────────────────────
# A winning spin's wins_delta is capped once the player holds >= 1M wins.
# Overflow is NOT lost — it is moved to wager_banked_wins (the "vault") and
# claimed via the Bank button. This keeps scoreboards readable (Season 8's
# "pascal win number" problem) without confiscating winnings.
PAYOUT_CAP_MIN_WINS = 1_000_000
PAYOUT_CAP_MULT     = 2


def compute_payout_cap(pre_spin_wins):
    """Return the max wins_delta a single winning spin may add.

    Applies once `pre_spin_wins >= PAYOUT_CAP_MIN_WINS`; below that the cap
    is unlimited (no change to the pre-S9 economy for normal players).
    """
    try:
        pre_spin_wins = int(pre_spin_wins)
    except (TypeError, ValueError):
        pre_spin_wins = 0
    if pre_spin_wins < PAYOUT_CAP_MIN_WINS:
        return None
    return max(PAYOUT_CAP_MIN_WINS, pre_spin_wins * PAYOUT_CAP_MULT)


def compute_stake_risk(current_amount, stake_pct, max_stake_pct=None):
    """T102: return the escrow amount: int(current_amount * stake_pct / 100), capped at current_amount.

    Args:
        current_amount: current wins (normal mode) or current losses (inverted mode)
        stake_pct: the percentage (0-45)
        max_stake_pct: the player's max stake percentage (30/35/40/45) for clamping

    Returns:
        int — the wins/losses to debit before the spin. Returns 0 if stake_pct==0
        or current_amount==0 or stake_pct > max_stake_pct.
    """
    if stake_pct <= 0 or current_amount <= 0:
        return 0
    if max_stake_pct is not None and stake_pct > max_stake_pct:
        stake_pct = max_stake_pct
    return int(max(0, current_amount) * stake_pct / 100)


def validate_stake(stake_pct, owns_wager_unlock, max_stake_pct=BASE_MAX_STAKE_PCT):
    """T102: validate and clamp stake_pct to [0, max_stake_pct], rounded to nearest 5%.

    If the player doesn't own ``wager_unlock``, returns 0.
    """
    if not owns_wager_unlock:
        return 0
    if not isinstance(stake_pct, (int, float)):
        try:
            stake_pct = int(stake_pct)
        except (TypeError, ValueError):
            return 0
    stake_pct = int(stake_pct)
    if stake_pct < 0:
        return 0
    if stake_pct > max_stake_pct:
        stake_pct = max_stake_pct
    # Snap to nearest step
    if stake_pct % STAKE_PCT_STEP != 0:
        stake_pct = round(stake_pct / STAKE_PCT_STEP) * STAKE_PCT_STEP
        if stake_pct > max_stake_pct:
            stake_pct = max_stake_pct
    return stake_pct


def compute_stake_value(wins, losses, stake_pct, owns_wager_unlock, is_inverted,
                        dd_active, wager_last_win_amount):
    """T102+T105: return the wins/losses that would be escrowed on the next spin.

    Returns 0 if:
    - stake_pct == 0
    - not owns_wager_unlock (and not in inverted mode where unlock is not required)
    - DD is armed but wager_last_win_amount == 0 (no prior win to risk)

    For DD: returns wager_last_win_amount (sidesteps the percentage system).
    Otherwise: returns int(wins_or_losses * stake_pct / 100).
    """
    if dd_active and wager_last_win_amount > 0:
        return wager_last_win_amount
    if stake_pct == 0:
        return 0
    owns_wager_unlock_eff = True if is_inverted else owns_wager_unlock
    if not owns_wager_unlock_eff:
        return 0
    base = losses if is_inverted else wins
    return int(max(0, base) * stake_pct / 100)


# Unchanged from before:
def compute_hot_streak_bonus(wager_streak, owns_hot_streak):
    if not owns_hot_streak:
        return 0.0
    return min(wager_streak * 0.05, 0.50)


def should_reset_streak(current_stake, last_stake):
    return last_stake != 0 and current_stake != last_stake


def apply_safety_net(stake_value, stake_pct, owns_safety_net):
    """T102: safety net refunds 25% of stake_value on a loss at >=15% stake."""
    if owns_safety_net and stake_pct >= 15:
        return int(stake_value * 0.25)
    return 0


def compute_wager_payout(payout, hot_streak_bonus):
    """Return (direct_wins, banked_wins).

    T102 (user redesign 2026-06-23): the payout is the NET win amount
    (stake_wins for stake > 0%, base_payout for 0%). The hot_streak_bonus
    is applied multiplicatively to the payout; the bonus portion is banked
    (legacy mechanic — kept per user "Keep bank button and bank the hot
    streak bonus separately" decision 2026-06-23).

    Spec example (100 wins, 10% stake, win):
      - payout = 10 (the wager)
      - with hot_streak_bonus 0.25: total = int(10 * 1.25) = 12
      - direct = 10 (added to wins)
      - banked = 2 (added to wager_banked_wins, claimable via /api/wager/bank)
    """
    total = int(payout * (1 + hot_streak_bonus))
    direct = int(payout)
    return direct, total - direct


def compute_wager_loss(base_loss, effective_stake):
    """Loss multiplier on the base_loss (e.g. for inverted-mode loss-farming).

    T102: at stake > 0% the per-spin loss is just the wager (stake_wins
    forfeited on loss). The caller in game.py short-circuits to 0 when
    stake_wins > 0 so the OLD behavior (base_loss * effective_stake which
    truncates to 0 at 0.10 effective_stake) is preserved. For 0% stake
    (no escrow) the OLD behavior is preserved: base_loss * 1 = base_loss.
    """
    return int(base_loss * effective_stake)


def _aware(dt_val):
    if dt_val is not None and dt_val.tzinfo is None:
        return dt_val.replace(tzinfo=timezone.utc)
    return dt_val


if __name__ == '__main__':
    # Self-check: compute_stake_risk matches direct percentage math
    assert compute_stake_risk(1000, 0) == 0
    assert compute_stake_risk(1000, 5) == 50
    assert compute_stake_risk(1000, 10) == 100
    assert compute_stake_risk(1000, 30) == 300
    assert compute_stake_risk(0, 30) == 0
    assert compute_stake_risk(1000, 50, max_stake_pct=45) == 450
    assert compute_stake_risk(1000, 30, max_stake_pct=30) == 300
    # compute_max_stake_pct
    assert compute_max_stake_pct([]) == 30
    assert compute_max_stake_pct(['wager_stake_extend_1']) == 35
    assert compute_max_stake_pct(['wager_stake_extend_1', 'wager_stake_extend_2']) == 40
    assert compute_max_stake_pct(['wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3']) == 45
    # Season 9: stake decay (wealth-adaptive max stake)
    assert compute_max_stake_pct([], 0) == 30
    assert compute_max_stake_pct([], 999_999) == 30          # below 1M: no decay
    assert compute_max_stake_pct([], 1_000_000) == 25        # 1M-10M: −5
    assert compute_max_stake_pct([], 10_000_000) == 20       # 10M-100M: −10
    assert compute_max_stake_pct([], 100_000_000) == 15      # 100M-1B: −15
    assert compute_max_stake_pct([], 1_000_000_000) == 10    # >= 1B: −20 → floor 10
    assert compute_max_stake_pct([], 1e40) == 10             # floor holds at any scale
    assert compute_max_stake_pct(['wager_stake_extend_1'], 1_000_000) == 30
    assert compute_max_stake_pct(['wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3'], 1e40) == 25
    # Season 9: vault payout cap
    assert compute_payout_cap(0) is None
    assert compute_payout_cap(999_999) is None               # below 1M: uncapped
    assert compute_payout_cap(1_000_000) == 2_000_000        # ≥1M → ×2 (never below floor)
    assert compute_payout_cap(2_000_000) == 4_000_000        # ×2
    assert compute_payout_cap(1e20) == 2e20
    # validate_stake
    assert validate_stake(10, True, 30) == 10
    assert validate_stake(13, True, 30) == 15  # snap to 5% step
    assert validate_stake(50, True, 45) == 45  # clamp
    assert validate_stake(10, False, 30) == 0  # no unlock
    # compute_stake_value
    assert compute_stake_value(1000, 0, 0, True, False, False, 0) == 0
    assert compute_stake_value(1000, 0, 10, True, False, False, 0) == 100
    assert compute_stake_value(1000, 0, 10, True, False, True, 5000) == 5000
    assert compute_stake_value(0, 1000, 10, True, True, False, 0) == 100
    # T102: compute_wager_payout (payout, hot_streak_bonus) — the bonus portion is banked
    direct, banked = compute_wager_payout(10, 0.0)   # no hot streak: all goes to direct
    assert direct == 10 and banked == 0
    direct, banked = compute_wager_payout(10, 0.25)  # 25% hot streak: 2.5 banked (rounds down)
    assert direct == 10 and banked == 2
    direct, banked = compute_wager_payout(10, 0.50)  # 50% hot streak: 5 banked
    assert direct == 10 and banked == 5
    direct, banked = compute_wager_payout(0, 0.25)   # 0 payout → all zero
    assert direct == 0 and banked == 0
    print("wagers.py self-check passed")
