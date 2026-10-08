import datetime as dt
import hmac
import logging
import os
import random
from datetime import timezone, timedelta

import psycopg2.extras
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import db_connection
from extensions import limiter, csrf
from models import (REGEN_SHIELD_RECHARGE_WINS,
                    GUARD_CHARGE_RECHARGE_SPINS, GUARD_CHARGE_MAX,
                    lure_mastery_mult,
                    CLASS_EARTH_FISH_BONUS, CLASS_MOON_PROC_BONUS, CLASS_STAR_WIN_BONUS,
                    streak_bonus, dice_max_charges,
                    roll_fish, fish_value, autofisher_catch_rate,
                    AUTO_SPIN_INTERVAL_SECONDS, MAX_SPINS_PER_TICK, CATCH_UP_THRESHOLD,
                    AUTO_SPIN_OFFLINE_CAP_S,
                    AUTO_FISH_INTERVAL_SECONDS, MAX_FISH_CATCHUP_TICKS, FISH_CATCHUP_THRESHOLD,
                    HAPPY_HOUR_START_UTC, HAPPY_HOUR_END_UTC,
                    RETIRED_S9_ITEMS)
from seasons import ensure_current_season, get_season_info, get_latest_winners, advance_season
from security import require_json
from wagers import (validate_stake, compute_hot_streak_bonus, should_reset_streak,
                    apply_safety_net, compute_wager_payout, compute_wager_loss,
                    compute_stake_risk, compute_max_stake_pct,
                    HIGH_STAKE_TOKEN_THRESHOLD)
from wheel_modes import WHEEL_MODES, get_available_modes, get_week_number, compute_gravity_probabilities, clamp_gravity_drift
from prestige import (get_prestige_bonus, get_prestige_threshold, MAX_PRESTIGE_LEVEL)
from bounties import increment_bounty, get_bounty_status, get_claim_rewards_for_bounty
from community_goals import get_active_goal, increment_goal, check_goal_completion, get_player_contribution
from chat import post_system_message, post_dedup_system_message
import chat_triggers
import dice
import fish
import shop
import loadout
from fish import (
    lure_level, autofisher_level, get_total_fish_clicks,
)


def is_happy_hour(now_utc=None):
    now = now_utc or dt.datetime.now(timezone.utc)
    return HAPPY_HOUR_START_UTC <= now.hour < HAPPY_HOUR_END_UTC


def _aware(dt_val):
    """Ensure a datetime from psycopg2 has UTC tzinfo (psycopg2 returns naive datetimes)."""
    if dt_val is not None and dt_val.tzinfo is None:
        return dt_val.replace(tzinfo=timezone.utc)
    return dt_val


log = logging.getLogger('wheel')
game_bp = Blueprint('game', __name__)

# ── Game state loader ──────────────────────────────────────────────────────
# Union of all columns needed by spin, tick, and buy endpoints. Defining the
_GAME_STATE_SQL = '''
    SELECT wins, losses, streak, best_streak, owned_items, regen_recharge_wins,
           spin_count, win_count, loss_count, cumulative_wins,
           winmult_inf_level, bonusmult_inf_level, streak_armor_level,
           jackpot_resonance_level, echo_amp_level, proc_streak_level, proc_streak,
           lure_mastery_level, equipped_class, fish_clicks, caught_species, active_cosmetics,
           dice_charges, dice_last_recharge, jackpot_echo_next, dice_rolled_since_spin,
           pending_dice, auto_spin_since, last_spin_at, active_tab_id, tab_last_seen,
           auto_fish_enabled, auto_fish_last_tick,
           prestige_level, prestige_count, legacy_wins, onboarding_step,
           wager_streak, wager_last_stake, double_down_pending, wager_banked_wins,
           insurance_charges, insurance_armed, active_wheel_mode,
           insurance_tokens, aquarium_species, cosmetic_fragments,
           guard_charges, guard_last_regen_spin, resilience_last_use_spin,
           bounty_claimed_date, biggest_win_announced,
           wager_last_win_amount, wager_banked_losses,
           insurance_free_claimed_date, insurance_unlock_grant_given,
           gravity_drift
    FROM game_state WHERE user_id = %s
'''


def _load_game_state(cur, user_id: int, *, for_update: bool = False):
    sql = _GAME_STATE_SQL + ('FOR UPDATE' if for_update else '')
    cur.execute(sql, (user_id,))
    return cur.fetchone()


def _maybe_announce_big_win(conn, gs, events, username, user_id, *, skip_message=False):
    """T83: Post a big-win chat message if this win strictly exceeds the
    player's previous biggest_win_announced, and return the value to persist
    in the same transaction (caller writes it to game_state). Returns the
    unchanged previous biggest when the message does not fire.

    T209: uses post_dedup_system_message so a player can only have one
    big_win chat message at a time.

    T221: jackpots are excluded entirely. A jackpot no longer triggers a
    chat message of any kind — neither the was_jackpot big_win nor any
    other format. Only regular wins above the threshold post.

    T230: skip_message=True suppresses the chat message while still
    updating biggest_win_announced. Used when the caller has already
    posted a merged double-down/big-win message — that message already
    conveys the big-win info, so a separate big_win would be a duplicate.
    """
    biggest = int(gs.get('biggest_win_announced', 0) or 0)
    wins_delta = int(events.get('wins_delta', 0) or 0)
    if (events.get('result') == 'win'
            and wins_delta >= chat_triggers.BIG_WIN_THRESHOLD
            and wins_delta > biggest):
        if not skip_message:
            post_dedup_system_message(
                conn,
                chat_triggers.big_win_msg(
                    username,
                    wins_delta,
                    events.get('active_wheel_mode', 'steady'),
                ),
                user_id,
                event_kind='big_win',
            )
        return wins_delta
    return biggest


# ── Upgrade-level helpers (spin path only — fishing helpers live in fish.py)

def _winmult_level(owned: list) -> int:
    for lvl in range(7, 0, -1):
        if f'winmult_{lvl}' in owned:
            return lvl
    return 0


# bonus_mult_from_level (removed in the T46 cleanup) used this exact table.
_BONUS_MULT_TABLE = [1, 2, 4, 8, 15, 35, 70]


def _bonusmult_level(owned: list) -> int:
    for lvl in range(6, 0, -1):
        if f'bonusmult_{lvl}' in owned:
            return lvl
    return 0


def _build_spin_context(gs: dict) -> dict:
    """Compute immutable per-request spin context from game state. Shared by spin() and tick()."""
    equipped_class = gs['equipped_class']
    moon_bonus = CLASS_MOON_PROC_BONUS if equipped_class == 'moon' else 0.0
    star_win_bonus = CLASS_STAR_WIN_BONUS if equipped_class == 'star' else 0.0
    # Season 8: prestige bonus is flat +2% per level (max +40% at level 20)
    prestige_bonus = get_prestige_bonus(gs.get('prestige_level', 0))
    # Season 8: aquarium luck bonus — +0.1% per unique species.
    # aquarium_species (DB column) is never written anywhere — the aquarium
    # mirrors the Fish Encyclopaedia's caught_species instead, which already
    # tracks the same "unique species ever caught" fact correctly.
    aquarium_species = gs.get('caught_species', [])
    aquarium_count = len(aquarium_species) if aquarium_species else 0
    aquarium_luck = aquarium_count * 0.001 if 'aquarium' in gs.get('owned_items', []) else 0.0

    # Season 8: old *infinite* levels (winmult_inf/bonusmult_inf) are frozen at
    # 0 and no longer read — replaced by the flat winmult_1-7/bonusmult_1-6
    # shop items, capped (no infinite tail).
    owned = gs.get('owned_items', [])
    base_win_mult = 1 << _winmult_level(owned)            # 1, 2, 4, ..., 128
    base_bonus_mult = _BONUS_MULT_TABLE[_bonusmult_level(owned)]  # 1, 2, 4, 8, 15, 35, 70

    return {
        'effective_win_mult': base_win_mult * (1.0 + star_win_bonus) * (1.0 + prestige_bonus),
        'bonus_mult':         base_bonus_mult,
        'jackpot_chance':     0.01 + moon_bonus,  # flat 1% base (resonance removed)
        'echo_chance':        0.20 + moon_bonus,  # flat 20% base (echo_amp removed)
        'charm_chance':       0.25 + moon_bonus,
        'resilience_chance':  min(0.50 + moon_bonus, 0.65),  # flat 50% (streak_armor removed)
        'proc_streak_level':  0,  # frozen
        'aquarium_luck':      aquarium_luck,
        'prestige_bonus':     prestige_bonus,
    }


def _current_wheel_probabilities(active_wheel_mode: str, gravity_drift: int = 0) -> dict:
    """T77 AC#4: return the wheel probabilities the player is currently facing.

    For gravity mode this is the drift-adjusted set; all other modes return
    their static WHEEL_MODES values. Used by /api/state and the spin
    response so the frontend can redraw the wheel correctly after every
    spin (gravity drift shifts after each resolve).
    """
    if active_wheel_mode == 'gravity':
        return compute_gravity_probabilities(gravity_drift)
    mode = WHEEL_MODES.get(active_wheel_mode, WHEEL_MODES['steady'])
    return {
        'win_pct':     mode['win_pct'],
        'lose_pct':    mode['loss_pct'],
        'jackpot_pct': mode['jackpot_pct'],
    }


def _resolve_spin(
    owned: list,
    streak: int,
    best_streak: int,
    regen_recharge_wins: int,
    wins: int,
    losses: int,
    jackpot_echo_next: bool,
    spin_count: int,        # already incremented for this spin
    active_cosmetics: list,
    proc_streak: int,
    # ── immutable per-session context ──
    effective_win_mult: float,
    bonus_mult: int,
    jackpot_chance: float,
    echo_chance: float,
    charm_chance: float,
    resilience_chance: float,
    proc_streak_level: int,
    pot_active: bool,
    pot_win_pct: float,     # fraction 0–1
    # ── Season 8: wager + wheel mode ──
    stake_pct: int = 0,
    wager_streak: int = 0,
    wager_last_stake: int = 0,
    active_wheel_mode: str = 'steady',
    aquarium_luck: float = 0.0,
    wager_banked_wins: int = 0,
    insurance_active: bool = False,
    # ── T73: double-down escrow uses last actual win amount ──
    double_down_active: bool = False,
    wager_last_win_amount: int = 0,
    # ── T77: gravity mode drift ──
    gravity_drift: int = 0,
    # ── T79: inverted mode tracks banked losses ──
    wager_banked_losses: int = 0,
    # ── T110: insurance-token spend (1:1 with the wins cost). T119
    # renamed the column wager_tokens → insurance_tokens; the function
    # parameter follows the new name.
    insurance_tokens: int = 0,
    pay_with_tokens: bool = False,
) -> tuple[dict, dict]:
    """Resolve one spin. Returns (new_state, events). Does not mutate inputs.

    v2 (T45): stake_wins is escrowed from wins before outcome determination.
    On a win the escrow is returned plus payout; on a loss the escrow is
    forfeited.  Safety net now refunds a portion of lost escrow, not losses.

    T77: gravity mode uses drift-adjusted probabilities and updates drift
    after each spin based on outcome (win/jackpot +10, loss -10, clamped to
    [-35, +35]).

    T79: inverted mode is loss-farming. The 'lose' outcome is GOOD — it
    refunds a staked-losses escrow and adds the loss-farming payout. The
    'win' outcome is BAD — it forfeits the escrow, still gives wins (which
    the player doesn't want), and triggers shield/guard/resilience. The
    'jackpot' outcome is SUPER-GOOD — refund + 5x the loss-farming payout.
    """
    original_wins   = wins
    original_losses = losses
    original_wager_banked_wins = wager_banked_wins
    original_wager_banked_losses = wager_banked_losses
    original_gravity_drift = gravity_drift

    # Season 8: auto_guard removed — no auto-purchase logic
    auto_guard_failed = False

    # Season 8: wheel mode outcome determination (replaces singularity/50-50)
    lucky_seven_triggered = False
    mode = WHEEL_MODES.get(active_wheel_mode, WHEEL_MODES['steady'])
    is_inverted = (active_wheel_mode == 'inverted')

    # T77: gravity mode replaces the static mode probabilities with
    # drift-adjusted values. Other modes use their static WHEEL_MODES entry.
    if active_wheel_mode == 'gravity':
        probs = compute_gravity_probabilities(gravity_drift)
    else:
        probs = {
            'win_pct':     mode['win_pct'],
            'lose_pct':    mode['loss_pct'],
            'jackpot_pct': mode['jackpot_pct'],
        }

    if 'lucky_seven' in owned and spin_count % 7 == 0:
        outcome = 'win'
        lucky_seven_triggered = True
    elif pot_active:
        outcome = 'win' if random.random() < (pot_win_pct + aquarium_luck) else 'lose'
    else:
        # Mode-based probability roll
        win_pct = probs['win_pct'] / 100.0 + aquarium_luck
        jackpot_pct = probs['jackpot_pct'] / 100.0
        roll = random.random()
        if roll < jackpot_pct:
            outcome = 'jackpot'
        elif roll < jackpot_pct + win_pct:
            outcome = 'win'
        else:
            outcome = 'lose'
        # Mirror mode: roll twice, take better
        if active_wheel_mode == 'mirror':
            roll2 = random.random()
            if roll2 < jackpot_pct:
                outcome2 = 'jackpot'
            elif roll2 < jackpot_pct + win_pct:
                outcome2 = 'win'
            else:
                outcome2 = 'lose'
            rank = {'jackpot': 2, 'win': 1, 'lose': 0}
            if rank[outcome2] > rank[outcome]:
                outcome = outcome2

    jackpot_echo_pending  = jackpot_echo_next
    new_jackpot_echo_next = False

    shield_used             = False
    shield_used_type        = None
    guard_triggered         = False
    guard_blocked           = False
    echo_triggered          = False
    jackpot_hit             = False
    jackpot_echo_triggered  = False
    resilience_triggered    = False
    fortune_charm_triggered = False
    insurance_used          = False
    bonus_earned            = 0
    new_owned               = owned
    # T73: tracks the latest `direct_wins` (base portion) so we can record it
    # as wager_last_win_amount on every winning outcome.
    last_direct_wins        = 0

    # Season 8: wager stake percentage and hot streak
    owns_wager_unlock = 'wager_unlock' in owned
    # T79 AC#10: inverted mode does NOT require wager_unlock — the stake
    # slider is fully functional without it. Treat the player as if they own
    # wager_unlock for stake validation + escrow purposes.
    owns_wager_unlock_eff = True if is_inverted else owns_wager_unlock
    # T102: max stake is 30% base + 5% per stake extension item owned (max 45%).
    max_stake_pct = compute_max_stake_pct(owned)
    actual_stake = validate_stake(stake_pct, owns_wager_unlock_eff, max_stake_pct)
    owns_hot_streak = 'wager_hot_streak' in owned
    if should_reset_streak(actual_stake, wager_last_stake):
        wager_streak = 0
    hot_streak_bonus = compute_hot_streak_bonus(wager_streak, owns_hot_streak)

    stake_wins = 0
    stake_losses = 0
    # T110: token-spend is only valid at high stake (>= HIGH_STAKE_TOKEN_THRESHOLD).
    # The /api/spin handler validates the request flag, but we re-check here so the
    # function is safe to call directly from tests/other paths. DD armed uses
    # wager_last_win_amount, not the percentage system, so tokens don't apply.
    # `stake_cost_total` is the FULL stake cost (in wins/losses), used for the
    # payout/loss calculation. After token-spend, `stake_wins` is reduced to
    # the cash portion only; the wager refund / payout still uses the full
    # `stake_cost_total` so the player gets credit for the tokens they spent.
    stake_cost_total = 0
    tokens_spent = 0
    token_spend_eligible = (
        pay_with_tokens
        and actual_stake >= HIGH_STAKE_TOKEN_THRESHOLD
        and not double_down_active
        and insurance_tokens > 0
    )
    if is_inverted:
        # T102: stake_losses = int(current_losses * stake_pct / 100), capped
        # at current_losses. Debited from losses immediately.
        stake_losses = compute_stake_risk(losses, actual_stake, max_stake_pct)
        # T73 integration: double-down escrows the last loss-gain (tracked in
        # wager_last_win_amount) from losses, mirroring the normal-mode flow
        # but with losses as the escrow source.
        if double_down_active and owns_wager_unlock_eff and wager_last_win_amount > 0:
            stake_losses = wager_last_win_amount
        stake_cost_total = stake_losses
        # T102: effective_stake is a fraction 0.0-0.45 (stake_pct / 100).
        # When there's no escrow (stake=0 or no losses to risk), it collapses
        # to 1.0 so payout/loss are computed at base (the safe position still
        # gives a base payout per spec AC#9: "win returns 0 + base_payout × 1").
        effective_stake = actual_stake / 100.0 if stake_cost_total > 0 else 1.0
        # T110: cover (part of) the stake with tokens; reduce the cash debit
        # by the same amount. 1:1 rate — see HIGH_STAKE_TOKEN_THRESHOLD.
        if token_spend_eligible and stake_losses > 0:
            tokens_spent = min(insurance_tokens, stake_losses)
            insurance_tokens -= tokens_spent
            stake_losses -= tokens_spent
        losses -= stake_losses
    else:
        # v2 (T45): escrow stake before outcome — real wins are now at risk.
        # Only for players who own wager_unlock; without it, stake is locked to 0
        # (above) and there must be zero escrow/risk, matching base game behavior.
        stake_wins = compute_stake_risk(wins, actual_stake, max_stake_pct) if owns_wager_unlock else 0
        # T78: mirror mode doubles the escrow (2× stake_wins debited; full refund
        # on a win, full forfeit on a double-loss). Insurance, when armed, still
        # returns the full doubled escrow and caps the loss at the player's stake.
        if active_wheel_mode == 'mirror' and owns_wager_unlock:
            stake_wins = stake_wins * 2
        # T73: double-down escrows the *previous* payout (wager_last_win_amount),
        # not the standard stake_pct / 100 risk. If the player has no prior win to
        # risk, double-down is a no-op (per AC#7) — stake_wins stays at the
        # normal computed value (or 0).
        if double_down_active and owns_wager_unlock and wager_last_win_amount > 0:
            stake_wins = wager_last_win_amount
        stake_cost_total = stake_wins
        # T102: when there is no escrow (player lacks wager_unlock, or stake=0,
        # or current_wins is so low the percentage risk floors to 0), the stake
        # multiplier must collapse to 1.0 so payout/loss are computed at base
        # (the safe position still gives a base payout per spec AC#9).
        effective_stake = actual_stake / 100.0 if stake_cost_total > 0 else 1.0
        # T110: cover (part of) the stake with tokens; reduce the cash debit
        # by the same amount. 1:1 rate — see HIGH_STAKE_TOKEN_THRESHOLD.
        if token_spend_eligible and stake_wins > 0:
            tokens_spent = min(insurance_tokens, stake_wins)
            insurance_tokens -= tokens_spent
            stake_wins -= tokens_spent
        wins -= stake_wins

    # ── T79: inverted mode outcome handling ──
    # In inverted mode the 'lose' outcome is GOOD and the 'win' outcome is
    # BAD. The bookkeeping is mirrored: stake comes from losses instead of
    # wins, payouts go to losses instead of wins. The 'jackpot' outcome is
    # SUPER-GOOD (5× multiplier on the loss-farming payout).
    inverted_handled = False
    if is_inverted:
        if outcome == 'lose':
            # T79 AC#3: GOOD outcome — loss-farming payout.
            # T102 (user redesign): payout = stake_losses (the wager), no
            # base_loss * effective_stake multiplication. The wager is debited
            # from losses, then refunded + matching payout added on 'lose' (good).
            # Hot streak bonus is applied multiplicatively to the wager and
            # banked (legacy mechanic, per user "Keep bank button" 2026-06-23).
            # wager_streak increments; banked_losses accumulates the bonus.
            new_streak = streak - 1 if streak <= 0 else -1
            loss_count = abs(new_streak) if new_streak < 0 else 0
            loss_bonus = streak_bonus(loss_count) * bonus_mult
            # T102: payout = stake_losses (the wager) + loss_bonus added to NET.
            # T110: use stake_cost_total (pre-token-spend) so a token-funded
            # spin still gets the loss-farming payout.
            net_payout = stake_cost_total + loss_bonus
            direct_losses, banked_losses_payout = compute_wager_payout(net_payout, hot_streak_bonus)
            # Refund the escrow, then add the loss-farming payout.
            losses += stake_cost_total
            losses += direct_losses
            wager_banked_losses += banked_losses_payout
            # T79 AC#8: wager_last_win_amount tracks the last loss-gain
            # amount (used by double-down's escrow on the next spin).
            wager_last_win_amount = direct_losses + banked_losses_payout
            # wager_streak increments (same-stake rule).
            if actual_stake == wager_last_stake or wager_last_stake == 0:
                wager_streak += 1
            else:
                wager_streak = 1
            bonus_earned = -loss_bonus if loss_bonus > 0 else 0
        elif outcome == 'win':
            # T79 AC#4: BAD outcome — player gains wins (undesired in
            # loss-farming) and forfeits the staked-losses escrow.
            # Shield/guard/resilience TRIGGER here. wager_streak resets to 0,
            # wager_banked_losses is forfeited.
            new_streak = streak + 1 if streak >= 0 else 1
            if regen_recharge_wins > 0:
                regen_recharge_wins -= 1
            # Compute the base win payout (mirrors the normal-mode win branch).
            count = abs(new_streak)
            raw_bonus = streak_bonus(count)
            base_bonus = raw_bonus * bonus_mult
            if 'fortune_charm' in owned and base_bonus > 0 and random.random() < charm_chance:
                base_bonus = int(base_bonus * 1.25)
                fortune_charm_triggered = True
            bonus_earned = base_bonus
            base_payout = effective_win_mult + bonus_earned
            direct_wins = int(base_payout * effective_stake)
            # ── shield/guard/resilience (the BAD outcome gets the protection) ──
            if 'regen_shield' in owned and regen_recharge_wins == 0:
                shield_used = True
                shield_used_type = 'regen_shield'
                regen_recharge_wins = REGEN_SHIELD_RECHARGE_WINS
                # Shield absorbs the bad-outcome wins — player gains nothing.
                direct_wins = 0
            elif 'guard' in owned:
                guard_triggered = True
                guard_blocked = True
                new_owned = [x for x in new_owned if x != 'guard']
                direct_wins = 0
            else:
                if 'resilience' in owned and streak > 0 and random.random() < resilience_chance:
                    resilience_triggered = True
                    new_streak = max(0, new_streak - 1)
                    proc_streak += 1
            # T74 AC#7 / T79 AC#7: insurance (when armed) caps the bad
            # outcome and refunds the escrowed losses. Safety net does NOT
            # stack with insurance.
            # T102: cap direct_wins at int(base_payout * effective_stake) so
            # the bad-outcome gain is at most the base_payout * stake%. Cast
            # to int to keep the cap a whole number (effective_stake is a
            # fraction; min(int, float) would otherwise return the float).
            if insurance_active and not insurance_used:
                direct_wins = min(direct_wins, int(base_payout * effective_stake))
                # T235: use stake_cost_total (pre-token-spend) so the
                # full escrow — including any token-funded portion —
                # is refunded. stake_losses here is the post-spend
                # cash-only debit; using it would silently forfeit
                # the token-funded portion on a protected loss.
                losses += stake_cost_total
                insurance_used = True
            wins += direct_wins
            # T79 AC#6: safety net on the bad outcome (win) at ≥5x stake
            # refunds 25% of staked losses.
            # T235: pass stake_cost_total (pre-token-spend) so the
            # 25% refund covers the full escrow, not just the cash
            # portion.
            if 'wager_safety_net' in owned and not insurance_used:
                losses += apply_safety_net(stake_cost_total, actual_stake, True)
            # T71: hot streak resets to 0, banked losses forfeited.
            wager_streak = 0
            wager_banked_losses = 0
            wager_last_win_amount = 0
        else:  # jackpot
            # T79 AC#5: SUPER-GOOD outcome — refund escrow + 5× the
            # loss-farming payout. wager_streak increments.
            # T102: truncate AFTER the * 5 (NOT before), so the loss-farming
            # payout has a chance to produce a non-zero amount at typical
            # base_loss values. compute_wager_loss would round base_loss*0.10
            # to 0, then * 5 = 0; truncating last preserves 5*0.10 = 0.5 → 0.
            # T110: use stake_cost_total (pre-token-spend) for the refund.
            new_streak = streak + 1 if streak >= 0 else 1
            if regen_recharge_wins > 0:
                regen_recharge_wins -= 1
            jackpot_hit = True
            loss_count = abs(new_streak) if new_streak < 0 else 0
            loss_bonus = streak_bonus(loss_count) * bonus_mult
            base_loss = 1 + loss_bonus
            actual_loss = int(base_loss * effective_stake * 5)
            losses += stake_cost_total
            losses += actual_loss
            wager_last_win_amount = actual_loss
            if actual_stake == wager_last_stake or wager_last_stake == 0:
                wager_streak += 1
            else:
                wager_streak = 1
            bonus_earned = -loss_bonus if loss_bonus > 0 else 0
        inverted_handled = True

    if not inverted_handled and outcome == 'lose':
        # T71: hot streak ends on a loss (wager_streak, wager_banked_wins, and
        # wager_last_win_amount all reset). Applied before shield/guard so the
        # streak always resets on a 'lose' outcome, matching banked_wins
        # behavior (which was already forfeited unconditionally).
        wager_streak = 0
        wager_banked_wins = 0
        wager_last_win_amount = 0
        if 'regen_shield' in owned and regen_recharge_wins == 0:
            shield_used         = True
            shield_used_type    = 'regen_shield'
            regen_recharge_wins = REGEN_SHIELD_RECHARGE_WINS
            new_streak          = streak
            # T235: refund the full escrow (stake_cost_total) — includes
            # the token-funded portion. stake_wins is the post-spend
            # cash-only value; using it would silently forfeit the
            # tokens on a protected loss.
            wins += stake_cost_total
        elif 'guard' in owned:
            guard_triggered = True
            guard_blocked = True
            new_owned  = [x for x in new_owned if x != 'guard']
            new_streak = streak
            # T235: see regen_shield branch — full-escrow refund.
            wins += stake_cost_total
        else:
            if 'resilience' in owned and streak > 0 and random.random() < resilience_chance:
                resilience_triggered = True
                new_streak  = max(0, streak - 1)
                proc_streak += 1
            else:
                new_streak = streak - 1 if streak <= 0 else -1
            loss_count   = abs(new_streak) if new_streak < 0 else 0
            loss_bonus   = streak_bonus(loss_count) * bonus_mult
            base_loss    = 1 + loss_bonus
            actual_loss  = compute_wager_loss(base_loss, effective_stake)
            if insurance_active:
                # T74 AC#6: cap loss at int(base_loss * effective_stake) and
                # refund the escrow. T102: in the new system actual_loss is
                # already int(base_loss * effective_stake), so the cap is a
                # no-op — kept for spec compliance and to guard against any
                # future change that introduces a real cap. Must cast
                # effective_stake to int since it's a fraction (0.0-0.45);
                # otherwise min(int, float) returns the float.
                actual_loss = min(actual_loss, int(base_loss * effective_stake))
                # T235: refund the full escrow (stake_cost_total) —
                # includes the token-funded portion. stake_wins is the
                # post-spend cash-only value; using it would silently
                # forfeit the tokens on a protected loss.
                wins += stake_cost_total
                insurance_used = True
            losses      += actual_loss
            # v2 (T45): safety net refunds 25% of lost escrow, not reduces losses.
            # T74 AC#7: skip when insurance already fired.
            # T235: pass stake_cost_total (pre-token-spend) so the 25%
            # refund covers the full escrow, not just the cash portion.
            if 'wager_safety_net' in owned and not insurance_used:
                wins += apply_safety_net(stake_cost_total, actual_stake, True)
            bonus_earned = -loss_bonus if loss_bonus > 0 else 0
    elif not inverted_handled and outcome == 'jackpot':
        new_streak = streak + 1 if streak >= 0 else 1
        if regen_recharge_wins > 0:
            regen_recharge_wins -= 1
        jackpot_hit = True
        jackpot_mult = mode.get('jackpot_multiplier', 25)
        # T102: payout = stake_wins (the wager) for stake > 0%, base_payout for 0%.
        # The regular win_streak_bonus (bonus_earned) is added to the NET (per user
        # intent: "applied to the amount that is won/lost AFTER the spin completes").
        # T110: use stake_cost_total (pre-token-spend) so a token-funded
        # spin still gets the wager-based payout.
        if stake_cost_total > 0:
            net_payout = stake_cost_total + bonus_earned
        else:
            net_payout = effective_win_mult + bonus_earned
        raw_payout   = net_payout * jackpot_mult
        direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
        wins        += stake_cost_total
        wins        += direct_wins
        wager_banked_wins += banked_wins
        last_direct_wins = direct_wins
        wager_last_win_amount = last_direct_wins
        bonus_earned = direct_wins + banked_wins - effective_win_mult
        if random.random() < 0.05:
            new_jackpot_echo_next = True
        if jackpot_echo_pending:
            jackpot_echo_triggered = True
    elif not inverted_handled:  # win
        new_streak = streak + 1 if streak >= 0 else 1
        if regen_recharge_wins > 0:
            regen_recharge_wins -= 1

        count      = abs(new_streak)
        raw_bonus  = streak_bonus(count)
        base_bonus = raw_bonus * bonus_mult
        if 'fortune_charm' in owned and base_bonus > 0 and random.random() < charm_chance:
            base_bonus = int(base_bonus * 1.25)
            fortune_charm_triggered = True
        bonus_earned = base_bonus

        # T102: payout = stake_wins (the wager) for stake > 0%, base_payout for 0%.
        # The regular win_streak_bonus (bonus_earned) is added to the NET (per user
        # intent: "applied to the amount that is won/lost AFTER the spin completes").
        # At 0% stake, base_payout = effective_win_mult + bonus_earned already includes
        # the win_streak_bonus; at N% stake we add bonus_earned to the wager.
        # T110: use stake_cost_total (pre-token-spend) so a token-funded spin
        # still gets the wager-based payout. The `wins += stake_wins` lines
        # below also use stake_cost_total for the wager refund.
        if stake_cost_total > 0:
            net_payout = stake_cost_total + bonus_earned
        else:
            net_payout = effective_win_mult + bonus_earned

        if jackpot_echo_pending:
            jackpot_echo_triggered = True
            jackpot_hit  = True
            raw_payout   = net_payout * 25
            direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
            wins        += stake_cost_total
            wins        += direct_wins
            wager_banked_wins += banked_wins
            last_direct_wins = direct_wins
            bonus_earned = direct_wins + banked_wins - effective_win_mult
        elif 'jackpot' in owned and random.random() < jackpot_chance:
            jackpot_hit  = True
            raw_payout   = net_payout * 25
            direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
            wins        += stake_cost_total
            wins        += direct_wins
            wager_banked_wins += banked_wins
            last_direct_wins = direct_wins
            bonus_earned = direct_wins + banked_wins - effective_win_mult
            if random.random() < 0.05:
                new_jackpot_echo_next = True
        else:
            if 'win_echo' in owned and random.random() < echo_chance:
                echo_triggered = True
                raw_payout   = net_payout * 2
                direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
                wins        += stake_cost_total
                wins        += direct_wins
                wager_banked_wins += banked_wins
                last_direct_wins = direct_wins
                bonus_earned = direct_wins + banked_wins - effective_win_mult
            else:
                raw_payout   = net_payout
                direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
                wins += stake_cost_total
                wins += direct_wins
                wager_banked_wins += banked_wins
                last_direct_wins = direct_wins

        # T73 AC#1: record the base (direct) portion of the payout so the next
        # spin can escrow it under double-down. On a loss, wager_last_win_amount
        # is already reset to 0 in the lose branch above.
        wager_last_win_amount = last_direct_wins

        # Update wager streak on win
        if actual_stake == wager_last_stake or wager_last_stake == 0:
            wager_streak += 1
        else:
            wager_streak = 1

    # T77 AC#2: update gravity_drift after the spin resolves. Jackpot counts
    # as a win for drift purposes. Drift resets to 0 on mode change (T76).
    if active_wheel_mode == 'gravity':
        if outcome in ('win', 'jackpot'):
            gravity_drift = clamp_gravity_drift(gravity_drift + 10)
        else:  # lose
            gravity_drift = clamp_gravity_drift(gravity_drift - 10)

    new_best_streak = max(best_streak, new_streak) if new_streak > 0 else best_streak

    # T77: compute the wheel_probabilities for the response from the NEW
    # (post-spin) gravity_drift, so the wheel redraws with the new arc
    # spans after each resolve. The segment_angle below still uses the
    # INPUT probabilities so the wheel animation lands in the correct
    # segment for the outcome that was just rolled.
    response_probs = (
        compute_gravity_probabilities(gravity_drift)
        if active_wheel_mode == 'gravity' else probs
    )

    # Map outcome to a CSS rotation angle that lands the pointer in the correct
    # visual segment.  Segments are arranged clockwise from 12-o'clock:
    #   WIN  → LOSE → JACKPOT (tiny sliver back to 12-o'clock)
    # CSS rotation range per zone:
    #   JACKPOT : [0,   J)
    #   LOSE    : [J,   J+L)
    #   WIN     : [J+L, 360)
    # T77: use the input-drift probabilities (probs) so the segment_angle
    # matches the outcome that was just rolled.
    _j_deg = probs['jackpot_pct'] / 100 * 360
    _l_deg = probs['lose_pct']    / 100 * 360
    _w_deg = probs['win_pct']     / 100 * 360
    _lose_start = _j_deg
    _win_start  = _j_deg + _l_deg
    if outcome == 'jackpot':
        segment_angle = random.uniform(max(1.0, _j_deg * 0.1), max(2.0, _j_deg - 1.0))
    elif outcome == 'lose':
        segment_angle = random.uniform(_lose_start + 1.0, _lose_start + _l_deg - 1.0)
    else:  # win
        segment_angle = random.uniform(_win_start + 1.0, _win_start + _w_deg - 1.0)

    new_state = {
        'owned':              new_owned,
        'streak':             new_streak,
        'best_streak':        new_best_streak,
        'regen_recharge_wins': regen_recharge_wins,
        'wins':               wins,
        'losses':             losses,
        'jackpot_echo_next':  new_jackpot_echo_next,
        'active_cosmetics':   active_cosmetics,
        'proc_streak':        proc_streak,
        'wager_streak':       wager_streak,
        'wager_last_stake':   actual_stake,
        'wager_banked_wins':  wager_banked_wins,
        'wager_banked_losses': wager_banked_losses,
        'wager_last_win_amount': wager_last_win_amount,
        'gravity_drift':      gravity_drift,
    }
    events = {
        'result':                  outcome,
        'segment_angle':           segment_angle,
        'wins_delta':              wins - original_wins,
        'losses_delta':            losses - original_losses,
        'streak':                  new_streak,
        'owned_items':             new_owned,
        'regen_recharge_wins':     regen_recharge_wins,
        'shield_used':             shield_used,
        'shield_used_type':        shield_used_type,
        'shield_broke':            False,
        'guard_triggered':         guard_triggered,
        'guard_blocked':           guard_blocked,
        'bonus_earned':            bonus_earned,
        'effective_win_mult':      effective_win_mult,
        'echo_triggered':          echo_triggered,
        'jackpot_hit':             jackpot_hit,
        'jackpot_echo_triggered':  jackpot_echo_triggered,
        'jackpot_echo_next':       new_jackpot_echo_next,
        'resilience_triggered':    resilience_triggered,
        'lucky_seven_triggered':   lucky_seven_triggered,
        'fortune_charm_triggered': fortune_charm_triggered,
        'active_cosmetics':        active_cosmetics,
        'auto_guard_failed':       auto_guard_failed,
        'proc_streak':             proc_streak,
        'wager_streak':            wager_streak,
        'stake':                   actual_stake,
        'effective_stake':         effective_stake,
        'wager_last_stake':        wager_last_stake,
        'max_stake_pct':           max_stake_pct,
        'active_wheel_mode':       active_wheel_mode,
        'wager_banked_wins':       wager_banked_wins,
        'wager_banked_wins_delta': wager_banked_wins - original_wager_banked_wins,
        'wager_banked_losses':     wager_banked_losses,
        'wager_banked_losses_delta': wager_banked_losses - original_wager_banked_losses,
        'wager_last_win_amount':   wager_last_win_amount,
        'double_down_active':      double_down_active,
        'insurance_used':          insurance_used,
        'gravity_drift':           gravity_drift,
        'gravity_drift_delta':     gravity_drift - original_gravity_drift,
        'wheel_probabilities':     response_probs,
        # T110/T119: insurance-token spend accounting. The key
        # `insurance_tokens` is what the spin response and the
        # insurance buy endpoint both read; the previous key
        # `wager_tokens` was renamed for T119.
        'tokens_spent':            tokens_spent,
        'insurance_tokens':        insurance_tokens,
        'message':                 _build_spin_message(
            result=outcome, wins_delta=wins - original_wins, losses_delta=losses - original_losses,
            is_inverted=(active_wheel_mode == 'inverted'),
            stake=actual_stake, is_mirror=(active_wheel_mode == 'mirror'),
        ),
    }
    return new_state, events


_RESPONSE_KEYS = (
    'result',
    'wins_delta',
    'losses_delta',
    'streak',
    'owned_items',
    'regen_recharge_wins',
    'shield_used',
    'shield_used_type',
    'shield_broke',
    'guard_triggered',
    'guard_blocked',
    'bonus_earned',
    'effective_win_mult',
    'echo_triggered',
    'jackpot_hit',
    'jackpot_echo_triggered',
    'jackpot_echo_next',
    'resilience_triggered',
    'lucky_seven_triggered',
    'fortune_charm_triggered',
    'active_cosmetics',
    'auto_guard_failed',
    'proc_streak',
    'wager_streak',
    'stake',
    'wager_banked_wins',
    'wager_banked_losses',
    'wager_banked_losses_delta',
    'wager_last_win_amount',
    'double_down_active',
    'insurance_used',
    'gravity_drift',
    'wheel_probabilities',
    'active_wheel_mode',
    'tokens_spent',
    'insurance_tokens',
    'message',
)


def _events_to_response(events: dict) -> dict:
    """Convert spin events into the JSON response payload shared by spin() and tick().

    Missing keys default to None so the response is always valid even when
    callers (e.g. test mocks) supply a partial events dict. New fields
    added by T77/T79 (gravity_drift, wheel_probabilities, etc.) are picked
    up automatically once they appear in _RESPONSE_KEYS.
    """
    return {k: events.get(k) for k in _RESPONSE_KEYS}


def _build_spin_message(*, result, wins_delta, losses_delta, is_inverted, stake, is_mirror):
    """T79: build a short human-readable message describing the spin outcome.
    In inverted mode the semantics are flipped (losses are good, wins are bad).
    """
    if is_mirror and result in ('win', 'jackpot'):
        return f'Mirror took the better roll: +{wins_delta} wins'
    if is_inverted:
        if result == 'lose':
            return f'Loss-farmed +{losses_delta} losses'
        if result == 'jackpot':
            return f'Inverted jackpot: +{wins_delta} wins AND +{losses_delta} losses'
        return f'Unwanted win — forfeited {-losses_delta} losses'
    if result == 'jackpot':
        return f'JACKPOT! +{wins_delta} wins'
    if result == 'win':
        return f'+{wins_delta} wins'
    if result == 'lose':
        return f'-{stake} wins'
    return f'Result: {result}'


@game_bp.route('/api/health')
def health():
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
        return jsonify({'status': 'ok'})
    except Exception:
        log.exception('HEALTH_CHECK_FAILED')
        return jsonify({'status': 'error'}), 503


@game_bp.route('/api/state')
@login_required
def get_state():
    try:
        with db_connection() as conn:
            season_info = ensure_current_season(conn)
            latest_winners = get_latest_winners(conn, season_info['season_number'])
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT wins, losses, fish_clicks, streak, owned_items,
                              equipped_fish, regen_recharge_wins,
                              active_cosmetics, spin_count, win_count, cumulative_wins,
                              winmult_inf_level, bonusmult_inf_level,
                              streak_armor_level, low_spec_mode,
                              lure_mastery_level, jackpot_resonance_level,
                              echo_amp_level, proc_streak_level, proc_streak,
                              fish_exchange_total, equipped_class,
                              dice_charges, dice_last_recharge, jackpot_echo_next,
                              dice_rolled_since_spin,
                              fishing_lucky_next, caught_species,
                              auto_spin_since, season_registered,
                              prestige_level, prestige_count, legacy_wins,
                              onboarding_step,
                              wager_streak, wager_last_stake, double_down_pending,
                              wager_banked_wins,
                              insurance_charges, insurance_armed,
                              wager_last_win_amount, wager_banked_losses,
                              active_wheel_mode, insurance_tokens, aquarium_species,
                              cosmetic_fragments, guard_charges,
                              gravity_drift,
                              auto_fish_enabled, auto_fish_last_tick
                       FROM game_state WHERE user_id = %s''',
                    (current_user.id,),
                )
                gs = cur.fetchone()
                cur.execute('SELECT total_contributed, target, win_chance_pct, filled, filled_at, last_decay_check FROM community_pot WHERE id = 1')
                pot = cur.fetchone()
                total_pending_clicks = get_total_fish_clicks(cur)
                # Season 8: singularity meter
                cur.execute('SELECT total_contributed, target, filled, filled_at, fill_count FROM singularity_meter WHERE id = 1')
                singularity = cur.fetchone()

            # T238: bounties + community goal run on the same conn as the rest
            # of the route. All three helpers are read-only (or read+INSERT-
            # then-rollback, same as before — the route does not commit), so
            # the open transaction is fine.
            now_utc = dt.datetime.now(timezone.utc)
            bounty_date = now_utc.date()
            week_num = get_week_number(now_utc)
            bounties = get_bounty_status(conn, current_user.id, bounty_date)
            goal_row, goal_def = get_active_goal(conn, season_info['season_number'], week_num)
            player_contrib = (
                get_player_contribution(conn, goal_def['goal_id'], current_user.id)
                if goal_row else 0
            )

            # T238: build the same `season` payload as before, from the single
            # ensure_current_season row + get_latest_winners. Net: one `seasons`
            # read per /api/state (was 2), same response shape.
            full_info = {
                'season_number': season_info['season_number'],
                'season_name': season_info['season_name'],
                'player_facing_number': season_info['player_facing_number'],
                'sub_number': season_info['sub_number'],
                'ends_at': season_info['ends_at'],
                'latest_winners': latest_winners,
            }

        pot_celebrate = _pot_boost_active(pot, now_utc)
        owned_items     = list(gs['owned_items'])
        max_charges     = dice_max_charges(owned_items)
        dice_charges    = min(gs['dice_charges'], max_charges)
        last_recharge   = gs['dice_last_recharge']
        dice_charges, last_recharge = dice._recharge_dice(dice_charges, last_recharge, max_charges, now_utc)

        # T119: insurance has no recharge. Charges are now derived purely
        # from tokens spent on insurance buys. The old
        # wager_insurance_charges/wager_insurance_last_recharge fields and
        # the WAGER_INSURANCE_MAX_CHARGES cap are gone (see migration 054).

        # Season 8: available wheel modes for this week
        available_modes = get_available_modes(week_num)
        if singularity and singularity['filled']:
            available_modes = available_modes + ['singularity']

        return jsonify({
            'wins':               int(gs['wins']),
            'losses':             gs['losses'],
            'fish_clicks':        gs['fish_clicks'],
            'streak':             gs['streak'],
            'owned_items':        owned_items,
            'equipped_fish':      gs['equipped_fish'],
            'regen_recharge_wins': gs['regen_recharge_wins'],
            'active_cosmetics':   list(gs['active_cosmetics']),
            'spin_count':         gs['spin_count'],
            'win_count':          gs['win_count'],
            'season':             full_info,
            'winmult_inf_level':         gs['winmult_inf_level'],
            'bonusmult_inf_level':       gs['bonusmult_inf_level'],
            'streak_armor_level':        gs['streak_armor_level'],
            'lure_mastery_level':        gs['lure_mastery_level'],
            'jackpot_resonance_level':   gs['jackpot_resonance_level'],
            'echo_amp_level':            gs['echo_amp_level'],
            'proc_streak_level':         gs['proc_streak_level'],
            'proc_streak':               gs['proc_streak'],
            'fish_exchange_total':       gs['fish_exchange_total'],
            'equipped_class':            gs['equipped_class'],
            'low_spec_mode':             gs['low_spec_mode'],
            'dice_charges':           dice_charges,
            'dice_last_recharge':     last_recharge.isoformat(),
            'jackpot_echo_next':      gs['jackpot_echo_next'],
            'dice_rolled_since_spin': bool(gs['dice_rolled_since_spin']),
            'fishing_lucky_next':  bool(gs['fishing_lucky_next']),
            'caught_species':      list(gs['caught_species']),
            'auto_spin_since':     gs['auto_spin_since'].isoformat() if gs['auto_spin_since'] else None,
            'season_registered':   bool(gs['season_registered']),
            'happy_hour':          is_happy_hour(),
            'community_pot': {
                'total_contributed':  pot['total_contributed'] if pot else 0,
                'target':             pot['target']            if pot else 1_000,
                'filled':             pot['filled']            if pot else False,
                'active':             pot_celebrate,
                'win_chance_pct':     float(pot['win_chance_pct']) if pot else 50.0,
                'total_pending_clicks': total_pending_clicks,
            } if pot else None,
            # Season 8 additions
            'prestige_level':       gs.get('prestige_level', 0),
            'prestige_count':       gs.get('prestige_count', 0),
            'next_prestige_threshold': (
                get_prestige_threshold(gs.get('owned_items', []), gs.get('prestige_level', 0))
                if gs.get('prestige_level', 0) < MAX_PRESTIGE_LEVEL else None
            ),
            'legacy_wins':          int(gs.get('legacy_wins', 0)),
            'onboarding_step':      gs.get('onboarding_step', 0),
            # T216: auto-spin is active iff auto_spin_since is set. The
            # 100-spin budget was removed (see migration 057). Heartbeat
            # auto-stop (60s of no /api/tick) is enforced in /api/tick.
            'auto_spin_active':     gs.get('auto_spin_since') is not None,
            'cumulative_wins':      int(gs.get('cumulative_wins', 0)),
            'wager_streak':         gs.get('wager_streak', 0),
            'wager_last_stake':     gs.get('wager_last_stake', 0),
            'double_down_pending':  bool(gs.get('double_down_pending', False)),
            'wager_banked_wins':    gs.get('wager_banked_wins', 0),
            'wager_banked_losses':  gs.get('wager_banked_losses', 0),
            'wager_last_win_amount': int(gs.get('wager_last_win_amount', 0) or 0),
            'insurance_charges':     int(gs.get('insurance_charges', 0) or 0),
            'insurance_armed':       bool(gs.get('insurance_armed', False)),
            # T224: surface auto_fish_enabled so the client stays in sync
            # with the server. Without this, a player who prestiged with
            # auto-fish on would have a stale client state (manual-fish UI
            # hidden, toggle hidden because they no longer own autofisher_*).
            'auto_fish_enabled':     bool(gs.get('auto_fish_enabled', False)),
            'insurance_free_claimed_date': (
                gs.get('insurance_free_claimed_date').isoformat()
                if gs.get('insurance_free_claimed_date') is not None
                else None
            ),
            'active_wheel_mode':    gs.get('active_wheel_mode', 'steady'),
            'available_wheel_modes': available_modes,
            # T77: gravity drift (resets to 0 on mode change per T76) and the
            # drift-adjusted wheel probabilities for the current mode.
            'gravity_drift':         int(gs.get('gravity_drift', 0) or 0),
            'wheel_probabilities':   _current_wheel_probabilities(
                gs.get('active_wheel_mode', 'steady'),
                int(gs.get('gravity_drift', 0) or 0),
            ),
            'insurance_tokens':     gs.get('insurance_tokens', 0),
            'aquarium_species':     list(gs.get('caught_species', [])),
            'cosmetic_fragments':   gs.get('cosmetic_fragments', 0),
            'guard_charges':        gs.get('guard_charges', 0),
            # T102: max stake percentage for this player (30 base, 35/40/45
            # with stake extension items). Frontend uses this to size the slider.
            'max_stake_pct':        compute_max_stake_pct(owned_items),
            'bounties':             bounties,
            'community_goal': {
                'goal_id':     goal_def['goal_id'],
                'description': goal_def['description'],
                'target':      goal_def['target'],
                'current':     goal_row['current'] if goal_row else 0,
                'completed':   goal_row['completed'] if goal_row else False,
                'player_contribution': player_contrib,
                'per_player_cap': goal_def['per_player_cap'],
            } if goal_def else None,
            'singularity': {
                'total_contributed': singularity['total_contributed'] if singularity else 0,
                'target':            singularity['target'] if singularity else 100_000_000,
                'filled':            singularity['filled'] if singularity else False,
                'fill_count':        singularity['fill_count'] if singularity else 0,
            } if singularity else None,
        })
    except Exception:
        log.exception('GET_STATE_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Failed to load state'}), 500


@game_bp.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    err = require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET low_spec_mode = %s WHERE user_id = %s',
                    (bool(data.get('low_spec_mode', False)), current_user.id),
                )
            conn.commit()
        return jsonify({'ok': True})
    except Exception:
        log.exception('SETTINGS_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Settings update failed'}), 500


def _apply_pot_decay(conn, pot_row, now_utc: dt.datetime) -> int:
    """Decay the community pot target by 20% per 12-hour period. Returns effective target."""
    if not pot_row or not pot_row.get('last_decay_check'):
        return int(pot_row['target']) if pot_row else 1_000
    last_decay = pot_row['last_decay_check']
    last_decay = _aware(last_decay)
    decay_periods = int((now_utc - last_decay).total_seconds() / (12 * 3600))
    effective_target = int(pot_row['target'])
    if decay_periods <= 0:
        return effective_target
    for _ in range(decay_periods):
        effective_target = max(500, int(effective_target * 0.8))
    if int(pot_row.get('total_contributed', 0)) > 0:
        effective_target = max(effective_target, int(pot_row['total_contributed']) + 1)
    new_decay_ts = last_decay + timedelta(hours=12 * decay_periods)
    with conn.cursor() as _cur:
        _cur.execute(
            'UPDATE community_pot SET target = %s, last_decay_check = %s WHERE id = 1',
            (effective_target, new_decay_ts),
        )
    return effective_target


def _reset_expired_pot(conn, pot) -> int:
    """Reset an expired filled pot: advance target ×1.25, clear contributions. Returns new target."""
    new_target = max(int(pot['target'] * 1.25), 1)
    with conn.cursor() as cur:
        cur.execute(
            '''UPDATE community_pot SET filled = false, filled_at = NULL,
               total_contributed = 0, target = %s, last_decay_check = NOW()
               WHERE id = 1''',
            (new_target,)
        )
    return new_target


# T247: the community pot's "boost window" — the pot was filled, the global
# win chance is boosted, and the boost expires 7 days after the fill. Every
# route that reads the pot has to know whether the boost is still active.
# The check is the same 3-clause expression in 5 places (see /api/state, the
# spin/tick/route paths); consolidate it here so the 7-day window is defined
# in exactly one place.
_POT_BOOST_DAYS = 7


def _pot_boost_active(pot_row, now_utc: dt.datetime) -> bool:
    """Return True if the pot boost is still active right now.

    Active = pot was filled AND the fill was within the last 7 days.
    Returns False for any falsy pot_row, unfilled pots, or pots whose
    filled_at is NULL — those are the same edge cases the inline
    expressions at the 5 call sites had to guard.
    """
    if not pot_row:
        return False
    if not pot_row.get('filled'):
        return False
    filled_at = pot_row.get('filled_at')
    if not filled_at:
        return False
    return filled_at > now_utc - dt.timedelta(days=_POT_BOOST_DAYS)


@game_bp.route('/api/spin', methods=['POST'])
@login_required
@limiter.limit('10 per second')
def spin():
    err = require_json()
    if err:
        return err

    try:
        with db_connection() as conn:
            ensure_current_season(conn)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                gs = _load_game_state(cur, current_user.id, for_update=True)

            # Block manual spins when server-side auto-spin is currently running.
            # T216: the `auto_spin_since` timestamp is the only signal — the
            # per-activation budget column was dropped (see migration 057).
            if gs.get('auto_spin_since') is not None:
                return jsonify({'error': 'Auto-spin is active. Stop it first to spin manually.'}), 403

            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT filled, filled_at, win_chance_pct, last_decay_check, total_contributed, target FROM community_pot WHERE id = 1')
                pot_row = cur.fetchone()

            # Tab-lock: only one browser tab may spin at a time.
            # The active tab holds a lock refreshed on each spin and by heartbeats.
            # A tab that hasn't refreshed in TAB_LOCK_TIMEOUT seconds is considered dead.
            TAB_LOCK_TIMEOUT = 30
            req_tab_id = (request.json or {}).get('tab_id', '')
            if req_tab_id:
                stored_tab_id  = gs['active_tab_id']
                tab_last_seen  = gs['tab_last_seen']
                if stored_tab_id and stored_tab_id != req_tab_id:
                    if tab_last_seen is not None:
                        tab_last_seen = _aware(tab_last_seen)
                        age = (dt.datetime.now(timezone.utc) - tab_last_seen).total_seconds()
                        if age < TAB_LOCK_TIMEOUT:
                            return jsonify({'error': 'Another tab is active. Close it to spin here.', 'tab_locked': True}), 423

            now_utc = dt.datetime.now(timezone.utc)

            pot_active = _pot_boost_active(pot_row, now_utc)
            if pot_row and pot_row['filled'] and not pot_active:
                _reset_expired_pot(conn, pot_row)

            # Community pot: apply target decay if 12+ hours since last check
            if not pot_active:
                _apply_pot_decay(conn, pot_row, now_utc)

            # Dice recharge
            dice_charges  = gs['dice_charges']
            last_recharge = gs['dice_last_recharge']
            owned_for_dice = list(gs['owned_items'])
            max_charges    = dice_max_charges(owned_for_dice)
            dice_charges   = min(dice_charges, max_charges)
            dice_charges, last_recharge = dice._recharge_dice(dice_charges, last_recharge, max_charges, now_utc)

            # T119: insurance has no recharge — charges are derived purely
            # from tokens spent on /api/insurance/buy. Cap is removed; the
            # insurance_charges value from the DB is the truth.

            # Build spin context (immutable for this request)
            ctx = _build_spin_context(gs)
            pot_win_pct_frac = float(pot_row['win_chance_pct']) / 100.0 if pot_row else 0.505

            # T102: get stake_pct from request body; resolve double-down if pending.
            # DD is handled in _resolve_spin's escrow logic (escrows
            # wager_last_win_amount) and does NOT modify the stake_pct
            # parameter — the slider value is sent as-is.
            req_stake = (request.json or {}).get('stake', 0)
            try:
                req_stake = int(req_stake)
            except (TypeError, ValueError):
                req_stake = 0
            double_down_active = bool(gs.get('double_down_pending', False))
            insurance_active = bool(gs.get('insurance_armed', False))

            # T110: pay_with_tokens opt-in for high-stake spins. The actual
            # spend is computed inside _resolve_spin (which knows the final
            # stake_wins); we only validate the request flag here.
            pay_with_tokens = bool((request.json or {}).get('pay_with_tokens', False))
            if pay_with_tokens:
                if req_stake < HIGH_STAKE_TOKEN_THRESHOLD:
                    return jsonify({
                        'error': f'Pay-with-tokens requires stake >= {HIGH_STAKE_TOKEN_THRESHOLD}%'
                    }), 400
                if double_down_active:
                    return jsonify({
                        'error': 'Pay-with-tokens is not compatible with Double-Down'
                    }), 400
                if int(gs.get('insurance_tokens', 0)) <= 0:
                    return jsonify({
                        'error': 'No insurance tokens to spend'
                    }), 400

            new_spin_count = gs['spin_count'] + 1

            # T220: consume any pending dice roll. The dice (rolled via
            # /api/roll-dice) was either applied immediately (if no
            # auto-spin was active) or buffered (if auto-spinning). In
            # both cases pending_dice holds {new_streak, original_streak,
            # dice_sum, ...}. We use new_streak as the input streak here.
            # If the spin resolves as a loss, we revert the streak to
            # original_streak and refund the dice charge below.
            pd = gs.get('pending_dice')
            if pd:
                input_streak = pd['new_streak']
            else:
                input_streak = gs['streak']

            new_state, events = _resolve_spin(
                owned=list(gs['owned_items']),
                streak=input_streak,
                best_streak=gs['best_streak'],
                regen_recharge_wins=gs['regen_recharge_wins'],
                wins=int(gs['wins']),
                losses=gs['losses'],
                jackpot_echo_next=bool(gs['jackpot_echo_next']),
                spin_count=new_spin_count,
                active_cosmetics=list(gs['active_cosmetics']),
                proc_streak=gs['proc_streak'],
                effective_win_mult=ctx['effective_win_mult'],
                bonus_mult=ctx['bonus_mult'],
                jackpot_chance=ctx['jackpot_chance'],
                echo_chance=ctx['echo_chance'],
                charm_chance=ctx['charm_chance'],
                resilience_chance=ctx['resilience_chance'],
                proc_streak_level=ctx['proc_streak_level'],
                pot_active=pot_active,
                pot_win_pct=pot_win_pct_frac,
                # T102: stake_pct is the slider value (0-45 percentage).
                stake_pct=req_stake,
                wager_streak=gs.get('wager_streak', 0),
                wager_last_stake=gs.get('wager_last_stake', 0),
                active_wheel_mode=gs.get('active_wheel_mode', 'steady'),
                aquarium_luck=ctx.get('aquarium_luck', 0.0),
                wager_banked_wins=int(gs.get('wager_banked_wins', 0)),
                insurance_active=insurance_active,
                # T73: double-down escrow uses the last actual win amount
                double_down_active=double_down_active,
                wager_last_win_amount=int(gs.get('wager_last_win_amount', 0) or 0),
                # T77: gravity drift
                gravity_drift=int(gs.get('gravity_drift', 0) or 0),
                # T79: banked losses
                wager_banked_losses=int(gs.get('wager_banked_losses', 0)),
                # T110: insurance-token spend (column renamed to insurance_tokens in T119)
                insurance_tokens=int(gs.get('insurance_tokens', 0)),
                pay_with_tokens=pay_with_tokens,
            )

            # T220: loss handler for pending dice. If this spin was a loss
            # AND there was a pending dice roll, revert the streak to the
            # pre-dice value and refund the dice charge.
            dice_refunded = False
            if pd and events['result'] == 'lose':
                original = pd.get('original_streak', gs['streak'])
                new_state['streak'] = original
                # best_streak should not be increased by the (now-reverted) bonus
                new_state['best_streak'] = max(gs['best_streak'], original) if original > 0 else gs['best_streak']
                # Refund the dice charge (cap at max). Reset recharge clock so
                # the player doesn't get a head-start on the next regen tick.
                dice_charges = min(dice_charges + 1, max_charges)
                last_recharge = now_utc
                dice_refunded = True
                log.info('DICE_REFUND_ON_LOSS  user_id=%s  original_streak=%s  dice_sum=%s',
                         current_user.id, original, pd.get('dice_sum'))

            new_win_count  = gs['win_count']  + (1 if events['result'] in ('win', 'jackpot')  else 0)
            new_loss_count = gs['loss_count'] + (1 if events['result'] == 'lose' else 0)
            # T106: cumulative_wins tracks the lifetime value of wins gained.
            # Incremented on every win/jackpot by wins_delta (the actual wins
            # gained from this spin, including wager payouts). Never decremented.
            new_cumulative_wins = int(gs.get('cumulative_wins', 0)) + max(0, int(events.get('wins_delta', 0)))

            # T221: jackpot chat messages are gone entirely. No system message
            # is posted for a jackpot, neither the old "JACKPOT in M mode at Nx
            # stake" format nor the new "hit a N jackpot in M mode" format
            # that big_win_msg produced via the was_jackpot flag. The
            # `_maybe_announce_big_win` call below also skips jackpots now.
            # T230: a double-down that lands produces a single merged
            # message ('💰 X won a Nx double-down for M wins in MODE!') that
            # also implies a big win. The big_win chat post is suppressed
            # (skip_message=True below) so the player sees one message, not
            # two. The biggest_win_annotated value is still updated, so the
            # per-player escalating threshold keeps working for non-DD wins.
            double_down_msg_posted = False
            if (double_down_active and events['result'] in ('win', 'jackpot')
                    and int(events.get('stake', 1)) >= chat_triggers.DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE):
                post_system_message(conn, chat_triggers.double_down_win_msg(
                    current_user.username,
                    int(events.get('stake', 1)),
                    int(events['wins_delta']),
                    events.get('active_wheel_mode', 'steady'),
                ), 'system', event_kind='double_down_win')
                double_down_msg_posted = True
            # Season 8: hot streak milestone (fires on exact transition to threshold)
            if (events['result'] in ('win', 'jackpot')
                    and int(events.get('wager_streak', 0)) == chat_triggers.HOT_STREAK_MSG_THRESHOLD):
                post_dedup_system_message(
                    conn, chat_triggers.hot_streak_msg(current_user.username),
                    current_user.id, event_kind='hot_streak')
            # Season 8: big win (T83 per-player escalating threshold).
            # T230: skip the chat post when a double-down message already
            # conveyed the same info (see skip_message=True below).
            new_biggest_win_announced = _maybe_announce_big_win(
                conn, gs, events, current_user.username, current_user.id,
                skip_message=double_down_msg_posted)

            # Season 8: bounty tracking
            bounty_date = dt.datetime.now(timezone.utc).date()
            if events['jackpot_hit']:
                increment_bounty(conn, current_user.id, 'bounty_jackpot', bounty_date)
            if events.get('stake', 1) >= 5 and events['result'] in ('win', 'jackpot'):
                increment_bounty(conn, current_user.id, 'bounty_wager5', bounty_date)
            # bounty_streak10 tracks the real win streak (events['streak']), not
            # wager_streak (the same-stake hot-streak counter, which never resets
            # at the default 1x stake and made this permanently uncompletable
            # after a player's first day). amount=10 completes it in one shot —
            # this is a one-time "reach a streak" achievement, not a 10x counter.
            if events.get('streak', 0) == 10:
                increment_bounty(conn, current_user.id, 'bounty_streak10', bounty_date, amount=10)
            if events.get('active_wheel_mode') == 'mirror' and events['result'] in ('win', 'jackpot'):
                increment_bounty(conn, current_user.id, 'bounty_mirror', bounty_date)
            if double_down_active and events['result'] in ('win', 'jackpot'):
                increment_bounty(conn, current_user.id, 'bounty_double', bounty_date)
            # Season 8: community goal contribution hooks
            season_info = get_season_info(conn)
            season_num = season_info.get('season_number', 8) if season_info else 8
            week_num = get_week_number(now_utc)
            _, goal_def = get_active_goal(conn, season_num, week_num)
            if goal_def:
                if goal_def['metric'] == 'jackpots_landed' and events['jackpot_hit']:
                    increment_goal(conn, goal_def['goal_id'], current_user.id, 1)
                    check_goal_completion(conn, goal_def['goal_id'])
                elif (goal_def['metric'] == 'wins_wagered' and events.get('stake', 1) > 1
                      and events['result'] in ('win', 'jackpot')):
                    # Gated on stake > 1 -- this metric is "wins wagered", not
                    # "wins earned". Previously fired on any win regardless of
                    # stake, so the goal filled from unrelated baseline play
                    # rather than actual wagering activity.
                    increment_goal(conn, goal_def['goal_id'], current_user.id, int(events.get('wins_delta', 0)))
                    check_goal_completion(conn, goal_def['goal_id'])

            # Season 8: onboarding advance
            onboarding_advance = False
            if gs.get('onboarding_step', 0) == 0:
                onboarding_advance = True
                # Season 8: post system message for new player first spin
                post_system_message(conn, chat_triggers.new_player_msg(current_user.username),
                                    'system', event_kind='new_player')
                # Season 8: grant trail_1 cosmetic reward on first spin
                if 'trail_1' not in new_state['owned']:
                    new_state['owned'] = list(new_state['owned']) + ['trail_1']
                if 'trail_1' not in new_state['active_cosmetics']:
                    new_state['active_cosmetics'] = list(new_state['active_cosmetics']) + ['trail_1']

            # Manual spin: add extra full rotations for the wheel animation
            total_rotation = random.randint(5, 8) * 360 + events['segment_angle']

            # T215: Guard Charge passive regen. Every N spins, if the player
            # owns the guard_charge item and has charges below the cap, grant
            # one charge. Computed against new_spin_count so the regen fires
            # on the Nth, 2Nth, 3Nth, ... spin (e.g. spin #50, #100, #150).
            # Distinct from the Regen Shield item (which blocks losses).
            prev_guard_charges = int(gs.get('guard_charges', 0) or 0)
            owns_guard_charge  = 'guard_charge' in gs['owned_items']
            if (owns_guard_charge
                    and new_spin_count > 0
                    and new_spin_count % GUARD_CHARGE_RECHARGE_SPINS == 0
                    and prev_guard_charges < GUARD_CHARGE_MAX):
                new_guard_charges = min(GUARD_CHARGE_MAX, prev_guard_charges + 1)
                log.info('GUARD_CHARGE_REGEN  user_id=%s  spin_count=%s  new_charges=%s',
                         current_user.id, new_spin_count, new_guard_charges)
            else:
                new_guard_charges = prev_guard_charges

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET wins = %s, losses = %s, streak = %s, best_streak = %s,
                           regen_recharge_wins = %s,
                           owned_items = %s, spin_count = %s, win_count = %s, loss_count = %s,
                           cumulative_wins = %s,
                           fish_clicks = %s, active_cosmetics = %s,
                           dice_charges = %s, dice_last_recharge = %s,
                           jackpot_echo_next = %s, proc_streak = %s,
                           guard_charges = %s,
                           pending_dice = NULL,
                           dice_rolled_since_spin = FALSE,
                           last_spin_at = NOW(),
                           active_tab_id = %s, tab_last_seen = NOW(),
                          wager_streak = %s, wager_last_stake = %s,
                          wager_banked_wins = %s,
                          wager_banked_losses = %s,
                          wager_last_win_amount = %s,
                          double_down_pending = FALSE,
                          insurance_armed = FALSE,
                          insurance_charges = %s,
                          biggest_win_announced = %s,
                          gravity_drift = %s,
                          insurance_tokens = %s,
                          onboarding_step = CASE WHEN onboarding_step = 0 THEN 1 ELSE onboarding_step END
                       WHERE user_id = %s''',
                     (new_state['wins'], new_state['losses'],
                      new_state['streak'], new_state['best_streak'],
                      new_state['regen_recharge_wins'],
                      new_state['owned'], new_spin_count, new_win_count, new_loss_count,
                      new_cumulative_wins,
                      gs['fish_clicks'], new_state['active_cosmetics'],
                      dice_charges, last_recharge,
                      new_state['jackpot_echo_next'], new_state['proc_streak'],
                      new_guard_charges,
                      req_tab_id or gs['active_tab_id'],
                     new_state.get('wager_streak', 0), new_state.get('wager_last_stake', 1),
                     new_state.get('wager_banked_wins', 0),
                     new_state.get('wager_banked_losses', 0),
                     new_state.get('wager_last_win_amount', 0),
                     int(gs.get('insurance_charges', 0) or 0),
                     new_biggest_win_announced,
                     new_state.get('gravity_drift', 0),
                     int(events.get('insurance_tokens', 0)),
                     current_user.id),
                )
            conn.commit()

        resp = _events_to_response(events)
        resp['angle'] = total_rotation
        resp['new_spin_count'] = new_spin_count
        resp['dice_charges'] = dice_charges
        resp['dice_last_recharge'] = last_recharge.isoformat()
        # T220: tell the client whether the dice roll was refunded (the spin
        # was a loss, so the dice bonus was reverted and the charge given back).
        resp['dice_refunded'] = dice_refunded
        if dice_refunded and pd:
            resp['dice_refunded_sum'] = pd.get('dice_sum', 0)
        # T106: echo the new cumulative_wins so the shop tier-locked text
        # updates live without a page refresh. The client had been waiting
        # for the next /api/state poll, which never happened on its own.
        resp['cumulative_wins'] = new_cumulative_wins
        resp['wager_streak'] = new_state.get('wager_streak', 0)
        resp['wager_banked_wins'] = new_state.get('wager_banked_wins', 0)
        resp['wager_banked_losses'] = new_state.get('wager_banked_losses', 0)
        resp['wager_last_win_amount'] = new_state.get('wager_last_win_amount', 0)
        resp['stake'] = new_state.get('wager_last_stake', 0)
        # T70: surface effective_stake + wager_last_stake on the spin response
        # so the frontend can verify the spin used the requested stake (and
        # apply the same value on next change / hot-streak reset).
        resp['effective_stake'] = events.get('effective_stake', 0.0)
        resp['wager_last_stake'] = new_state.get('wager_last_stake', 0)
        # T102: max_stake_pct for this player (30-45 with stake extension items).
        resp['max_stake_pct'] = events.get('max_stake_pct',
                                            compute_max_stake_pct(list(gs['owned_items'])))
        resp['onboarding_advance'] = onboarding_advance
        resp['double_down_active'] = double_down_active
        # T119: surface insurance state on spin response. Column renamed
        # from wager_insurance_charges/armed to insurance_charges/armed;
        # the recharge timestamp key is gone.
        resp['insurance_charges'] = int(gs.get('insurance_charges', 0) or 0)
        resp['insurance_armed'] = False
        # T215: surface the post-regen guard_charges so the client's UI
        # updates immediately after the spin (no /api/state poll required).
        resp['guard_charges'] = new_guard_charges
        # T77: gravity drift + drift-adjusted probabilities on the spin
        # response so the wheel redraws correctly after each resolve.
        resp['gravity_drift'] = new_state.get('gravity_drift', 0)
        resp['wheel_probabilities'] = events.get('wheel_probabilities')
        # T110: surface the post-spend token balance + amount spent so the
        # client can update its display without a /api/state poll.
        resp['insurance_tokens'] = int(events.get('insurance_tokens', gs.get('insurance_tokens', 0)))
        resp['tokens_spent'] = int(events.get('tokens_spent', 0))
        return jsonify(resp)
    except Exception:
        log.exception('SPIN_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Spin failed'}), 500


@game_bp.route('/api/tab/heartbeat', methods=['POST'])
@login_required
@limiter.limit('30 per minute')
def tab_heartbeat():
    err = require_json()
    if err:
        return err
    tab_id = (request.json or {}).get('tab_id', '')
    if not tab_id:
        return jsonify({'ok': False}), 400

    TAB_LOCK_TIMEOUT = 30
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT active_tab_id, tab_last_seen FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,)
                )
                gs = cur.fetchone()

            if gs is None:
                return jsonify({'ok': False}), 404

            stored = gs['active_tab_id']
            last_seen = gs['tab_last_seen']
            now = dt.datetime.now(timezone.utc)

            last_seen = _aware(last_seen)

            stale = (last_seen is None or (now - last_seen).total_seconds() >= TAB_LOCK_TIMEOUT)
            can_claim = not stored or stored == tab_id or stale

            if can_claim:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE game_state SET active_tab_id = %s, tab_last_seen = NOW() WHERE user_id = %s',
                        (tab_id, current_user.id)
                    )
                conn.commit()
                return jsonify({'ok': True, 'active': True})
            else:
                conn.rollback()
                return jsonify({'ok': True, 'active': False})
    except Exception:
        log.exception('TAB_HEARTBEAT_ERROR  user_id=%s', current_user.id)
        return jsonify({'ok': False}), 500


@game_bp.route('/api/tick', methods=['POST'])
@login_required
@limiter.limit('30 per minute')
def tick():
    """Server-side auto-spin tick. Called every ~3s by the client.
    Computes all pending spin outcomes since the last tick and returns results.
    """
    try:
        now_utc = dt.datetime.now(timezone.utc)
        with db_connection() as conn:
            ensure_current_season(conn)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                gs = _load_game_state(cur, current_user.id, for_update=True)
                cur.execute(
                    'SELECT filled, filled_at, win_chance_pct FROM community_pot WHERE id = 1'
                )
                pot_row = cur.fetchone()

            # T216: only process auto-spin when the player has started it.
            # The per-activation budget column was dropped (see migration 057).
            # Manual spins go through /api/spin directly.
            if gs.get('auto_spin_since') is None:
                return jsonify({'spins': [], 'auto_spin_active': False, 'elapsed_ms': 0})

            auto_spin_since = gs['auto_spin_since']
            auto_spin_since = _aware(auto_spin_since)

            last_spin = gs['last_spin_at'] or auto_spin_since
            last_spin = _aware(last_spin)
            # Never count time before the wheel started this session, or more
            # than AUTO_SPIN_OFFLINE_CAP_S before now (S9 RV-03 offline cap).
            cursor = max(auto_spin_since, last_spin,
                         now_utc - timedelta(seconds=AUTO_SPIN_OFFLINE_CAP_S))

            elapsed = (now_utc - cursor).total_seconds()
            # T216: only the MAX_SPINS_PER_TICK catch-up cap remains; the
            # 100-spin budget cap was dropped with migration 057.
            spins_due = min(int(elapsed // AUTO_SPIN_INTERVAL_SECONDS), MAX_SPINS_PER_TICK)

            if spins_due == 0:
                return jsonify({'spins': [], 'auto_spin_active': True,
                                'elapsed_ms': int(elapsed * 1000)})

            is_catch_up = spins_due > CATCH_UP_THRESHOLD

            pot_active = _pot_boost_active(pot_row, now_utc)
            pot_win_pct = float(pot_row['win_chance_pct']) / 100.0 if pot_row else 0.50

            # Carry-over mutable state
            owned               = list(gs['owned_items'])
            streak              = gs['streak']
            best_streak         = gs['best_streak']
            regen_recharge_wins = gs['regen_recharge_wins']
            current_wins        = int(gs['wins'])
            current_losses      = gs['losses']
            jackpot_echo_next   = bool(gs['jackpot_echo_next'])
            new_spin_count      = gs['spin_count']
            new_win_count       = gs['win_count']
            new_loss_count      = gs['loss_count']
            # T106: cumulative_wins — lifetime value of wins gained.
            new_cumulative_wins = int(gs.get('cumulative_wins', 0))
            active_cosmetics    = list(gs['active_cosmetics'])
            current_proc_streak = gs['proc_streak']
            # T90: track escalating big-win threshold across the loop
            new_biggest_win_announced = int(gs.get('biggest_win_announced', 0) or 0)
            # T77: gravity drift is carried across spins within the tick so
            # the wheel probabilities shift correctly after each resolve.
            current_gravity_drift = int(gs.get('gravity_drift', 0) or 0)
            # T79: auto-spin never banked losses (stake=1, no wager) but the
            # carry-over is here for symmetry with manual spin.
            current_wager_banked_losses = int(gs.get('wager_banked_losses', 0) or 0)

            # Immutable spin context
            ctx = _build_spin_context(gs)

            # Dice recharge (computed once per tick from actual elapsed time)
            dice_charges  = gs['dice_charges']
            last_recharge = gs['dice_last_recharge']
            max_charges = dice_max_charges(owned)
            dice_charges = min(dice_charges, max_charges)
            dice_charges, last_recharge = dice._recharge_dice(dice_charges, last_recharge, max_charges, now_utc)

            # T220: Apply any pending dice roll before processing spins.
            # The pending dice was either buffered (if auto-spin was active
            # at roll time) or applied immediately (if not). In both cases
            # the input streak to the next spin is pd['new_streak'].
            # Loss handling: if the spin resolves as a 'lose', we revert the
            # streak to pd['original_streak'] and refund the dice charge
            # inside the loop below.
            pd = gs.get('pending_dice')
            if pd:
                streak      = pd['new_streak']
                best_streak = max(best_streak, streak) if streak > 0 else best_streak
            else:
                pd = None

            spin_results = []
            dice_refunded_this_tick = False

            for _ in range(spins_due):
                new_spin_count += 1
                new_state, events = _resolve_spin(
                    owned=owned,
                    streak=streak,
                    best_streak=best_streak,
                    regen_recharge_wins=regen_recharge_wins,
                    wins=current_wins,
                    losses=current_losses,
                    jackpot_echo_next=jackpot_echo_next,
                    spin_count=new_spin_count,
                    active_cosmetics=active_cosmetics,
                    proc_streak=current_proc_streak,
                    effective_win_mult=ctx['effective_win_mult'],
                    bonus_mult=ctx['bonus_mult'],
                    jackpot_chance=ctx['jackpot_chance'],
                    echo_chance=ctx['echo_chance'],
                    charm_chance=ctx['charm_chance'],
                    resilience_chance=ctx['resilience_chance'],
                    proc_streak_level=ctx['proc_streak_level'],
                    pot_active=pot_active,
                    pot_win_pct=pot_win_pct,
                    # T102: auto-spin always uses stake_pct=0 (safe), no wager streak
                    stake_pct=0,
                    wager_streak=0,
                    wager_last_stake=0,
                    active_wheel_mode=gs.get('active_wheel_mode', 'steady'),
                    aquarium_luck=ctx.get('aquarium_luck', 0.0),
                    wager_banked_wins=0,
                    # T77: gravity drift carries across the loop
                    gravity_drift=current_gravity_drift,
                    # T79: auto-spin doesn't bank losses (no stake)
                    wager_banked_losses=current_wager_banked_losses,
                )

                # Update carry-over state from result
                owned               = new_state['owned']
                streak              = new_state['streak']
                best_streak         = new_state['best_streak']
                regen_recharge_wins = new_state['regen_recharge_wins']
                current_wins        = new_state['wins']
                current_losses      = new_state['losses']
                jackpot_echo_next   = new_state['jackpot_echo_next']
                active_cosmetics    = new_state['active_cosmetics']
                current_proc_streak = new_state['proc_streak']
                # T77: drift may have shifted — propagate for the next spin.
                current_gravity_drift = new_state.get('gravity_drift', current_gravity_drift)
                current_wager_banked_losses = new_state.get('wager_banked_losses', current_wager_banked_losses)

                # T220: loss handler for pending dice. If this spin was a
                # loss AND there was a pending dice roll, revert the streak
                # to the pre-dice value and refund the dice charge. The
                # dice is single-shot — only the first spin in the tick
                # can consume it; subsequent spins in the same tick don't
                # see the dice (we clear `pd` below after the first spin).
                if pd and not dice_refunded_this_tick and events['result'] == 'lose':
                    original = pd.get('original_streak', streak)
                    streak = original
                    best_streak = max(best_streak, original) if original > 0 else best_streak
                    new_state['streak'] = original
                    new_state['best_streak'] = best_streak
                    dice_charges = min(dice_charges + 1, max_charges)
                    last_recharge = now_utc
                    dice_refunded_this_tick = True
                    log.info('DICE_REFUND_ON_LOSS  user_id=%s  path=tick  original_streak=%s  dice_sum=%s',
                             current_user.id, original, pd.get('dice_sum'))
                # Clear pd after first spin regardless of result so
                # subsequent spins in the same catch-up tick don't see it.
                pd = None

                new_win_count  += 1 if events['result'] == 'win'  else 0
                new_loss_count += 1 if events['result'] == 'lose' else 0
                # T106: cumulative_wins — track lifetime value of wins gained.
                new_cumulative_wins += max(0, int(events.get('wins_delta', 0)))

                # T221: jackpot chat messages are gone entirely (see /api/spin).
                # T90: auto-post chat messages (mirror T82 manual /api/spin path)
                if (int(events.get('wager_streak', 0)) == chat_triggers.HOT_STREAK_MSG_THRESHOLD):
                    post_dedup_system_message(
                        conn, chat_triggers.hot_streak_msg(current_user.username),
                        current_user.id, event_kind='hot_streak')
                new_biggest_win_announced = _maybe_announce_big_win(
                    conn, gs, events, current_user.username, current_user.id)
                gs['biggest_win_announced'] = new_biggest_win_announced

                if not is_catch_up:
                    resp = _events_to_response(events)
                    resp['angle'] = events['segment_angle']
                    resp['new_spin_count'] = new_spin_count
                    resp['dice_charges'] = dice_charges
                    resp['dice_last_recharge'] = last_recharge.isoformat()
                    # T106: echo the new cumulative_wins so the shop tier-locked
                    # text updates live during auto-spin too. Same fix as /api/spin.
                    resp['cumulative_wins'] = new_cumulative_wins
                    # T220: tell the client if the dice was refunded on this
                    # spin (loss path) so it can show the refund toast.
                    resp['dice_refunded'] = dice_refunded_this_tick
                    spin_results.append(resp)

            # Advance last_spin_at cursor
            new_last_spin = cursor + timedelta(seconds=spins_due * AUTO_SPIN_INTERVAL_SECONDS)

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET wins = %s, losses = %s, streak = %s, best_streak = %s,
                           regen_recharge_wins = %s,
                           owned_items = %s, spin_count = %s, win_count = %s, loss_count = %s,
                           cumulative_wins = %s,
                           active_cosmetics = %s, jackpot_echo_next = %s,
                           dice_charges = %s, dice_last_recharge = %s,
                           proc_streak = %s,
                           biggest_win_announced = %s,
                           gravity_drift = %s,
                           wager_banked_losses = %s,
                       dice_rolled_since_spin = FALSE, pending_dice = NULL,
                       last_spin_at = %s
                      WHERE user_id = %s''',
                    (current_wins, current_losses, streak, best_streak,
                     regen_recharge_wins,
                     owned, new_spin_count, new_win_count, new_loss_count,
                     new_cumulative_wins,
                     active_cosmetics, jackpot_echo_next,
                     dice_charges, last_recharge,
                     current_proc_streak,
                     new_biggest_win_announced,
                     current_gravity_drift,
                     current_wager_banked_losses,
                     new_last_spin,
                     current_user.id),
                )

            # Auto-fish AFK catch-up — process missed ticks in the same transaction
            fish_catchup_data = None
            if gs['auto_fish_enabled']:
                last_fish = gs['auto_fish_last_tick']
                if last_fish is not None:
                    last_fish = _aware(last_fish)
                    fish_elapsed = (now_utc - last_fish).total_seconds()
                    pending_fish = min(
                        int(fish_elapsed / AUTO_FISH_INTERVAL_SECONDS),
                        MAX_FISH_CATCHUP_TICKS,
                    )
                    if pending_fish >= FISH_CATCHUP_THRESHOLD:
                        autofisher_lvl = autofisher_level(owned)
                        if autofisher_lvl >= 1:
                            lure_lvl       = lure_level(owned)
                            _lm_mult       = lure_mastery_mult(gs['lure_mastery_level'])
                            _earth_mult    = 1.0 + CLASS_EARTH_FISH_BONUS if gs['equipped_class'] == 'earth' else 1.0
                            new_clicks     = int(gs['fish_clicks'])
                            new_caught     = list(gs['caught_species'])
                            total_value    = 0
                            catch_count    = 0
                            first_catches  = []
                            for _ in range(pending_fish):
                                if random.random() < autofisher_catch_rate(autofisher_lvl):
                                    sid = roll_fish(auto_mode=True, allow_rare=(autofisher_lvl >= 4))
                                    val = max(1, int(fish_value(sid, lure_lvl) * _lm_mult * _earth_mult))
                                    new_clicks  += val
                                    total_value += val
                                    catch_count += 1
                                    if sid not in new_caught:
                                        new_caught.append(sid)
                                        first_catches.append(sid)
                            with conn.cursor() as cur:
                                cur.execute(
                                    '''UPDATE game_state
                                       SET fish_clicks = %s, caught_species = %s,
                                           auto_fish_last_tick = %s
                                       WHERE user_id = %s''',
                                    (new_clicks, new_caught, now_utc, current_user.id),
                                )
                            fish_catchup_data = {
                                'fish_count':      catch_count,
                                'total_value':     total_value,
                                'new_species':     first_catches,
                                'fish_clicks':     new_clicks,
                                'elapsed_seconds': fish_elapsed,
                            }

            conn.commit()

        final_state = {
            'wins':                  int(current_wins),
            'losses':                current_losses,
            'streak':                streak,
            'owned_items':           owned,
            'regen_recharge_wins':   regen_recharge_wins,
            'active_cosmetics':      active_cosmetics,
            'spin_count':            new_spin_count,
            'win_count':             new_win_count,
            'dice_charges':          dice_charges,
            'dice_last_recharge':    last_recharge.isoformat(),
            'jackpot_echo_next':     jackpot_echo_next,
            'dice_rolled_since_spin': False,
            'proc_streak':           current_proc_streak,
            # T216: `auto_spin_budget` removed (migration 057). Auto-spin
            # is binary on/off now; reporting `auto_spin_active: true` here
            # signals the client that the session is still running.
            'auto_spin_active':      True,
            # T106: cumulative_wins after all processed spins (catch-up summary).
            'cumulative_wins':       new_cumulative_wins,
        }

        if is_catch_up:
            return jsonify({
                'catch_up':        True,
                'spins_processed': spins_due,
                'wins_gained':     current_wins - int(gs['wins']),
                'elapsed_seconds': elapsed,
                'state':           final_state,
                'fish_catchup':    fish_catchup_data,
            })

        return jsonify({
            'spins':        spin_results,
            'state':        final_state,
            'fish_catchup': fish_catchup_data,
        })

    except Exception:
        log.exception('TICK_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Tick failed'}), 500


@game_bp.route('/api/roll-dice', methods=['POST'])
@login_required
@limiter.limit('3 per second')
def roll_dice():
    err = require_json()
    if err:
        return err
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT wins, streak, best_streak, owned_items,
                              dice_charges, dice_last_recharge, dice_rolled_since_spin,
                              auto_spin_since
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned   = list(gs['owned_items'])
            now_utc = dt.datetime.now(timezone.utc)

            result = dice.roll_dice_core(gs, owned, now_utc)
            if not result['ok']:
                return jsonify({'error': result['error']}), result['status']

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET pending_dice = %s,
                           streak = %s, best_streak = CASE WHEN %s > best_streak THEN %s ELSE best_streak END,
                           dice_charges = %s, dice_last_recharge = %s,
                           dice_rolled_since_spin = TRUE
                       WHERE user_id = %s''',
                    (psycopg2.extras.Json(result['pending']),
                     result['new_streak_to_store'],
                     result['new_streak_to_store'], result['new_streak_to_store'],
                     result['new_charges'], result['new_last_recharge'],
                     current_user.id),
                )
            conn.commit()

        return jsonify({
            'die1':               result['dice'][0],
            'die2':               result['dice'][1],
            'die3':               result['dice'][2] if len(result['dice']) > 2 else None,
            'dice':               result['dice'],
            'dice_sum':           result['dice_sum'],
            'cursed':             result['cursed'] or result['cursed_triple'],
            'blessed':            result['blessed'] or result['blessed_triple'],
            'cursed_triple':      result['cursed_triple'],
            'blessed_triple':     result['blessed_triple'],
            'streak':             result['new_streak'],
            'wins':               int(gs['wins']),
            'dice_charges':       result['new_charges'],
            'dice_last_recharge': result['recharged_last_recharge'].isoformat(),
            'buffered':           not result['applied_immediately'],
            'applied_immediately': result['applied_immediately'],
        })
    except Exception:
        log.exception('ROLL_DICE_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Dice roll failed'}), 500


@game_bp.route('/api/buy', methods=['POST'])
@login_required
def buy():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id') or ''
    if item_id in RETIRED_S9_ITEMS:
        return jsonify({'error': 'This item was retired in Season 9.'}), 403

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                gs = _load_game_state(cur, current_user.id, for_update=True)
                result = shop.buy_core(cur, conn, item_id, current_user.id, gs)
            if isinstance(result, tuple):
                status, body = result
                return jsonify(body), status
            conn.commit()
            return jsonify(result)
    except Exception:
        log.exception('BUY_ERROR  user_id=%s  item_id=%s', current_user.id, item_id)
        return jsonify({'error': 'Purchase failed'}), 500


@game_bp.route('/api/community-pot')
@login_required
def community_pot_state():
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT total_contributed, target, win_chance_pct, filled, filled_at FROM community_pot WHERE id = 1')
                pot = cur.fetchone()
                total_pending_clicks = get_total_fish_clicks(cur)
            if not pot:
                return jsonify({'total_contributed': 0, 'target': 1_000, 'filled': False, 'active': False, 'win_chance_pct': 50.0, 'total_pending_clicks': total_pending_clicks})
            now_utc = dt.datetime.now(timezone.utc)
            pot_active = _pot_boost_active(pot, now_utc)
            if pot['filled'] and not pot_active:
                new_pot_target = _reset_expired_pot(conn, pot)
                conn.commit()
                pot = dict(pot)
                pot['filled'] = False
                pot['total_contributed'] = 0
                pot['target'] = new_pot_target
        return jsonify({
            'total_contributed':   pot['total_contributed'],
            'target':              pot['target'],
            'filled':              pot['filled'],
            'active':              pot_active,
            'win_chance_pct':      float(pot['win_chance_pct']),
            'filled_at':           pot['filled_at'].isoformat() if pot['filled_at'] else None,
            'total_pending_clicks': total_pending_clicks,
        })
    except Exception:
        log.exception('COMMUNITY_POT_STATE_ERROR')
        return jsonify({'error': 'Failed to load pot'}), 500


@game_bp.route('/api/community-pot/contribute', methods=['POST'])
@login_required
@limiter.limit('5 per second')
def community_pot_contribute():
    err = require_json()
    if err:
        return err
    data        = request.get_json(silent=True) or {}
    amount_type = data.get('amount', 'all')  # '10pct' or 'all'
    if amount_type not in ('10pct', 'all'):
        return jsonify({'error': 'Invalid amount type'}), 400

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT fish_clicks FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()
                cur.execute(
                    'SELECT total_contributed, target, win_chance_pct, filled, filled_at, last_decay_check FROM community_pot WHERE id = 1 FOR UPDATE'
                )
                pot = cur.fetchone()

            if not pot:
                return jsonify({'error': 'Pot not found'}), 500

            now_utc = dt.datetime.now(timezone.utc)

            if pot['filled']:
                if _pot_boost_active(pot, now_utc):
                    return jsonify({'error': 'Pot is active — wait for the boost to expire'}), 400
                new_exp_target = _reset_expired_pot(conn, pot)
                pot = dict(pot)
                pot['filled'] = False
                pot['total_contributed'] = 0
                pot['target'] = new_exp_target

            # Apply decay if 12+ hours since last check
            effective_target = _apply_pot_decay(conn, pot, now_utc)

            fish_clicks  = gs['fish_clicks']
            happy_hour   = is_happy_hour(now_utc)
            if amount_type == '10pct':
                base = min(max(1, effective_target // 10), fish_clicks)
            else:
                base = fish_clicks
            # Happy hour: double contribution value (capped to what the player has)
            contribute = min(base * 2, fish_clicks) if happy_hour else base

            if contribute <= 0:
                return jsonify({'error': 'No fish bucks to contribute'}), 400

            # Cap at remaining target
            remaining    = effective_target - int(pot['total_contributed'])
            contribute   = min(contribute, max(0, remaining))
            if contribute <= 0:
                return jsonify({'error': 'Pot already full — wait for next cycle'}), 400
            new_total    = int(pot['total_contributed']) + contribute
            newly_filled = new_total >= effective_target

            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET fish_clicks = fish_clicks - %s WHERE user_id = %s',
                    (contribute, current_user.id),
                )
                if newly_filled:
                    new_pct = min(float(pot['win_chance_pct']) + 0.5, 75.0)
                    cur.execute(
                        '''UPDATE community_pot
                           SET total_contributed = %s,
                               filled = true, filled_at = now(),
                               win_chance_pct = %s
                           WHERE id = 1''',
                        (new_total, new_pct),
                    )
                else:
                    cur.execute(
                        'UPDATE community_pot SET total_contributed = %s WHERE id = 1',
                        (new_total,),
                    )
            conn.commit()

        if newly_filled:
            ret_total    = new_total
            ret_target   = effective_target
            ret_pct      = new_pct
            ret_filled_at = dt.datetime.now(timezone.utc).isoformat()
        else:
            ret_total    = new_total
            ret_target   = effective_target
            ret_pct      = float(pot['win_chance_pct'])
            ret_filled_at = pot['filled_at'].isoformat() if pot['filled_at'] else None

        return jsonify({
            'fish_clicks':    fish_clicks - contribute,
            'contributed':    contribute,
            'pot_total':      ret_total,
            'pot_target':     ret_target,
            'pot_filled':     newly_filled,
            'pot_active':     newly_filled,
            'win_chance_pct': ret_pct,
            'filled_at':      ret_filled_at,
        })
    except Exception:
        log.exception('CONTRIBUTE_POT_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Contribution failed'}), 500


@game_bp.route('/api/equip', methods=['POST'])
@login_required
def equip():
    """T245: logic moved to loadout.equip_fish_core."""
    err = require_json()
    if err:
        return err

    data    = request.get_json(silent=True) or {}
    fish_id = data.get('fish_id') or ''

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                result = loadout.equip_fish_core(cur, conn, current_user.id, fish_id)
            conn.commit()
        if isinstance(result, tuple):
            return jsonify(result[1]), result[0]
        return jsonify(result)
    except Exception:
        log.exception('EQUIP_ERROR  user_id=%s  fish_id=%s', current_user.id, fish_id)
        return jsonify({'error': 'Equip failed'}), 500


# ── Fishing routes ─────────────────────────────────────────────────────────
# T240: logic moved to fish.py. These are thin route handlers that open
# the transaction, call into fish, and render the response. The
# response shape is unchanged from the pre-extraction version — the
# React client depends on it.

@game_bp.route('/api/cast', methods=['POST'])
@login_required
@limiter.limit('5 per second')
def cast_line():
    err = require_json()
    if err:
        return err
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                result = fish.cast_line(cur, current_user.id,
                                        dt.datetime.now(timezone.utc))
            conn.commit()
        if isinstance(result, tuple):
            return jsonify(result[1]), result[0]
        return jsonify(result)
    except Exception:
        log.exception('CAST_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Cast failed'}), 500


@game_bp.route('/api/bite-poll', methods=['POST'])
@login_required
@limiter.limit('4 per second')
def bite_poll():
    err = require_json()
    if err:
        return err
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                result = fish.bite_poll(cur, current_user.id,
                                        dt.datetime.now(timezone.utc))
        return jsonify(result)
    except Exception:
        log.exception('BITE_POLL_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Poll failed'}), 500


@game_bp.route('/api/reel', methods=['POST'])
@login_required
@limiter.limit('5 per second')
def reel_line():
    err = require_json()
    if err:
        return err
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                result = fish.reel_line(cur, conn, current_user.id,
                                        dt.datetime.now(timezone.utc))
            conn.commit()
        if isinstance(result, tuple):
            return jsonify(result[1]), result[0]
        return jsonify(result)
    except Exception:
        log.exception('REEL_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Reel failed'}), 500


@game_bp.route('/api/auto-fish-tick', methods=['POST'])
@login_required
@limiter.limit('1 per 5 second')
def auto_fish_tick():
    err = require_json()
    if err:
        return err
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                result = fish.auto_fish_tick(cur, conn, current_user.id,
                                             dt.datetime.now(timezone.utc))
            conn.commit()
        if isinstance(result, tuple):
            return jsonify(result[1]), result[0]
        return jsonify(result)
    except Exception:
        log.exception('AUTO_FISH_TICK_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Auto fish tick failed'}), 500


@game_bp.route('/api/auto-fish-enabled', methods=['POST'])
@login_required
@limiter.limit('10 per minute')
def set_auto_fish_enabled():
    err = require_json()
    if err:
        return err
    try:
        data = request.get_json()
        requested = bool(data.get('enabled', False))
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                result = fish.set_auto_fish_enabled(
                    cur, conn, current_user.id, requested,
                    dt.datetime.now(timezone.utc),
                )
            conn.commit()
        return jsonify(result)
    except Exception:
        log.exception('AUTO_FISH_ENABLED_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Failed to update auto fish state'}), 500


@game_bp.route('/api/equip-class', methods=['POST'])
@login_required
@limiter.limit('20 per minute')
def equip_class():
    """T245: logic moved to loadout.equip_class_core."""
    err = require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    class_id = data.get('class_id')  # 'class_earth' | 'class_moon' | 'class_star' | None

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                result = loadout.equip_class_core(cur, conn, current_user.id, class_id)
            conn.commit()
        if isinstance(result, tuple):
            return jsonify(result[1]), result[0]
        return jsonify(result)
    except Exception:
        log.exception('EQUIP_CLASS_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Failed to equip class'}), 500


@game_bp.route('/api/fish-exchange', methods=['POST'])
@login_required
@limiter.limit('5 per second')
def fish_exchange():
    err = require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    amount_type = data.get('amount', '10pct')
    if amount_type not in ('10pct', 'all'):
        return jsonify({'error': 'Invalid amount type'}), 400

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT fish_clicks, fish_exchange_total FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            fish_clicks = int(gs['fish_clicks'])
            if fish_clicks <= 0:
                return jsonify({'error': 'No fish bucks to exchange'}), 400

            fish_to_exchange = max(1, fish_clicks // 10) if amount_type == '10pct' else fish_clicks

            # Linear decay: 1:1 for first 25M exchanged, then decays to a 10% floor by 125M
            exchange_total = int(gs['fish_exchange_total'])
            if exchange_total < 25_000_000:
                rate = 1.0
            elif exchange_total < 125_000_000:
                t = (exchange_total - 25_000_000) / 100_000_000
                rate = max(0.10, 1.0 - 0.90 * t)
            else:
                rate = 0.10
            wins_earned = max(1, int(fish_to_exchange * rate))

            new_fish           = fish_clicks - fish_to_exchange
            new_exchange_total = exchange_total + fish_to_exchange

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET fish_clicks = %s, wins = wins + %s, fish_exchange_total = %s
                       WHERE user_id = %s''',
                    (new_fish, wins_earned, new_exchange_total, current_user.id),
                )
                cur.execute('SELECT wins FROM game_state WHERE user_id = %s', (current_user.id,))
                updated_wins = cur.fetchone()[0]
            conn.commit()

        return jsonify({
            'ok':          True,
            'fish_spent':  fish_to_exchange,
            'wins_earned': wins_earned,
            'rate':        round(rate, 3),
            'fish_clicks': new_fish,
            'wins':        int(updated_wins),
        })
    except Exception:
        log.exception('FISH_EXCHANGE_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Exchange failed'}), 500


@game_bp.route('/api/wins-exchange', methods=['POST'])
@login_required
@limiter.limit('5 per second')
def wins_exchange():
    err = require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    amount_type = data.get('amount', '10pct')
    if amount_type not in ('10pct', 'all'):
        return jsonify({'error': 'Invalid amount type'}), 400

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT wins FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            current_wins = int(gs['wins'])
            if current_wins <= 0:
                return jsonify({'error': 'No wins to exchange'}), 400

            wins_to_exchange = max(1, current_wins // 10) if amount_type == '10pct' else current_wins
            fish_earned = wins_to_exchange  # 1:1 rate

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET wins = wins - %s, fish_clicks = fish_clicks + %s
                       WHERE user_id = %s''',
                    (wins_to_exchange, fish_earned, current_user.id),
                )
                cur.execute('SELECT wins, fish_clicks FROM game_state WHERE user_id = %s', (current_user.id,))
                row = cur.fetchone()
                updated_wins, updated_fish = row[0], row[1]
            conn.commit()

        return jsonify({
            'ok':          True,
            'wins_spent':  wins_to_exchange,
            'fish_earned': fish_earned,
            'wins':        int(updated_wins),
            'fish_clicks': int(updated_fish),
        })
    except Exception:
        log.exception('WINS_EXCHANGE_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Exchange failed'}), 500



@game_bp.route('/api/equip-cosmetic', methods=['POST'])
@login_required
def equip_cosmetic():
    """T245: logic moved to loadout.equip_cosmetic_core."""
    err = require_json()
    if err:
        return err

    data    = request.get_json(silent=True) or {}
    item_id = data.get('item_id') or ''

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                result = loadout.equip_cosmetic_core(cur, conn, current_user.id, item_id)
            conn.commit()
        if isinstance(result, tuple):
            return jsonify(result[1]), result[0]
        return jsonify(result)
    except Exception:
        log.exception('EQUIP_COSMETIC_ERROR  user_id=%s  item_id=%s', current_user.id, item_id)
        return jsonify({'error': 'Equip failed'}), 500


@game_bp.route('/api/stats')
@login_required
def stats():
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT spin_count, win_count, loss_count, fish_clicks, total_fish_clicks, fastest_catch_pct FROM game_state WHERE user_id = %s',
                    (current_user.id,)
                )
                row = cur.fetchone()
                cur.execute('SELECT season_number FROM seasons ORDER BY id LIMIT 1')
                season_row = cur.fetchone()
                current_season = season_row['season_number'] if season_row else 1
                cur.execute(
                    '''SELECT season_number, finishing_position, final_wins, final_losses
                       FROM user_season_history
                       WHERE user_id = %s
                       ORDER BY season_number''',
                    (current_user.id,)
                )
                history_rows = cur.fetchall()

        # Build a lookup of user's history by season number
        history_by_season = {r['season_number']: r for r in history_rows}
        # Show all completed seasons (1 through current-1); blank if user has no entry
        season_history = []
        for sn in range(1, current_season):
            h = history_by_season.get(sn)
            season_history.append({
                'season_number':      sn,
                'finishing_position': h['finishing_position'] if h else None,
                'final_wins':         int(h['final_wins']) if h else None,
            })

        return jsonify({
            'spin_count':         row['spin_count'],
            'win_count':          row['win_count'],
            'loss_count':         row['loss_count'],
            'fish_clicks':        row['fish_clicks'],
            'total_fish_clicks':  row['total_fish_clicks'],
            'fastest_catch_pct':  row['fastest_catch_pct'],
            'season_history':     season_history,
        })
    except Exception:
        log.exception('STATS_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Failed to load stats'}), 500


@game_bp.route('/api/hall-of-fame')
@limiter.limit('30 per minute')
def hall_of_fame():
    """Every ended season/tide newest first with its podium, plus S9 medal counts.
    Podiums come from season_snapshots, which already excludes test users."""
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT l.season_number, l.label, l.name, l.ended_at,
                              s.position, s.username, s.wins
                       FROM season_log l
                       LEFT JOIN season_snapshots s ON s.season_number = l.season_number
                       ORDER BY l.season_number DESC, s.position'''
                )
                rows = cur.fetchall()
                cur.execute(
                    '''SELECT s.username,
                              COUNT(*) FILTER (WHERE s.position = 1) AS gold,
                              COUNT(*) FILTER (WHERE s.position = 2) AS silver,
                              COUNT(*) FILTER (WHERE s.position = 3) AS bronze
                       FROM season_snapshots s
                       JOIN season_log l ON l.season_number = s.season_number
                       WHERE l.label LIKE '9.%%'
                       GROUP BY s.username
                       ORDER BY gold DESC, silver DESC, bronze DESC, s.username'''
                )
                medals = cur.fetchall()
        tides = {}
        for r in rows:
            t = tides.setdefault(r['season_number'], {
                'label': r['label'], 'name': r['name'],
                'ended_at': r['ended_at'].isoformat() if r['ended_at'] else None,
                'podium': []})
            if r['position'] is not None:
                t['podium'].append({'position': r['position'], 'username': r['username'],
                                    'wins': int(r['wins'])})
        return jsonify({'tides': list(tides.values()), 'medals': [dict(m) for m in medals]})
    except Exception:
        log.exception('HALL_OF_FAME_ERROR')
        return jsonify({'error': 'Could not load the Hall of Fame.'}), 500


@game_bp.route('/api/leaderboard')
@limiter.limit('30 per minute')
def leaderboard():
    try:
        with db_connection() as conn:
            ensure_current_season(conn)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # T241: hide test users (pytest runs against the prod DB, so
                # 127.0.0.1 means "created by a test"). The 8 real players
                # connect from 192.168.68.10; never localhost. Filtering here
                # keeps the leaderboard clean for every viewer, server-side.
                cur.execute(
                    '''SELECT u.username, gs.wins, gs.losses, gs.streak, gs.best_streak,
                              gs.last_spin_at
                       FROM game_state gs
                       JOIN users u ON u.id = gs.user_id
                       WHERE gs.wins > 0
                         AND u.ip_address <> '127.0.0.1'
                       ORDER BY gs.wins DESC
                       LIMIT 10'''
                )
                rows = cur.fetchall()
        now_utc = dt.datetime.now(timezone.utc)
        result = []
        for r in rows:
            last_spin = r['last_spin_at']
            last_spin = _aware(last_spin)
            active = last_spin and (now_utc - last_spin).total_seconds() < 86400
            result.append({
                'username':        r['username'],
                'wins':            int(r['wins']),
                'losses':          r['losses'],
                'streak':          r['streak'],
                'best_streak':     r['best_streak'],
                'active':          bool(active),
            })
        return jsonify(result)
    except Exception:
        log.exception('LEADERBOARD_ERROR')
        return jsonify([])


_PATCH_NOTES_PATH = os.path.join(os.path.dirname(__file__), 'PATCH_NOTES.md')
_patch_notes_cache: dict = {'mtime': None, 'content': None}


@game_bp.route('/api/patch-notes')
@limiter.limit('20 per minute')
def get_patch_notes():
    """Public endpoint that returns raw PATCH_NOTES.md content (mtime-cached)."""
    try:
        mtime = os.path.getmtime(_PATCH_NOTES_PATH)
        if _patch_notes_cache['mtime'] != mtime:
            with open(_PATCH_NOTES_PATH, 'r', encoding='utf-8') as f:
                _patch_notes_cache['content'] = f.read()
            _patch_notes_cache['mtime'] = mtime
        return jsonify({'content': _patch_notes_cache['content']})
    except Exception:
        log.exception('PATCH_NOTES_ERROR')
        return jsonify({'error': 'Failed to load patch notes'}), 500


@game_bp.route('/api/season')
@limiter.limit('60 per minute')
def get_season():
    """Public endpoint for season info. Used by cron safety net and frontend polling."""
    try:
        with db_connection() as conn:
            ensure_current_season(conn)
            info = get_season_info(conn)
        info['happy_hour'] = is_happy_hour()
        return jsonify(info)
    except Exception:
        log.exception('GET_SEASON_ERROR')
        return jsonify({'error': 'Failed to load season'}), 500


@game_bp.route('/api/admin/advance-season', methods=['POST'])
@csrf.exempt
def admin_advance_season():
    """Manually advance the season. Requires X-Admin-Secret header."""
    secret = os.environ.get('ADMIN_SECRET', '')
    if not secret:
        log.warning('ADMIN_SECRET not configured — advance-season endpoint is disabled')
        return jsonify({'error': 'Forbidden'}), 403
    provided = request.headers.get('X-Admin-Secret', '')
    if not hmac.compare_digest(provided.encode(), secret.encode()):
        return jsonify({'error': 'Forbidden'}), 403
    try:
        with db_connection() as conn:
            advance_season(conn)
        return jsonify({'ok': True})
    except Exception:
        log.exception('ADMIN_ADVANCE_SEASON_ERROR')
        return jsonify({'error': 'Failed to advance season'}), 500


# ════════════════════════════════════════════════════════════════════════════
# Season 8 API Endpoints
# ════════════════════════════════════════════════════════════════════════════

@game_bp.route('/api/wager/bank', methods=['POST'])
@login_required
def wager_bank():
    """Bank wager_banked_wins into wins AND wager_banked_losses into losses,
    then reset wager_streak to 0. The same double-down-pending guard from
    T72 covers both — banking mid-bet is forbidden for either side.
    """
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            # T72: refuse to bank while a double-down is armed. Banking mid
            # double-down would forfeit the in-flight 2x-stake bet (the
            # double-down's "wins at risk" semantics are then violated). The
            # player must resolve the pending spin (or cancel) first.
            # T79: same guard applies to inverted-mode banked losses.
            if gs.get('double_down_pending'):
                return jsonify({'error': 'Cannot bank while double-down is pending'}), 409
            banked_wins = int(gs.get('wager_banked_wins', 0))
            # T79: also bank wager_banked_losses (inverted-mode loss-farming).
            banked_losses = int(gs.get('wager_banked_losses', 0))
            # Tolerate missing 'losses' key (some test fixtures predate T79).
            current_losses = int(gs.get('losses', 0) or 0)
            if banked_wins <= 0 and banked_losses <= 0:
                return jsonify({'error': 'No banked wins or losses to claim'}), 400
            new_wins   = int(gs['wins']) + banked_wins
            new_losses = current_losses + banked_losses
            cur.execute(
                '''UPDATE game_state
                   SET wins = %s, losses = %s,
                       wager_banked_wins = 0, wager_banked_losses = 0,
                       wager_streak = 0
                   WHERE user_id = %s''',
                (new_wins, new_losses, current_user.id),
            )
        bounty_date = dt.datetime.now(timezone.utc).date()
        increment_bounty(conn, current_user.id, 'bounty_bank', bounty_date)
        conn.commit()
    return jsonify({
        'wins':               new_wins,
        'losses':             new_losses,
        'wager_streak':       0,
        'banked_wins':        banked_wins,
        'banked_losses':      banked_losses,
        'banked':             banked_wins,  # legacy field (T72)
    })

@game_bp.route('/api/wager/stake', methods=['POST'])
@login_required
def wager_set_stake():
    """Set the wager stake percentage for manual spins. Validates against wager_unlock."""
    err = require_json()
    if err:
        return err
    # T102: stake field is now stake_pct (0-45 percentage, 5% steps).
    stake = (request.json or {}).get('stake', 0)
    try:
        stake = int(stake)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid stake'}), 400
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            owns_unlock = 'wager_unlock' in gs['owned_items']
            # T102: clamp to player's max stake (30 base, up to 45 with items).
            max_pct = compute_max_stake_pct(list(gs.get('owned_items', [])))
            actual_stake = validate_stake(stake, owns_unlock, max_pct)
            cur.execute('UPDATE game_state SET wager_last_stake = %s WHERE user_id = %s',
                        (actual_stake, current_user.id))
            # T102: onboarding advances 1→2 when first non-zero stake is set.
            # The 0% (safe) position is a real, valid stake; "actual_stake > 0"
            # is the right gate now (was "> 1" in the multiplier system).
            if actual_stake > 0 and owns_unlock and gs.get('onboarding_step', 0) == 1:
                cur.execute(
                    '''UPDATE game_state
                       SET onboarding_step = 2,
                           owned_items = CASE WHEN NOT (owned_items @> ARRAY['confetti_1'])
                               THEN array_append(owned_items, 'confetti_1') ELSE owned_items END,
                           active_cosmetics = CASE WHEN NOT (active_cosmetics @> ARRAY['confetti_1'])
                               THEN array_append(active_cosmetics, 'confetti_1') ELSE active_cosmetics END
                       WHERE user_id = %s''',
                    (current_user.id,),
                )
        conn.commit()
    return jsonify({'stake': actual_stake, 'max_stake_pct': max_pct})


@game_bp.route('/api/wager/double-down', methods=['POST'])
@login_required
def wager_double_down():
    """Double down: next spin uses 2× stake. Only if wager_double_down owned."""
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'wager_double_down' not in gs['owned_items']:
                return jsonify({'error': 'Double down not unlocked'}), 403
            if gs.get('double_down_pending'):
                return jsonify({'error': 'Double down already pending'}), 409
            cur.execute('UPDATE game_state SET double_down_pending = TRUE WHERE user_id = %s',
                        (current_user.id,))
        conn.commit()
    return jsonify({'ok': True, 'message': 'Double down armed for next spin'})


@game_bp.route('/api/wager/double-down/cancel', methods=['POST'])
@login_required
def wager_double_down_cancel():
    """T108: cancel an armed double-down. No item ownership required."""
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if not gs.get('double_down_pending'):
                return jsonify({'error': 'Double down not armed'}), 409
            cur.execute('UPDATE game_state SET double_down_pending = FALSE WHERE user_id = %s',
                        (current_user.id,))
        conn.commit()
    return jsonify({'ok': True})


@game_bp.route('/api/insurance/arm', methods=['POST'])
@login_required
def wager_insurance():
    """T119: Arm insurance. Consumes 1 insurance_token per arm (was: 1
    charge). No recharge, no cap. Charge is wasted on a win (by design,
    inherited from T74)."""
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'wager_insurance' not in gs['owned_items']:
                return jsonify({'error': 'Insurance not unlocked'}), 403
            if gs.get('insurance_armed'):
                return jsonify({'error': 'Insurance already armed'}), 409
            current_tokens = int(gs.get('insurance_tokens', 0) or 0)
            if current_tokens < 1:
                return jsonify({'error': 'No insurance tokens left'}), 403
            new_tokens = current_tokens - 1
            cur.execute(
                '''UPDATE game_state
                   SET insurance_tokens = %s,
                       insurance_armed = TRUE
                   WHERE user_id = %s''',
                (new_tokens, current_user.id),
            )
        conn.commit()
    return jsonify({'ok': True, 'message': 'Insurance activated',
                    'insurance_tokens': new_tokens})


@game_bp.route('/api/insurance/cancel', methods=['POST'])
@login_required
def wager_insurance_cancel():
    """T108/T119: cancel armed insurance. The 1 insurance_token consumed
    on arm is NOT refunded — by design (T74: charge is wasted on a win
    too). The player takes the loss; that's the gamble."""
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if not gs.get('insurance_armed'):
                return jsonify({'error': 'Insurance not armed'}), 409
            cur.execute('UPDATE game_state SET insurance_armed = FALSE WHERE user_id = %s',
                        (current_user.id,))
        conn.commit()
    return jsonify({'ok': True})


@game_bp.route('/api/insurance/buy', methods=['POST'])
@login_required
def insurance_buy_with_tokens():
    """T119: spend insurance tokens to buy insurance charges. 1 token =
    1 charge (fixed rate). No cap — players can stockpile as many
    charges as they've bought."""
    err = require_json()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    try:
        token_cost = int(body.get('token_cost', 1))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token_cost'}), 400
    if token_cost < 1:
        return jsonify({'error': 'token_cost must be >= 1'}), 400
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'fish_to_wager' not in gs['owned_items']:
                return jsonify({'error': 'fish_to_wager not unlocked'}), 403
            if 'wager_insurance' not in gs['owned_items']:
                return jsonify({'error': 'Insurance not unlocked'}), 403
            current_tokens = int(gs.get('insurance_tokens', 0) or 0)
            if current_tokens < token_cost:
                return jsonify({'error': 'Not enough insurance tokens'}), 400
            new_tokens = current_tokens - token_cost
            new_charges = int(gs.get('insurance_charges', 0) or 0) + token_cost
            cur.execute(
                '''UPDATE game_state
                   SET insurance_tokens = %s,
                       insurance_charges = %s
                   WHERE user_id = %s''',
                (new_tokens, new_charges, current_user.id),
            )
        conn.commit()
    return jsonify({
        'ok': True,
        'insurance_tokens': new_tokens,
        'insurance_charges': new_charges,
        'granted': token_cost,
    })


@game_bp.route('/api/insurance/claim-free', methods=['POST'])
@login_required
def insurance_claim_free():
    """T119: claim 3 free insurance tokens once per UTC day. Gated on
    the `insurance_free_claimed_date` column — if today's date equals
    the stored date, the request is rejected with 409. The atomic
    check inside the FOR UPDATE transaction prevents double-claims
    when two concurrent requests race the gate."""
    err = require_json()
    if err:
        return err
    FREE_PER_DAY = 3
    today = dt.datetime.now(timezone.utc).date()
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if gs.get('insurance_free_claimed_date') == today:
                return jsonify({'error': 'Already claimed today'}), 409
            cur.execute(
                '''UPDATE game_state
                   SET insurance_tokens = insurance_tokens + %s,
                       insurance_free_claimed_date = %s
                   WHERE user_id = %s
                   RETURNING insurance_tokens''',
                (FREE_PER_DAY, today, current_user.id),
            )
            new_tokens = int(cur.fetchone()['insurance_tokens'])
        conn.commit()
    return jsonify({'ok': True, 'tokens_awarded': FREE_PER_DAY,
                    'insurance_tokens': new_tokens})


@game_bp.route('/api/prestige', methods=['POST'])
@login_required
def prestige_reset():
    return jsonify({'error': 'Retired in Season 9.'}), 410


@game_bp.route('/api/prestige', methods=['GET'])
@login_required
def prestige_info():
    return jsonify({'error': 'Retired in Season 9.'}), 410


@game_bp.route('/api/bounties', methods=['GET'])
@login_required
def get_bounties_endpoint():
    """Get today's bounty status.

    T119: onboarding step 3 (visit bounties panel) used to grant 100
    wager_tokens. That earning path is now gone — the new free-claim,
    per-bounty, and initial-purchase paths are the only sources. The
    step is still advanced so the modal disappears, but no tokens
    are credited.
    """
    bounty_date = dt.datetime.now(timezone.utc).date()
    onboarding_advance = False
    with db_connection() as conn:
        status = get_bounty_status(conn, current_user.id, bounty_date)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                '''SELECT onboarding_step FROM game_state WHERE user_id = %s FOR UPDATE''',
                (current_user.id,),
            )
            gs = cur.fetchone()
            if gs and gs.get('onboarding_step', 0) == 3:
                cur.execute(
                    '''UPDATE game_state
                       SET onboarding_step = 5
                       WHERE user_id = %s''',
                    (current_user.id,),
                )
                onboarding_advance = True
        conn.commit()
    return jsonify({'bounties': status, 'date': str(bounty_date), 'onboarding_advance': onboarding_advance})


@game_bp.route('/api/bounties/claim', methods=['POST'])
@login_required
def claim_bounty():
    """Claim a completed bounty (per-bounty, T117)."""
    err = require_json()
    if err:
        return err
    bounty_id = (request.json or {}).get('bounty_id')
    if not bounty_id:
        return jsonify({'error': 'bounty_id required'}), 400
    bounty_date = dt.datetime.now(timezone.utc).date()
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            rewards = get_claim_rewards_for_bounty(conn, current_user.id, bounty_date, bounty_id)
            if rewards is None:
                return jsonify({'error': 'Bounty not claimable'}), 400
            cur.execute(
                '''SELECT completed, claimed FROM bounty_progress
                   WHERE user_id = %s AND bounty_date = %s AND bounty_id = %s
                   FOR UPDATE''',
                (current_user.id, bounty_date, bounty_id),
            )
            row = cur.fetchone()
            if not row or not row.get('completed'):
                return jsonify({'error': 'Bounty not completed'}), 400
            if row.get('claimed'):
                return jsonify({'error': 'Already claimed'}), 400
            cur.execute(
                '''UPDATE bounty_progress
                   SET claimed = TRUE, claimed_at = NOW()
                   WHERE user_id = %s AND bounty_date = %s AND bounty_id = %s''',
                (current_user.id, bounty_date, bounty_id),
            )
            cur.execute(
                '''UPDATE game_state SET insurance_tokens = insurance_tokens + %s
                   WHERE user_id = %s''',
                (rewards['tokens'], current_user.id),
            )
        conn.commit()
    return jsonify({'ok': True, 'rewards': rewards})


@game_bp.route('/api/community-goal', methods=['GET'])
@login_required
def community_goal_endpoint():
    """Get active community goal status."""
    with db_connection() as conn:
        season_info = get_season_info(conn)
        season_num = season_info.get('season_number', 8) if season_info else 8
        now_utc = dt.datetime.now(timezone.utc)
        week_num = get_week_number(now_utc)
        goal_row, goal_def = get_active_goal(conn, season_num, week_num)
        player_contrib = get_player_contribution(conn, goal_def['goal_id'], current_user.id) if goal_row else 0
    if not goal_def:
        return jsonify({'goal': None})
    return jsonify({
        'goal': {
            'goal_id':     goal_def['goal_id'],
            'description': goal_def['description'],
            'target':      goal_def['target'],
            'current':     goal_row['current'] if goal_row else 0,
            'completed':   goal_row['completed'] if goal_row else False,
            'player_contribution': player_contrib,
            'per_player_cap': goal_def['per_player_cap'],
        }
    })


@game_bp.route('/api/singularity', methods=['GET'])
@login_required
def singularity_status():
    return jsonify({'error': 'Retired in Season 9.'}), 410


@game_bp.route('/api/singularity/contribute', methods=['POST'])
@login_required
def singularity_contribute():
    return jsonify({'error': 'Retired in Season 9.'}), 410


@game_bp.route('/api/loadout', methods=['GET'])
@login_required
def get_loadout():
    return jsonify({'error': 'Retired in Season 9.'}), 410


@game_bp.route('/api/loadout', methods=['POST'])
@login_required
def save_loadout():
    return jsonify({'error': 'Retired in Season 9.'}), 410


@game_bp.route('/api/loadout/apply', methods=['POST'])
@login_required
def apply_loadout():
    return jsonify({'error': 'Retired in Season 9.'}), 410


@game_bp.route('/api/guard', methods=['POST'])
@login_required
def guard_endpoint():
    """Manually trigger a guard charge to block a loss. Only if guard_charges > 0."""
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if gs.get('guard_charges', 0) <= 0:
                return jsonify({'error': 'No guard charges'}), 403
            if 'guard' not in gs['owned_items']:
                return jsonify({'error': 'Guard not owned'}), 403
            cur.execute('UPDATE game_state SET guard_charges = guard_charges - 1 WHERE user_id = %s',
                        (current_user.id,))
        conn.commit()
    return jsonify({'ok': True, 'message': 'Guard activated'})


@game_bp.route('/api/auto-spin/start', methods=['POST'])
@login_required
def auto_spin_start():
    """Start server-side auto-spin.

    T107: gated on the `auto_spin_unlock` shop item. The auto-spin UI is
    hidden in the wager panel for players who haven't bought the upgrade.

    T216: the per-activation 100-spin budget was removed (see migration
    057). Auto-spin now runs continuously until the user explicitly stops
    it OR the heartbeat auto-stop in /api/tick fires (60s of no /api/tick
    from this session). The `budget` request body field is ignored for
    backward compatibility.
    """
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'auto_spin_unlock' not in (gs.get('owned_items') or []):
                return jsonify({'error': 'Buy auto_spin_unlock from the shop (5,000 wins)'}), 403
            # T216: `auto_spin_since` is the sole signal. A stale timestamp
            # left over from a prior session / tab-closed-but-not-stopped
            # event still counts as 'active' — the heartbeat auto-stop will
            # clear it on the next /api/tick if it's actually stale.
            if gs.get('auto_spin_since') is not None:
                return jsonify({'error': 'Auto-spin already active'}), 409
            cur.execute(
                '''UPDATE game_state
                   SET auto_spin_since = NOW()
                   WHERE user_id = %s''',
                (current_user.id,),
            )
        conn.commit()
    return jsonify({'ok': True})


@game_bp.route('/api/auto-spin/stop', methods=['POST'])
@login_required
def auto_spin_stop():
    """Stop server-side auto-spin."""
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor() as cur:
            # T216: the `auto_spin_budget` column was dropped (migration 057).
            # Only `auto_spin_since` needs clearing now.
            cur.execute(
                '''UPDATE game_state SET auto_spin_since = NULL WHERE user_id = %s''',
                (current_user.id,),
            )
        conn.commit()
    return jsonify({'ok': True})


@game_bp.route('/api/aquarium', methods=['GET'])
@login_required
def aquarium_status():
    return jsonify({'error': 'Retired in Season 9.'}), 410


@game_bp.route('/api/wheel-mode', methods=['POST'])
@login_required
def set_wheel_mode():
    """Set the active wheel mode for the week."""
    err = require_json()
    if err:
        return err
    mode = (request.json or {}).get('mode', 'steady')
    now_utc = dt.datetime.now(timezone.utc)
    week_num = get_week_number(now_utc)
    available = get_available_modes(week_num)
    if mode not in available and mode != 'steady':
        return jsonify({'error': 'Mode not available this week', 'available': available}), 403
    response = {'ok': True, 'mode': mode}
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT active_wheel_mode, owned_items FROM game_state WHERE user_id = %s',
                        (current_user.id,))
            row = cur.fetchone()
            current_mode = row['active_wheel_mode'] if row else 'steady'
            # T102: include max_stake_pct so the frontend slider can re-size
            # itself if the player has bought stake extension items since
            # the last state load.
            response['max_stake_pct'] = compute_max_stake_pct(
                list(row['owned_items']) if row and row.get('owned_items') else []
            )
            if mode != current_mode:
                # T76: mode change resets state that doesn't carry across modes.
                # Hot-streak reset prevents mode-hopping to farm the +5% bonus
                # at low variance. Insurance / double-down are per-mode bets
                # that don't carry forward. Gravity drift resets on entering
                # OR leaving gravity (any mode change).
                cur.execute(
                    '''UPDATE game_state SET active_wheel_mode = %s,
                                              wager_streak = 0,
                                              insurance_armed = FALSE,
                                              double_down_pending = FALSE,
                                              gravity_drift = 0
                       WHERE user_id = %s''',
                    (mode, current_user.id))
                response['wager_streak'] = 0
                response['insurance_armed'] = False
                response['double_down_pending'] = False
                response['gravity_drift'] = 0
            else:
                cur.execute('UPDATE game_state SET active_wheel_mode = %s WHERE user_id = %s',
                            (mode, current_user.id))
        conn.commit()
    return jsonify(response)


# Note: there is no separate /api/insurance/earn endpoint. insurance_tokens are
# earned through three paths in T119: the daily /api/insurance/claim-free
# claim, per-bounty rewards (T117, credited on /api/bounties/claim), and the
# one-time +5 grant on the player's first purchase of fish_to_wager. A
# second manual conversion endpoint would let players mint tokens
# indefinitely from the same source — not safe.
# list would let players re-claim the same catch for tokens indefinitely.
