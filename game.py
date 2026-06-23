import datetime as dt
import hmac
import logging
import os
import random
import secrets
import time
from datetime import timezone, timedelta

import psycopg2.extras
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import db_connection
from extensions import limiter, csrf
from models import (ALL_ITEMS, INFINITE_UPGRADES, REGEN_SHIELD_RECHARGE_WINS, VALID_FISH_IDS,
                    ITEM_CURRENCY,
                    inf_upgrade_cost,
                    lure_mastery_mult,
                    CLASS_EARTH_FISH_BONUS, CLASS_MOON_PROC_BONUS, CLASS_STAR_WIN_BONUS,
                    streak_bonus, DICE_RECHARGE_SECONDS, dice_max_charges,
                    WAGER_INSURANCE_RECHARGE_SECONDS, WAGER_INSURANCE_MAX_CHARGES,
                    UPGRADE_TIER_THRESHOLDS, item_tier,
                    FISH_CATALOG, roll_fish, lure_bite_delay_seconds, fish_value, autofisher_catch_rate,
                    AUTO_SPIN_INTERVAL_SECONDS, MAX_SPINS_PER_TICK, CATCH_UP_THRESHOLD,
                    AUTO_FISH_INTERVAL_SECONDS, MAX_FISH_CATCHUP_TICKS, FISH_CATCHUP_THRESHOLD,
                    HAPPY_HOUR_START_UTC, HAPPY_HOUR_END_UTC, FISH_TO_WAGER_RATES,
                    SINGULARITY_PER_PLAYER_CAP)
from seasons import ensure_current_season, get_season_info, advance_season
from security import require_json
from wagers import (validate_stake, compute_hot_streak_bonus, should_reset_streak,
                    apply_safety_net, compute_wager_payout, compute_wager_loss,
                    compute_stake_risk, compute_max_stake_pct, compute_stake_value,
                    _recharge_wager_insurance)
from wheel_modes import WHEEL_MODES, get_available_modes, get_week_number, compute_gravity_probabilities, clamp_gravity_drift
from prestige import (get_prestige_bonus, get_starting_prestige, can_prestige,
                     get_prestige_threshold, get_legacy_keep_count,
                     compute_wins_kept, filter_kept_items,
                     PRESTIGE_RESET_COLUMNS, MAX_PRESTIGE_LEVEL)
from bounties import increment_bounty, get_bounty_status, get_claim_rewards, BOUNTY_DEFS
from community_goals import COMMUNITY_GOAL_DEFS, get_active_goal, increment_goal, check_goal_completion, get_player_contribution
from chat import post_system_message
import chat_triggers

COSMETIC_SLOTS = {
    'bg_ocean':   'bg', 'bg_royal':   'bg', 'bg_inferno': 'bg',
    'bg_forest':  'bg', 'bg_abyss':   'bg', 'bg_cosmic':  'bg',
    'fishsize_small': 'size', 'fishsize_1': 'size', 'fishsize_2': 'size', 'fishsize_3': 'size',
    'confetti_1': 'confetti', 'confetti_2': 'confetti', 'confetti_3': 'confetti',
    'party_mode': 'party',
    'trail_1': 'trail', 'trail_2': 'trail', 'trail_3': 'trail',
    'trail_4': 'trail', 'trail_5': 'trail', 'trail_6': 'trail',
    'theme_fire': 'wheel', 'theme_ice': 'wheel', 'theme_neon': 'wheel',
    'theme_void': 'wheel', 'theme_gold': 'wheel',
    'theme_tidal': 'wheel', 'theme_ember': 'wheel', 'theme_frost': 'wheel',
    'theme_aurora': 'wheel', 'theme_vintage': 'wheel',
    'golden_wheel': 'golden',
    'page_season1': 'page_theme', 'page_season2': 'page_theme', 'page_season3': 'page_theme',
    'page_season4': 'page_theme', 'page_season5': 'page_theme', 'page_season6': 'page_theme', 'page_season7': 'page_theme',
    'page_season8': 'page_theme',
    'auto_guard':   'auto_guard',
}


def is_happy_hour(now_utc=None):
    now = now_utc or dt.datetime.now(timezone.utc)
    return HAPPY_HOUR_START_UTC <= now.hour < HAPPY_HOUR_END_UTC


def _aware(dt_val):
    """Ensure a datetime from psycopg2 has UTC tzinfo (psycopg2 returns naive datetimes)."""
    if dt_val is not None and dt_val.tzinfo is None:
        return dt_val.replace(tzinfo=timezone.utc)
    return dt_val


def _recharge_dice(charges, last_recharge, max_charges, now_utc):
    """Recharge dice charges based on elapsed time. Returns (charges, last_recharge)."""
    last_recharge = _aware(last_recharge)
    elapsed = int((now_utc - last_recharge).total_seconds() // DICE_RECHARGE_SECONDS)
    if elapsed > 0 and charges < max_charges:
        charges = min(charges + elapsed, max_charges)
        last_recharge = last_recharge + timedelta(seconds=DICE_RECHARGE_SECONDS * elapsed)
    return charges, last_recharge


log = logging.getLogger('wheel')
game_bp = Blueprint('game', __name__)

# ── SUM(fish_clicks) cache ─────────────────────────────────────────────────
# Full-table aggregate; cache per worker for 15 s to avoid scanning on every
# /api/state load and every 5-second /api/community-pot poll.
_fish_clicks_cache: dict = {'ts': 0.0, 'total': 0}
_FISH_CLICKS_TTL = 15.0


def _get_total_fish_clicks(cur) -> int:
    now = time.monotonic()
    if now - _fish_clicks_cache['ts'] < _FISH_CLICKS_TTL:
        return _fish_clicks_cache['total']
    cur.execute('SELECT COALESCE(SUM(fish_clicks), 0) AS total FROM game_state')
    total = int(cur.fetchone()['total'])
    _fish_clicks_cache['ts'] = now
    _fish_clicks_cache['total'] = total
    return total


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
           prestige_level, prestige_count, legacy_wins, onboarding_step, auto_spin_budget,
           wager_streak, wager_last_stake, double_down_pending, wager_banked_wins,
           wager_insurance_charges, wager_insurance_armed, active_wheel_mode,
           wager_tokens, aquarium_species, cosmetic_fragments,
           guard_charges, guard_last_regen_spin, resilience_last_use_spin,
           bounty_claimed_date, biggest_win_announced,
           wager_last_win_amount, wager_banked_losses, wager_insurance_last_recharge,
           gravity_drift
    FROM game_state WHERE user_id = %s
'''


def _load_game_state(cur, user_id: int, *, for_update: bool = False):
    sql = _GAME_STATE_SQL + ('FOR UPDATE' if for_update else '')
    cur.execute(sql, (user_id,))
    return cur.fetchone()


def _maybe_announce_big_win(conn, gs, events, username):
    """T83: Post a big-win chat message if this win strictly exceeds the
    player's previous biggest_win_announced, and return the value to persist
    in the same transaction (caller writes it to game_state). Returns the
    unchanged previous biggest when the message does not fire.
    """
    biggest = int(gs.get('biggest_win_announced', 0) or 0)
    wins_delta = int(events.get('wins_delta', 0) or 0)
    if (events.get('result') in ('win', 'jackpot')
            and wins_delta >= chat_triggers.BIG_WIN_THRESHOLD
            and wins_delta > biggest):
        post_system_message(conn, chat_triggers.big_win_msg(
            username,
            wins_delta,
            events.get('active_wheel_mode', 'steady'),
        ), 'system', event_kind='big_win')
        return wins_delta
    return biggest


# ── Fishing constants ──────────────────────────────────────────────────────
# Server-side reel window: client sees 1.5 s, server grants 0.3 s of network
# headroom so a tap at the last moment still registers.
REEL_WINDOW_SECONDS = 1.8
# Minimum elapsed seconds after bite_at before a reel is accepted. Sub-50ms
# reels are impossible for real players (poll cadence + network RTT floor).
REEL_MIN_DELTA_SECONDS = 0.05
# EWMA smoothing factor for precise_pct telemetry (lower = slower response).
_EWMA_ALPHA = 0.15


def _lure_level(owned: list) -> int:
    for lvl, item in [(5, 'lure_5'), (4, 'lure_4'), (3, 'lure_3'), (2, 'lure_2'), (1, 'lure_1')]:
        if item in owned:
            return lvl
    return 0


def _autofisher_level(owned: list) -> int:
    for lvl, item in [(4, 'autofisher_4'), (3, 'autofisher_3'), (2, 'autofisher_2'), (1, 'autofisher_1')]:
        if item in owned:
            return lvl
    return 0


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


# Cap wins to prevent JS Infinity display (Number.MAX_VALUE ~1.8e308)
_MAX_WINS = 5_000_000  # Season 8 economy ceiling (was round(9.99e99))


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
    if is_inverted:
        # T102: stake_losses = int(current_losses * stake_pct / 100), capped
        # at current_losses. Debited from losses immediately.
        stake_losses = compute_stake_risk(losses, actual_stake, max_stake_pct)
        # T73 integration: double-down escrows the last loss-gain (tracked in
        # wager_last_win_amount) from losses, mirroring the normal-mode flow
        # but with losses as the escrow source.
        if double_down_active and owns_wager_unlock_eff and wager_last_win_amount > 0:
            stake_losses = wager_last_win_amount
        # T102: effective_stake is a fraction 0.0-0.45 (stake_pct / 100).
        # When there's no escrow (stake=0 or no losses to risk), it collapses
        # to 1.0 so payout/loss are computed at base (the safe position still
        # gives a base payout per spec AC#9: "win returns 0 + base_payout × 1").
        effective_stake = actual_stake / 100.0 if stake_losses > 0 else 1.0
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
        # T102: when there is no escrow (player lacks wager_unlock, or stake=0,
        # or current_wins is so low the percentage risk floors to 0), the stake
        # multiplier must collapse to 1.0 so payout/loss are computed at base
        # (the safe position still gives a base payout per spec AC#9).
        effective_stake = actual_stake / 100.0 if stake_wins > 0 else 1.0
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
            net_payout = stake_losses + loss_bonus
            direct_losses, banked_losses_payout = compute_wager_payout(net_payout, hot_streak_bonus)
            # Refund the escrow, then add the loss-farming payout.
            losses += stake_losses
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
                losses += stake_losses
                insurance_used = True
            wins += direct_wins
            # T79 AC#6: safety net on the bad outcome (win) at ≥5x stake
            # refunds 25% of staked losses.
            if 'wager_safety_net' in owned and not insurance_used:
                losses += apply_safety_net(stake_losses, actual_stake, True)
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
            new_streak = streak + 1 if streak >= 0 else 1
            if regen_recharge_wins > 0:
                regen_recharge_wins -= 1
            jackpot_hit = True
            loss_count = abs(new_streak) if new_streak < 0 else 0
            loss_bonus = streak_bonus(loss_count) * bonus_mult
            base_loss = 1 + loss_bonus
            actual_loss = int(base_loss * effective_stake * 5)
            losses += stake_losses
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
            wins += stake_wins
        elif 'guard' in owned:
            guard_triggered = True
            guard_blocked = True
            new_owned  = [x for x in new_owned if x != 'guard']
            new_streak = streak
            wins += stake_wins
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
                wins += stake_wins
                insurance_used = True
            losses      += actual_loss
            # v2 (T45): safety net refunds 25% of lost escrow, not reduces losses.
            # T74 AC#7: skip when insurance already fired.
            if 'wager_safety_net' in owned and not insurance_used:
                wins += apply_safety_net(stake_wins, actual_stake, True)
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
        if stake_wins > 0:
            net_payout = stake_wins + bonus_earned
        else:
            net_payout = effective_win_mult + bonus_earned
        raw_payout   = net_payout * jackpot_mult
        direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
        wins        += stake_wins
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
        if stake_wins > 0:
            net_payout = stake_wins + bonus_earned
        else:
            net_payout = effective_win_mult + bonus_earned

        if jackpot_echo_pending:
            jackpot_echo_triggered = True
            jackpot_hit  = True
            raw_payout   = net_payout * 25
            direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
            wins        += stake_wins
            wins        += direct_wins
            wager_banked_wins += banked_wins
            last_direct_wins = direct_wins
            bonus_earned = direct_wins + banked_wins - effective_win_mult
        elif 'jackpot' in owned and random.random() < jackpot_chance:
            jackpot_hit  = True
            raw_payout   = net_payout * 25
            direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
            wins        += stake_wins
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
                wins        += stake_wins
                wins        += direct_wins
                wager_banked_wins += banked_wins
                last_direct_wins = direct_wins
                bonus_earned = direct_wins + banked_wins - effective_win_mult
            else:
                raw_payout   = net_payout
                direct_wins, banked_wins = compute_wager_payout(raw_payout, hot_streak_bonus)
                wins += stake_wins
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
    wins = min(wins, _MAX_WINS)

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
            full_info   = get_season_info(conn)
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
                              onboarding_step, auto_spin_budget,
                              wager_streak, wager_last_stake, double_down_pending,
                              wager_banked_wins, wager_insurance_charges,
                              wager_insurance_armed, wager_insurance_last_recharge,
                              wager_last_win_amount, wager_banked_losses,
                              active_wheel_mode, wager_tokens, aquarium_species,
                              cosmetic_fragments, guard_charges,
                              gravity_drift
                       FROM game_state WHERE user_id = %s''',
                    (current_user.id,),
                )
                gs = cur.fetchone()
                cur.execute('SELECT total_contributed, target, win_chance_pct, filled, filled_at, last_decay_check FROM community_pot WHERE id = 1')
                pot = cur.fetchone()
                total_pending_clicks = _get_total_fish_clicks(cur)
                # Season 8: singularity meter
                cur.execute('SELECT total_contributed, target, filled, filled_at, fill_count FROM singularity_meter WHERE id = 1')
                singularity = cur.fetchone()

        now_utc = dt.datetime.now(timezone.utc)
        pot_celebrate = bool(
            pot and pot['filled'] and pot['filled_at'] and
            pot['filled_at'] > now_utc - dt.timedelta(days=7)
        )
        owned_items     = list(gs['owned_items'])
        max_charges     = dice_max_charges(owned_items)
        dice_charges    = min(gs['dice_charges'], max_charges)
        last_recharge   = gs['dice_last_recharge']
        dice_charges, last_recharge = _recharge_dice(dice_charges, last_recharge, max_charges, now_utc)

        # T74: wager insurance recharge (mirrors dice recharge semantics).
        wager_insurance_charges = min(int(gs.get('wager_insurance_charges', 0) or 0),
                                      WAGER_INSURANCE_MAX_CHARGES)
        wager_insurance_last_recharge = gs.get('wager_insurance_last_recharge') or now_utc
        wager_insurance_charges, wager_insurance_last_recharge = _recharge_wager_insurance(
            wager_insurance_charges, wager_insurance_last_recharge,
            WAGER_INSURANCE_MAX_CHARGES, now_utc,
        )

        # Season 8: available wheel modes for this week
        week_num = get_week_number(now_utc)
        available_modes = get_available_modes(week_num)
        if singularity and singularity['filled']:
            available_modes = available_modes + ['singularity']

        # Season 8: bounty status + community goal (needs a connection)
        bounty_date = now_utc.date()
        season_num = full_info.get('season_number', 8) if full_info else 8
        with db_connection() as conn2:
            bounties = get_bounty_status(conn2, current_user.id, bounty_date)
            goal_row, goal_def = get_active_goal(conn2, season_num, week_num)
            player_contrib = get_player_contribution(conn2, goal_def['goal_id'], current_user.id) if goal_row else 0

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
            'legacy_wins':          int(gs.get('legacy_wins', 0)),
            'onboarding_step':      gs.get('onboarding_step', 0),
            'auto_spin_budget':     gs.get('auto_spin_budget', 0),
            'auto_spin_active':     gs.get('auto_spin_since') is not None and int(gs.get('auto_spin_budget', 0)) > 0,
            'cumulative_wins':      int(gs.get('cumulative_wins', 0)),
            'wager_streak':         gs.get('wager_streak', 0),
            'wager_last_stake':     gs.get('wager_last_stake', 0),
            'double_down_pending':  bool(gs.get('double_down_pending', False)),
            'wager_banked_wins':    gs.get('wager_banked_wins', 0),
            'wager_banked_losses':  gs.get('wager_banked_losses', 0),
            'wager_last_win_amount': int(gs.get('wager_last_win_amount', 0) or 0),
            'wager_insurance_charges': int(wager_insurance_charges),
            'wager_insurance_armed': bool(gs.get('wager_insurance_armed', False)),
            'wager_insurance_last_recharge': (
                wager_insurance_last_recharge.isoformat()
                if hasattr(wager_insurance_last_recharge, 'isoformat')
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
            'wager_tokens':         gs.get('wager_tokens', 0),
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

            # Block manual spins when server-side auto-spin is currently running (budget > 0 + auto_spin_since set).
            # Season 8: auto-spin is opt-in (budget only > 0 when user explicitly started it).
            if gs['auto_spin_since'] is not None and int(gs.get('auto_spin_budget', 0)) > 0:
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

            pot_active = bool(
                pot_row and pot_row['filled'] and pot_row['filled_at'] and
                pot_row['filled_at'] > now_utc - dt.timedelta(days=7)
            )
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
            dice_charges, last_recharge = _recharge_dice(dice_charges, last_recharge, max_charges, now_utc)

            # T74: wager insurance recharge (1 charge per 10 min, capped at 3).
            wager_insurance_charges = min(int(gs.get('wager_insurance_charges', 0) or 0),
                                          WAGER_INSURANCE_MAX_CHARGES)
            wager_insurance_last_recharge = gs.get('wager_insurance_last_recharge') or now_utc
            (wager_insurance_charges,
             wager_insurance_last_recharge) = _recharge_wager_insurance(
                wager_insurance_charges, wager_insurance_last_recharge,
                WAGER_INSURANCE_MAX_CHARGES, now_utc,
            )

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
            insurance_active = bool(gs.get('wager_insurance_armed', False))

            new_spin_count = gs['spin_count'] + 1
            new_state, events = _resolve_spin(
                owned=list(gs['owned_items']),
                streak=gs['streak'],
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
            )

            new_win_count  = gs['win_count']  + (1 if events['result'] in ('win', 'jackpot')  else 0)
            new_loss_count = gs['loss_count'] + (1 if events['result'] == 'lose' else 0)
            # T106: cumulative_wins tracks the lifetime value of wins gained.
            # Incremented on every win/jackpot by wins_delta (the actual wins
            # gained from this spin, including wager payouts). Never decremented.
            new_cumulative_wins = int(gs.get('cumulative_wins', 0)) + max(0, int(events.get('wins_delta', 0)))

            # Season 8: post system message on jackpot
            if events['jackpot_hit']:
                post_system_message(conn, chat_triggers.jackpot_msg(
                    current_user.username,
                    events.get('active_wheel_mode', 'steady'),
                    int(events.get('stake', 1)),
                    int(events['wins_delta']),
                ), 'system', event_kind='jackpot')
            # Season 8: post system message on big double-down win
            if (double_down_active and events['result'] in ('win', 'jackpot')
                    and int(events.get('stake', 1)) >= chat_triggers.DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE):
                post_system_message(conn, chat_triggers.double_down_win_msg(
                    current_user.username,
                    int(events.get('stake', 1)),
                    int(events['wins_delta']),
                ), 'system', event_kind='double_down_win')
            # Season 8: hot streak milestone (fires on exact transition to threshold)
            if (events['result'] in ('win', 'jackpot')
                    and int(events.get('wager_streak', 0)) == chat_triggers.HOT_STREAK_MSG_THRESHOLD):
                post_system_message(conn, chat_triggers.hot_streak_msg(current_user.username),
                                    'system', event_kind='hot_streak_10')
            # Season 8: big win (T83 per-player escalating threshold)
            new_biggest_win_announced = _maybe_announce_big_win(
                conn, gs, events, current_user.username)

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
                           dice_rolled_since_spin = FALSE,
                           last_spin_at = NOW(),
                           active_tab_id = %s, tab_last_seen = NOW(),
                          wager_streak = %s, wager_last_stake = %s,
                          wager_banked_wins = %s,
                          wager_banked_losses = %s,
                          wager_last_win_amount = %s,
                          double_down_pending = FALSE,
                          wager_insurance_armed = FALSE,
                          wager_insurance_charges = %s,
                          wager_insurance_last_recharge = %s,
                          biggest_win_announced = %s,
                          gravity_drift = %s,
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
                     req_tab_id or gs['active_tab_id'],
                     new_state.get('wager_streak', 0), new_state.get('wager_last_stake', 1),
                     new_state.get('wager_banked_wins', 0),
                     new_state.get('wager_banked_losses', 0),
                     new_state.get('wager_last_win_amount', 0),
                     wager_insurance_charges,
                     wager_insurance_last_recharge,
                     new_biggest_win_announced,
                     new_state.get('gravity_drift', 0),
                     current_user.id),
                )
            conn.commit()

        resp = _events_to_response(events)
        resp['angle'] = total_rotation
        resp['new_spin_count'] = new_spin_count
        resp['dice_charges'] = dice_charges
        resp['dice_last_recharge'] = last_recharge.isoformat()
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
        # T74: surface insurance state on spin response.
        resp['wager_insurance_charges'] = wager_insurance_charges
        resp['wager_insurance_armed'] = False
        resp['wager_insurance_last_recharge'] = (
            wager_insurance_last_recharge.isoformat()
            if hasattr(wager_insurance_last_recharge, 'isoformat')
            else None
        )
        # T77: gravity drift + drift-adjusted probabilities on the spin
        # response so the wheel redraws correctly after each resolve.
        resp['gravity_drift'] = new_state.get('gravity_drift', 0)
        resp['wheel_probabilities'] = events.get('wheel_probabilities')
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


@game_bp.route('/api/register-season', methods=['POST'])
@login_required
def register_season():
    """Mark user as pre-registered for the next season start.
    Also activates the wheel mid-season if not already started.
    """
    try:
        now_utc = dt.datetime.now(timezone.utc)
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET season_registered = TRUE,
                           auto_spin_since = CASE WHEN auto_spin_since IS NULL THEN %s ELSE auto_spin_since END,
                           last_spin_at    = CASE WHEN auto_spin_since IS NULL THEN %s ELSE last_spin_at END
                       WHERE user_id = %s''',
                    (now_utc, now_utc, current_user.id),
                )
            conn.commit()
        return jsonify({'ok': True})
    except Exception:
        log.exception('REGISTER_SEASON_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Registration failed'}), 500


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

            # Season 8: only process auto-spin when the player has started it (budget > 0).
            # If budget is 0, return immediately — manual spins go through /api/spin directly.
            budget = int(gs.get('auto_spin_budget', 0))
            if budget == 0:
                return jsonify({'spins': [], 'auto_spin_active': False, 'elapsed_ms': 0})

            # First auto-spin tick of the session — start the clock now
            if gs['auto_spin_since'] is None:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE game_state SET auto_spin_since = %s, last_spin_at = %s WHERE user_id = %s',
                        (now_utc, now_utc, current_user.id),
                    )
                conn.commit()
                return jsonify({'started': True, 'auto_spin_since': now_utc.isoformat(),
                                'auto_spin_active': True, 'auto_spin_budget': budget})

            auto_spin_since = gs['auto_spin_since']
            auto_spin_since = _aware(auto_spin_since)

            last_spin = gs['last_spin_at'] or auto_spin_since
            last_spin = _aware(last_spin)
            # Never count time before the wheel started this session
            cursor = max(auto_spin_since, last_spin)

            elapsed = (now_utc - cursor).total_seconds()
            spins_due = min(int(elapsed // AUTO_SPIN_INTERVAL_SECONDS), MAX_SPINS_PER_TICK)

            # Cap by remaining budget (Season 8: max 100 spins per activation)
            spins_due = min(spins_due, budget)

            if spins_due == 0:
                return jsonify({'spins': [], 'auto_spin_active': True,
                                'auto_spin_budget': budget, 'elapsed_ms': int(elapsed * 1000)})

            is_catch_up = spins_due > CATCH_UP_THRESHOLD

            pot_active = bool(
                pot_row and pot_row['filled'] and pot_row['filled_at'] and
                pot_row['filled_at'] > now_utc - dt.timedelta(days=7)
            )
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
            dice_charges, last_recharge = _recharge_dice(dice_charges, last_recharge, max_charges, now_utc)

            # Apply any pending dice roll before processing spins
            if gs['pending_dice']:
                pd = gs['pending_dice']
                streak      = pd['new_streak']
                best_streak = max(best_streak, streak) if streak > 0 else best_streak

            spin_results = []

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

                new_win_count  += 1 if events['result'] == 'win'  else 0
                new_loss_count += 1 if events['result'] == 'lose' else 0
                # T106: cumulative_wins — track lifetime value of wins gained.
                new_cumulative_wins += max(0, int(events.get('wins_delta', 0)))

                # T90: auto-post chat messages (mirror T82 manual /api/spin path)
                if events['result'] == 'jackpot':
                    post_system_message(conn, chat_triggers.jackpot_msg(
                        current_user.username,
                        events.get('active_wheel_mode', 'steady'),
                        1,
                        int(events['wins_delta']),
                    ), 'system', event_kind='jackpot')
                if (int(events.get('wager_streak', 0)) == chat_triggers.HOT_STREAK_MSG_THRESHOLD):
                    post_system_message(conn, chat_triggers.hot_streak_msg(current_user.username),
                                        'system', event_kind='hot_streak_10')
                new_biggest_win_announced = _maybe_announce_big_win(
                    conn, gs, events, current_user.username)
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
                       auto_spin_budget = GREATEST(auto_spin_budget - %s, 0),
                       auto_spin_since = CASE WHEN auto_spin_budget - %s <= 0 THEN NULL ELSE auto_spin_since END,
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
                     spins_due, spins_due,
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
                        autofisher_lvl = _autofisher_level(owned)
                        if autofisher_lvl >= 1:
                            lure_lvl       = _lure_level(owned)
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

        budget_remaining = max(budget - spins_due, 0) if budget > 0 else 0
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
            'auto_spin_budget':      budget_remaining,
            'auto_spin_active':      budget_remaining > 0,
            # T106: cumulative_wins after all processed spins (catch-up summary).
            'cumulative_wins':       new_cumulative_wins,
        }

        if is_catch_up:
            return jsonify({
                'catch_up':        True,
                'spins_processed': spins_due,
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
                    '''SELECT wins, losses, streak, best_streak, owned_items,
                              dice_charges, dice_last_recharge, dice_rolled_since_spin
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            wins        = int(gs['wins'])
            streak      = gs['streak']
            best_streak = gs['best_streak']
            owned       = list(gs['owned_items'])
            now_utc     = dt.datetime.now(timezone.utc)

            # Recharge dice charges
            max_charges = dice_max_charges(owned)
            dice_charges  = min(gs['dice_charges'], max_charges)  # cap stale over-limit values
            last_recharge = gs['dice_last_recharge']
            dice_charges, last_recharge = _recharge_dice(dice_charges, last_recharge, max_charges, now_utc)

            # Season 5: dice requires win streak >= 3 (no loss streak amplification)
            if streak < 3:
                return jsonify({'error': 'Need a win streak of 3 or more to roll'}), 400
            if dice_charges < 1:
                return jsonify({'error': 'No dice charges available'}), 400
            if gs['dice_rolled_since_spin']:
                return jsonify({'error': 'You must spin once before rolling again'}), 400

            num_dice = 3 if 'dice_extra' in owned else 2
            dice     = [random.randint(1, 6) for _ in range(num_dice)]
            dice_sum = sum(dice)

            ones  = dice.count(1)
            sixes = dice.count(6)
            # Triple outcomes (3-die only): cursed_triple / blessed_triple take priority
            cursed_triple  = (num_dice == 3 and ones  == 3)
            blessed_triple = (num_dice == 3 and sixes == 3)
            # Pair outcomes: any two 1s or two 6s (includes snake-eyes on 2-die)
            cursed  = not cursed_triple  and ones  >= 2
            blessed = not blessed_triple and sixes >= 2

            if cursed_triple:
                new_streak = max(0, streak // 3)
            elif blessed_triple:
                new_streak = streak * 3
            elif cursed:
                new_streak = max(0, streak // 2)
            elif blessed:
                new_streak = streak * 2
            else:
                new_streak = streak + dice_sum

            new_charges   = dice_charges - 1
            # Reset recharge clock from now when a charge is consumed
            new_last_recharge = now_utc if new_charges < max_charges else last_recharge

            # Buffer the result — streak is applied by the next /api/tick, not immediately.
            pending = {
                'new_streak':      new_streak,
                'die1':            dice[0],
                'die2':            dice[1],
                'die3':            dice[2] if len(dice) > 2 else None,
                'dice_sum':        dice_sum,
                'cursed':          cursed or cursed_triple,
                'blessed':         blessed or blessed_triple,
                'cursed_triple':   cursed_triple,
                'blessed_triple':  blessed_triple,
            }
            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET pending_dice = %s,
                           dice_charges = %s, dice_last_recharge = %s,
                           dice_rolled_since_spin = TRUE
                       WHERE user_id = %s''',
                    (psycopg2.extras.Json(pending), new_charges, new_last_recharge, current_user.id),
                )
            conn.commit()

        return jsonify({
            'die1':               dice[0],
            'die2':               dice[1],
            'die3':               dice[2] if len(dice) > 2 else None,
            'dice':               dice,
            'dice_sum':           dice_sum,
            'cursed':             cursed or cursed_triple,
            'blessed':            blessed or blessed_triple,
            'cursed_triple':      cursed_triple,
            'blessed_triple':     blessed_triple,
            'streak':             new_streak,
            'wins':               wins,
            'dice_charges':       new_charges,
            'dice_last_recharge': last_recharge.isoformat(),
            'buffered':           True,
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

    # Infinite repeatable upgrades — handled separately (no "already owned" restriction)
    if item_id in INFINITE_UPGRADES:
        inf      = INFINITE_UPGRADES[item_id]
        col      = inf['db_column']
        currency = 'wins'  # ponytail: only clickmult_inf survives Season 8 (spec S5)
        try:
            with db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    gs = _load_game_state(cur, current_user.id, for_update=True)

                owned     = list(gs['owned_items'])
                cur_level = gs[col]

                # Generic max_level check
                max_level = inf.get('max_level')
                if max_level is not None and cur_level >= max_level:
                    return jsonify({'error': 'Maximum level reached'}), 400

                # Per-upgrade requirement checks
                if item_id == 'streak_armor_inf':
                    if 'resilience' not in owned:
                        return jsonify({'error': 'Requires Resilience'}), 400
                elif item_id == 'jackpot_resonance_inf':
                    if 'jackpot' not in owned:
                        return jsonify({'error': 'Requires Jackpot upgrade'}), 400
                elif item_id == 'echo_amp_inf':
                    if 'win_echo' not in owned:
                        return jsonify({'error': 'Requires Win Echo upgrade'}), 400
                elif item_id == 'proc_streak_inf':
                    if not any(x in owned for x in ('jackpot', 'win_echo', 'fortune_charm')):
                        return jsonify({'error': 'Requires Jackpot, Win Echo, or Fortune Charm'}), 400

                cost = inf_upgrade_cost(item_id, cur_level)

                # Currency-aware balance check and deduction
                if currency == 'fish_clicks':
                    if int(gs['fish_clicks']) < cost:
                        return jsonify({'error': 'Insufficient fish bucks'}), 402
                    new_wins  = int(gs['wins'])
                    new_fish  = int(gs['fish_clicks']) - cost
                else:  # wins
                    if int(gs['wins']) < cost:
                        return jsonify({'error': 'Insufficient wins'}), 402
                    new_wins  = int(gs['wins']) - cost
                    new_fish  = gs['fish_clicks']

                new_level = cur_level + 1

                with conn.cursor() as cur:
                    cur.execute(
                        f'UPDATE game_state SET wins = %s, fish_clicks = %s, {col} = %s WHERE user_id = %s',
                        (new_wins, new_fish, new_level, current_user.id),
                    )
                conn.commit()

            def _lvl(field):
                return new_level if col == field else gs[field]

            return jsonify({
                'wins':                    new_wins,
                'losses':                  gs['losses'],
                'fish_clicks':             new_fish,
                'owned_items':             owned,
                'regen_recharge_wins':     gs['regen_recharge_wins'],
                'active_cosmetics':        list(gs['active_cosmetics']),
                'winmult_inf_level':         _lvl('winmult_inf_level'),
                'bonusmult_inf_level':       _lvl('bonusmult_inf_level'),
                'streak_armor_level':        _lvl('streak_armor_level'),
                'lure_mastery_level':        _lvl('lure_mastery_level'),
                'jackpot_resonance_level':   _lvl('jackpot_resonance_level'),
                'echo_amp_level':            _lvl('echo_amp_level'),
                'proc_streak_level':         _lvl('proc_streak_level'),
            })
        except Exception:
            log.exception('BUY_INF_ERROR  user_id=%s  item_id=%s', current_user.id, item_id)
            return jsonify({'error': 'Purchase failed'}), 500

    if item_id not in ALL_ITEMS:
        return jsonify({'error': 'Unknown item'}), 400

    item     = ALL_ITEMS[item_id]
    cost     = item['cost']
    requires = item.get('requires')
    currency = ITEM_CURRENCY[item_id]

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                gs = _load_game_state(cur, current_user.id, for_update=True)

            owned = list(gs['owned_items'])

            if item_id in owned:
                return jsonify({'error': 'Already owned'}), 409
            if requires and requires not in owned:
                return jsonify({'error': 'Prerequisite not met'}), 400

            # Master upgrades require all 13 species caught (complete Encyclopaedia)
            if item_id in ('lure_5', 'autofisher_4', 'precise_angler_3'):
                caught = set(gs['caught_species'])
                all_species = set(FISH_CATALOG.keys())
                if caught < all_species:
                    missing = len(all_species) - len(caught & all_species)
                    return jsonify({'error': f'Complete your Encyclopaedia first — {missing} species still to catch'}), 403

            # T106: tier gating — check cumulative_wins threshold (lifetime wins gained)
            tier = item_tier(item_id)
            if tier > 1:
                threshold = UPGRADE_TIER_THRESHOLDS[tier]
                cumulative = int(gs.get('cumulative_wins', 0))
                if cumulative < threshold:
                    return jsonify({'error': f'Unlocks at {threshold:,} total wins gained (you have {cumulative:,})'}), 403

            # Currency-specific balance check
            if currency == 'wins':
                if int(gs['wins']) < cost:
                    return jsonify({'error': 'Insufficient wins'}), 402
                new_wins   = int(gs['wins']) - cost
                new_losses = gs['losses']
                new_clicks = gs['fish_clicks']
            elif currency == 'losses':
                if gs['losses'] < cost:
                    return jsonify({'error': 'Insufficient losses'}), 402
                new_wins   = int(gs['wins'])
                new_losses = gs['losses'] - cost
                new_clicks = gs['fish_clicks']
            else:  # fish_clicks — singularity only
                if gs['fish_clicks'] < cost:
                    return jsonify({'error': 'Insufficient fish bucks'}), 402
                new_wins   = int(gs['wins'])
                new_losses = gs['losses']
                new_clicks = gs['fish_clicks'] - cost

            new_owned          = owned + [item_id]
            new_regen_recharge = 0 if item_id == 'regen_shield' else gs['regen_recharge_wins']

            # Auto-activate cosmetic items when purchased
            new_active_cosmetics = list(gs['active_cosmetics'])
            if item_id in COSMETIC_SLOTS:
                slot = COSMETIC_SLOTS[item_id]
                new_active_cosmetics = [c for c in new_active_cosmetics if COSMETIC_SLOTS.get(c) != slot]
                new_active_cosmetics.append(item_id)

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET wins = %s, losses = %s, fish_clicks = %s,
                           owned_items = %s, regen_recharge_wins = %s, active_cosmetics = %s
                       WHERE user_id = %s''',
                     (new_wins, new_losses, new_clicks, new_owned,
                      new_regen_recharge, new_active_cosmetics, current_user.id),
                )
            conn.commit()

            if item_id == 'wager_insurance':
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE game_state SET wager_insurance_charges = wager_insurance_charges + 3 WHERE user_id = %s',
                        (current_user.id,),
                    )
                conn.commit()

        return jsonify({
            'wins':                new_wins,
            'losses':              new_losses,
            'fish_clicks':         new_clicks,
            'owned_items':         new_owned,
            'regen_recharge_wins': new_regen_recharge,
            'active_cosmetics':    new_active_cosmetics,
            'winmult_inf_level':   gs['winmult_inf_level'],
            'bonusmult_inf_level': gs['bonusmult_inf_level'],
        })
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
                total_pending_clicks = _get_total_fish_clicks(cur)
            if not pot:
                return jsonify({'total_contributed': 0, 'target': 1_000, 'filled': False, 'active': False, 'win_chance_pct': 50.0, 'total_pending_clicks': total_pending_clicks})
            now_utc = dt.datetime.now(timezone.utc)
            pot_active = bool(
                pot['filled'] and pot['filled_at'] and
                pot['filled_at'] > now_utc - dt.timedelta(days=7)
            )
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
                pot_window_active = pot['filled_at'] and pot['filled_at'] > now_utc - dt.timedelta(days=7)
                if pot_window_active:
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
    err = require_json()
    if err:
        return err

    data    = request.get_json(silent=True) or {}
    fish_id = data.get('fish_id') or ''

    if fish_id not in VALID_FISH_IDS:
        return jsonify({'error': 'Invalid fish'}), 400

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT owned_items FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned = list(gs['owned_items'])
            if fish_id != 'default' and fish_id not in owned:
                return jsonify({'error': 'Fish not owned'}), 403

            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET equipped_fish = %s WHERE user_id = %s',
                    (fish_id, current_user.id),
                )
            conn.commit()

        return jsonify({'equipped_fish': fish_id})
    except Exception:
        log.exception('EQUIP_ERROR  user_id=%s  fish_id=%s', current_user.id, fish_id)
        return jsonify({'error': 'Equip failed'}), 500


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
                cur.execute(
                    'SELECT owned_items, fishing_cast_at, fishing_bite_at FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned   = list(gs['owned_items'])
            now_utc = dt.datetime.now(timezone.utc)

            # Allow new cast if there is no active session, or the bite window has expired
            cast_at = gs['fishing_cast_at']
            bite_at = gs['fishing_bite_at']
            if cast_at and bite_at:
                bite_at = _aware(bite_at)
                if bite_at + timedelta(seconds=REEL_WINDOW_SECONDS) > now_utc:
                    return jsonify({'error': 'Already fishing'}), 400

            lure_level        = _lure_level(owned)
            min_delay, max_delay = lure_bite_delay_seconds(lure_level)
            delay             = random.uniform(min_delay, max_delay)
            new_bite_at       = now_utc + timedelta(seconds=delay)
            expires_at        = new_bite_at + timedelta(seconds=REEL_WINDOW_SECONDS)

            # 50% chance of a fake nibble partway through the wait (adds tension)
            nibble_at = None
            if random.random() < 0.5:
                nibble_frac = random.uniform(0.25, 0.70)
                nibble_at   = (now_utc + timedelta(seconds=delay * nibble_frac)).isoformat()

            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET fishing_cast_at = %s, fishing_bite_at = %s WHERE user_id = %s',
                    (now_utc, new_bite_at, current_user.id),
                )
            conn.commit()

        # bite_at is intentionally omitted from this response — the client
        # must poll /api/bite-poll to detect the bite rather than pre-timing it.
        return jsonify({
            'cast_at':   now_utc.isoformat(),
            'nibble_at': nibble_at,
        })
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
                cur.execute(
                    'SELECT fishing_bite_at FROM game_state WHERE user_id = %s',
                    (current_user.id,),
                )
                gs = cur.fetchone()

        now_utc = dt.datetime.now(timezone.utc)
        bite_at = gs['fishing_bite_at']

        if bite_at is None:
            return jsonify({'bite': False}), 200

        bite_at = _aware(bite_at)

        expires_at = bite_at + timedelta(seconds=REEL_WINDOW_SECONDS)

        if now_utc > expires_at:
            return jsonify({'expired': True}), 200

        if now_utc < bite_at:
            return jsonify({'bite': False}), 200

        remaining_ms = int((expires_at - now_utc).total_seconds() * 1000)
        return jsonify({'bite': True, 'remaining_ms': max(0, remaining_ms)}), 200

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
                cur.execute(
                    '''SELECT owned_items, fishing_cast_at, fishing_bite_at,
                              fishing_lucky_next, caught_species, fish_clicks,
                              fastest_catch_pct,
                              suspicious_catches, catch_count, catch_pct_ewma,
                              catch_of_the_day_date, onboarding_step
                     FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            now_utc = dt.datetime.now(timezone.utc)
            cast_at = gs['fishing_cast_at']
            bite_at = gs['fishing_bite_at']

            if not cast_at or not bite_at:
                return jsonify({'result': 'miss', 'reason': 'no_session',
                                'fish_clicks': int(gs['fish_clicks'])}), 200

            bite_at = _aware(bite_at)

            expires_at = bite_at + timedelta(seconds=REEL_WINDOW_SECONDS)

            # Always clear the session regardless of timing
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET fishing_cast_at = NULL, fishing_bite_at = NULL WHERE user_id = %s',
                    (current_user.id,),
                )

            if now_utc < bite_at or now_utc > expires_at:
                conn.commit()
                return jsonify({'result': 'miss', 'reason': 'bad_timing',
                                'fish_clicks': int(gs['fish_clicks'])}), 200

            elapsed_s = (now_utc - bite_at).total_seconds()
            if elapsed_s < REEL_MIN_DELTA_SECONDS:
                conn.commit()
                log.warning('SUSPICIOUS_REEL_TOO_FAST user_id=%s delta_ms=%.1f',
                            current_user.id, elapsed_s * 1000)
                return jsonify({'result': 'miss', 'reason': 'too_fast',
                                'fish_clicks': int(gs['fish_clicks'])}), 200

            # Successful catch!
            owned          = list(gs['owned_items'])
            lure_level     = _lure_level(owned)
            species_id     = roll_fish(auto_mode=False, master_lure=(lure_level >= 5),
                                       happy_hour=is_happy_hour(now_utc))
            species        = FISH_CATALOG[species_id]
            value          = fish_value(species_id, lure_level)
            lucky_next     = bool(gs['fishing_lucky_next'])
            caught_species = list(gs['caught_species'])
            was_doubled    = False

            if lucky_next:
                value *= 2
                was_doubled = True

            # Precise Angler: tiered multiplier for early reels (exclusive — highest gate wins).
            # elapsed_s already computed above (reused from the too_fast check).
            precise_pct    = round((elapsed_s / REEL_WINDOW_SECONDS) * 100, 1)
            precise_mult   = 1.0
            if 'precise_angler_3' in owned and precise_pct <= 15.0:
                precise_mult = 2.0
            elif 'precise_angler_2' in owned and precise_pct <= 20.0:
                precise_mult = 1.5
            elif 'precise_angler_1' in owned and precise_pct <= 50.0:
                precise_mult = 1.2
            precise_bonus = precise_mult > 1.0
            if precise_bonus:
                value = int(value * precise_mult)

            new_lucky_next = (species_id == 'lucky')
            first_catch    = species_id not in caught_species
            if first_catch:
                caught_species = caught_species + [species_id]

            new_fish_clicks = int(gs['fish_clicks']) + value

            # Track personal best (lowest = fastest) precise catch percentage
            old_best = gs['fastest_catch_pct']
            new_best = precise_pct if (old_best is None or precise_pct < old_best) else old_best

            # Telemetry: EWMA of precise_pct and suspicious-catch counter.
            old_ewma       = gs['catch_pct_ewma']
            new_ewma       = precise_pct if old_ewma is None else _EWMA_ALPHA * precise_pct + (1 - _EWMA_ALPHA) * old_ewma
            new_catch_count = int(gs['catch_count']) + 1
            new_suspicious  = int(gs['suspicious_catches'])
            if precise_pct < 12.0:
                new_suspicious += 1
                if new_suspicious % 10 == 0:
                    log.warning('SUSPICIOUS_REEL user_id=%s pct=%.1f ewma=%.1f catch_count=%d suspicious=%d',
                                current_user.id, precise_pct, new_ewma, new_catch_count, new_suspicious)

            # Season 8: award wager_tokens if fish_to_wager owned
            wager_tokens_awarded = 0
            catch_of_day_bonus = False
            if 'fish_to_wager' in owned:
                tier_map = {'Common': 0, 'Uncommon': 1, 'Rare': 2, 'Legendary': 3}
                tier_idx = tier_map.get(species.get('tier', 'Common'), 0)
                wager_tokens_awarded = FISH_TO_WAGER_RATES[tier_idx]
                # catch_of_the_day: first catch each UTC day worth 5x
                if 'catch_of_the_day' in owned:
                    today = now_utc.date().isoformat()
                    last_cotd = gs.get('catch_of_the_day_date') or ''
                    if last_cotd != today:
                        wager_tokens_awarded *= 5
                        catch_of_day_bonus = True

            with conn.cursor() as cur:
                if wager_tokens_awarded > 0 and catch_of_day_bonus:
                    cur.execute(
                        '''UPDATE game_state
                           SET fish_clicks = %s, fishing_lucky_next = %s, caught_species = %s,
                               fastest_catch_pct = %s,
                               suspicious_catches = %s, catch_count = %s, catch_pct_ewma = %s,
                               wager_tokens = wager_tokens + %s,
                               catch_of_the_day_date = %s
                           WHERE user_id = %s''',
                        (new_fish_clicks, new_lucky_next, caught_species, new_best,
                         new_suspicious, new_catch_count, new_ewma,
                         wager_tokens_awarded, now_utc.date(), current_user.id),
                    )
                elif wager_tokens_awarded > 0:
                    cur.execute(
                        '''UPDATE game_state
                           SET fish_clicks = %s, fishing_lucky_next = %s, caught_species = %s,
                               fastest_catch_pct = %s,
                               suspicious_catches = %s, catch_count = %s, catch_pct_ewma = %s,
                               wager_tokens = wager_tokens + %s
                           WHERE user_id = %s''',
                        (new_fish_clicks, new_lucky_next, caught_species, new_best,
                         new_suspicious, new_catch_count, new_ewma,
                         wager_tokens_awarded, current_user.id),
                    )
                else:
                    cur.execute(
                        '''UPDATE game_state
                           SET fish_clicks = %s, fishing_lucky_next = %s, caught_species = %s,
                               fastest_catch_pct = %s,
                               suspicious_catches = %s, catch_count = %s, catch_pct_ewma = %s
                           WHERE user_id = %s''',
                        (new_fish_clicks, new_lucky_next, caught_species, new_best,
                         new_suspicious, new_catch_count, new_ewma, current_user.id),
                    )
            # Bounty tracking
            bounty_date = now_utc.date()
            increment_bounty(conn, current_user.id, 'bounty_fish10', bounty_date)

            # Community goal tracking
            season_info = get_season_info(conn)
            season_num = season_info.get('season_number', 8) if season_info else 8
            week_num = get_week_number(now_utc)
            _, goal_def = get_active_goal(conn, season_num, week_num)
            if goal_def:
                if goal_def['metric'] == 'fish_caught':
                    increment_goal(conn, goal_def['goal_id'], current_user.id, 1)
                    check_goal_completion(conn, goal_def['goal_id'])
                elif goal_def['metric'] == 'unique_species' and first_catch:
                    increment_goal(conn, goal_def['goal_id'], current_user.id, 1)
                    check_goal_completion(conn, goal_def['goal_id'])

            # Onboarding: advance step 2→3 on first successful catch
            if gs.get('onboarding_step', 0) == 2:
                with conn.cursor() as cur:
                    cur.execute(
                        '''UPDATE game_state
                           SET onboarding_step = 3,
                               owned_items = CASE WHEN NOT (owned_items @> ARRAY['fish_tropical'])
                                   THEN array_append(owned_items, 'fish_tropical') ELSE owned_items END
                           WHERE user_id = %s''',
                        (current_user.id,),
                    )

            conn.commit()

        return jsonify({
            'result':           'hit',
            'species':          species_id,
            'species_emoji':    species['emoji'],
            'species_name':     species['name'],
            'value':            value,
            'first_catch':      first_catch,
            'was_doubled':      was_doubled,
            'precise_bonus':    precise_bonus,
            'precise_mult':     precise_mult,
            'precise_pct':      precise_pct,
            'lucky_next_active': new_lucky_next,
            'fish_clicks':      new_fish_clicks,
            'wager_tokens':     wager_tokens_awarded,
            'catch_of_day_bonus': catch_of_day_bonus,
            'onboarding_advance': gs.get('onboarding_step', 0) == 2,
        })
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
                cur.execute(
                    '''SELECT owned_items, fish_clicks, caught_species, auto_fish_last_tick,
                              lure_mastery_level, equipped_class
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            now_utc        = dt.datetime.now(timezone.utc)
            owned          = list(gs['owned_items'])
            autofisher_lvl = _autofisher_level(owned)

            if autofisher_lvl < 1:
                return jsonify({'error': 'Auto-Fisher not owned'}), 403

            last_tick = gs['auto_fish_last_tick']
            if last_tick is not None:
                last_tick = _aware(last_tick)
                if (now_utc - last_tick).total_seconds() < 5.0:
                    conn.commit()
                    return jsonify({'result': 'miss', 'fish_clicks': int(gs['fish_clicks'])}), 200

            if random.random() >= autofisher_catch_rate(autofisher_lvl):
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE game_state SET auto_fish_last_tick = %s, auto_fish_enabled = TRUE WHERE user_id = %s',
                        (now_utc, current_user.id),
                    )
                conn.commit()
                return jsonify({'result': 'miss', 'fish_clicks': int(gs['fish_clicks'])}), 200

            lure_level     = _lure_level(owned)
            species_id     = roll_fish(auto_mode=True, allow_rare=(autofisher_lvl >= 4))
            species        = FISH_CATALOG[species_id]
            base_value     = fish_value(species_id, lure_level)
            lm_mult        = lure_mastery_mult(gs['lure_mastery_level'])
            earth_mult     = 1.0 + CLASS_EARTH_FISH_BONUS if gs['equipped_class'] == 'earth' else 1.0
            value          = max(1, int(base_value * lm_mult * earth_mult))
            caught_species = list(gs['caught_species'])
            first_catch    = species_id not in caught_species
            if first_catch:
                caught_species = caught_species + [species_id]

            new_fish_clicks = int(gs['fish_clicks']) + value

            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET fish_clicks = %s, caught_species = %s, auto_fish_last_tick = %s, auto_fish_enabled = TRUE WHERE user_id = %s',
                    (new_fish_clicks, caught_species, now_utc, current_user.id),
                )
            conn.commit()

        return jsonify({
            'result':        'hit',
            'species':       species_id,
            'species_emoji': species['emoji'],
            'species_name':  species['name'],
            'value':         value,
            'first_catch':   first_catch,
            'fish_clicks':   new_fish_clicks,
        })
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
        enabled = bool(data.get('enabled', False))
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET auto_fish_enabled = %s WHERE user_id = %s',
                    (enabled, current_user.id),
                )
            conn.commit()
        return jsonify({'ok': True, 'auto_fish_enabled': enabled})
    except Exception:
        log.exception('AUTO_FISH_ENABLED_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Failed to update auto fish state'}), 500


@game_bp.route('/api/equip-class', methods=['POST'])
@login_required
@limiter.limit('20 per minute')
def equip_class():
    err = require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    class_item = data.get('class_id')  # 'class_earth' | 'class_moon' | 'class_star' | None

    CLASS_MAP = {'class_earth': 'earth', 'class_moon': 'moon', 'class_star': 'star', None: None}
    if class_item not in CLASS_MAP:
        return jsonify({'error': 'Invalid class'}), 400
    equipped_value = CLASS_MAP[class_item]

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT owned_items FROM game_state WHERE user_id = %s', (current_user.id,))
                gs = cur.fetchone()

            if class_item and class_item not in list(gs['owned_items']):
                return jsonify({'error': 'Class not owned'}), 400

            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET equipped_class = %s WHERE user_id = %s',
                    (equipped_value, current_user.id),
                )
            conn.commit()
        return jsonify({'ok': True, 'equipped_class': equipped_value})
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
    err = require_json()
    if err:
        return err

    data    = request.get_json(silent=True) or {}
    item_id = data.get('item_id') or ''

    if item_id not in COSMETIC_SLOTS:
        return jsonify({'error': 'Invalid cosmetic item'}), 400

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT owned_items, active_cosmetics FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned            = list(gs['owned_items'])
            active_cosmetics = list(gs['active_cosmetics'])

            if item_id not in owned:
                return jsonify({'error': 'Not owned'}), 400

            if item_id in active_cosmetics:
                # Unequip (toggle off)
                active_cosmetics = [c for c in active_cosmetics if c != item_id]
            else:
                # Remove all items in same slot, then equip
                slot = COSMETIC_SLOTS[item_id]
                active_cosmetics = [c for c in active_cosmetics if COSMETIC_SLOTS.get(c) != slot]
                active_cosmetics.append(item_id)

            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET active_cosmetics = %s WHERE user_id = %s',
                    (active_cosmetics, current_user.id),
                )
            conn.commit()

        return jsonify({'active_cosmetics': active_cosmetics})
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


@game_bp.route('/api/leaderboard')
@limiter.limit('30 per minute')
def leaderboard():
    try:
        with db_connection() as conn:
            ensure_current_season(conn)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT u.username, gs.wins, gs.losses, gs.streak, gs.best_streak,
                              gs.winmult_inf_level, gs.bonusmult_inf_level,
                              gs.last_spin_at
                       FROM game_state gs
                       JOIN users u ON u.id = gs.user_id
                       WHERE gs.wins > 0
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
                'username':           r['username'],
                'wins':               int(r['wins']),
                'losses':             r['losses'],
                'streak':             r['streak'],
                'best_streak':        r['best_streak'],
                'winmult_inf_level':  r['winmult_inf_level'],
                'bonusmult_inf_level': r['bonusmult_inf_level'],
                'active':             bool(active),
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
@csrf.exempt
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
@csrf.exempt
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
@csrf.exempt
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


@game_bp.route('/api/wager/insurance', methods=['POST'])
@login_required
@csrf.exempt
def wager_insurance():
    """T74: Activate insurance — consumes a charge immediately, caps the next
    loss at the stake, refunds the escrowed wins on a loss. Charge is wasted
    on a win (it's a gamble, by design)."""
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'wager_insurance' not in gs['owned_items']:
                return jsonify({'error': 'Insurance not unlocked'}), 403
            # T74: refresh charges before arming so the player always sees the
            # freshest count (mirrors /api/state behaviour).
            now_utc = dt.datetime.now(timezone.utc)
            charges = min(int(gs.get('wager_insurance_charges', 0) or 0),
                          WAGER_INSURANCE_MAX_CHARGES)
            last_recharge = gs.get('wager_insurance_last_recharge') or now_utc
            charges, last_recharge = _recharge_wager_insurance(
                charges, last_recharge, WAGER_INSURANCE_MAX_CHARGES, now_utc,
            )
            if charges <= 0:
                return jsonify({'error': 'No insurance charges left'}), 403
            if gs.get('wager_insurance_armed'):
                return jsonify({'error': 'Insurance already armed'}), 409
            new_charges = charges - 1
            # T74 AC#5: reset the recharge timer only if the new charge count
            # is still below the cap (timer pauses at cap).
            new_last_recharge = now_utc if new_charges < WAGER_INSURANCE_MAX_CHARGES else last_recharge
            cur.execute(
                '''UPDATE game_state
                   SET wager_insurance_charges = %s,
                       wager_insurance_armed = TRUE,
                       wager_insurance_last_recharge = %s
                   WHERE user_id = %s''',
                (new_charges, new_last_recharge, current_user.id),
            )
        conn.commit()
    return jsonify({'ok': True, 'message': 'Insurance activated',
                    'wager_insurance_charges': new_charges})


def _prestige_default(col):
    """T85: return the appropriate reset value for a column on prestige.

    Most columns zero out; booleans flip to FALSE; timestamps, JSONB and
    nullable scalars clear to NULL; text arrays empty; the single NOT NULL
    enum (active_wheel_mode) returns to its declared default.
    """
    if col in (
        'wins', 'losses', 'streak', 'best_streak', 'spin_count', 'win_count',
        'loss_count',
        'winmult_inf_level', 'bonusmult_inf_level', 'clickmult_inf_level',
        'streak_armor_level', 'jackpot_resonance_level', 'echo_amp_level',
        'proc_streak_level', 'proc_streak', 'lure_mastery_level',
        'wager_streak', 'wager_last_stake', 'wager_banked_wins',
        'wager_banked_losses', 'wager_insurance_charges',
        'wager_last_win_amount',
        'guard_charges', 'guard_last_regen_spin', 'resilience_last_use_spin',
        'dice_charges', 'fish_clicks', 'fish_exchange_total',
        'gravity_drift', 'biggest_win_announced',
    ):
        return 0
    if col in (
        'double_down_pending', 'wager_insurance_armed',
        'dice_rolled_since_spin', 'fishing_lucky_next',
    ):
        return False
    if col == 'active_wheel_mode':
        return 'steady'
    if col in (
        'wager_insurance_last_recharge', 'dice_last_recharge',
        'fishing_cast_at', 'fishing_bite_at',
    ):
        return dt.datetime.now(timezone.utc)
    if col in (
        'pending_dice', 'fastest_catch_pct', 'equipped_class', 'bounty_claimed_date',
    ):
        return None
    if col == 'caught_species':
        return []
    # Defensive fallback: zero. Should be unreachable because
    # PRESTIGE_RESET_COLUMNS is the single source of truth.
    return 0


@game_bp.route('/api/prestige', methods=['POST'])
@login_required
@csrf.exempt
def prestige_reset():
    """Prestige: reset wins for permanent bonus + legacy_wins preservation.

    T85: resets the full AC#1 scope — every retired / per-season column
    listed in PRESTIGE_RESET_COLUMNS. Preserves prestige_level, prestige_count,
    legacy_wins, owned_cosmetics, active_cosmetics, aquarium_species, loadouts,
    cosmetic_fragments, onboarding_step (T88), and wager_tokens (T85 AC#2).

    T86: wins are not zeroed — ``compute_wins_kept`` retains a fraction of
    them based on the player's prestige_efficiency level.
    """
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'prestige_unlock' not in gs['owned_items']:
                return jsonify({'error': 'Prestige not unlocked'}), 403
            current_level = gs.get('prestige_level', 0)
            if current_level >= MAX_PRESTIGE_LEVEL:
                return jsonify({'error': 'Already at max prestige'}), 403
            threshold = get_prestige_threshold(gs['owned_items'], current_level)
            if int(gs['wins']) < threshold:
                return jsonify({'error': f'Need {threshold} wins to prestige', 'current_wins': int(gs['wins'])}), 403
            new_level = current_level + 1
            new_prestige_count = gs.get('prestige_count', 0) + 1
            legacy_keep = get_legacy_keep_count(gs['owned_items'])
            current_wins = int(gs['wins'])
            new_legacy_wins = int(gs.get('legacy_wins', 0)) + current_wins
            new_wins = compute_wins_kept(current_wins, gs['owned_items'])
            new_owned_items = filter_kept_items(gs['owned_items'], legacy_keep)
            starting_prestige = get_starting_prestige(new_legacy_wins)
            # T85: one UPDATE per prestige, every reset column cleared.
            # Preserved columns (per AC#2): prestige_level, prestige_count,
            # legacy_wins, active_cosmetics, aquarium_species, cosmetic_fragments,
            # onboarding_step, wager_tokens. owned_items is rewritten to the
            # filtered list (kept functional + all cosmetics).
            reset_sql_parts = [
                'prestige_level = %s',
                'prestige_count = %s',
                'legacy_wins = %s',
                'wins = %s',
                'owned_items = %s',
            ]
            reset_params = [new_level, new_prestige_count, new_legacy_wins,
                            new_wins, new_owned_items]
            for col in PRESTIGE_RESET_COLUMNS:
                if col == 'wins':
                    continue  # handled above (retained, not zeroed)
                reset_sql_parts.append(f'{col} = %s')
                reset_params.append(_prestige_default(col))
            reset_sql_parts.append('wager_tokens = wager_tokens')  # preserve
            cur.execute(
                f'''UPDATE game_state
                    SET {', '.join(reset_sql_parts)}
                    WHERE user_id = %s''',
                tuple(reset_params) + (current_user.id,),
            )
        # Season 8: post system message on prestige
        post_system_message(conn, chat_triggers.prestige_msg(current_user.username, new_level),
                            'system', event_kind='prestige')
        # Bounty tracking
        bounty_date = dt.datetime.now(timezone.utc).date()
        increment_bounty(conn, current_user.id, 'bounty_prestige', bounty_date)
        # Community goal tracking
        season_info = get_season_info(conn)
        season_num = season_info.get('season_number', 8) if season_info else 8
        now_utc = dt.datetime.now(timezone.utc)
        week_num = get_week_number(now_utc)
        _, goal_def = get_active_goal(conn, season_num, week_num)
        if goal_def and goal_def['metric'] == 'prestiges':
            increment_goal(conn, goal_def['goal_id'], current_user.id, 1)
            check_goal_completion(conn, goal_def['goal_id'])
        conn.commit()
    return jsonify({
        'prestige_level': new_level,
        'prestige_count': new_prestige_count,
        'legacy_wins': new_legacy_wins,
        'wins_kept': new_wins,
        'starting_prestige': starting_prestige,
    })


@game_bp.route('/api/prestige', methods=['GET'])
@login_required
def prestige_info():
    """Get prestige status and requirements."""
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id)
            level = gs.get('prestige_level', 0)
            owned = gs.get('owned_items', [])
            threshold = get_prestige_threshold(owned, level) if level < MAX_PRESTIGE_LEVEL else None
            can = can_prestige(int(gs['wins']), owned, level)
    return jsonify({
        'prestige_level': level,
        'prestige_count': gs.get('prestige_count', 0),
        'legacy_wins': int(gs.get('legacy_wins', 0)),
        'current_wins': int(gs['wins']),
        'next_threshold': threshold,
        'can_prestige': can,
        'max_level': MAX_PRESTIGE_LEVEL,
        'bonus_pct': get_prestige_bonus(level),
    })


@game_bp.route('/api/bounties', methods=['GET'])
@login_required
def get_bounties_endpoint():
    """Get today's bounty status."""
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
                       SET onboarding_step = 5,
                           wager_tokens = wager_tokens + 100
                       WHERE user_id = %s''',
                    (current_user.id,),
                )
                onboarding_advance = True
        conn.commit()
    return jsonify({'bounties': status, 'date': str(bounty_date), 'onboarding_advance': onboarding_advance})


@game_bp.route('/api/bounties/claim', methods=['POST'])
@login_required
@csrf.exempt
def claim_bounty():
    """Claim a completed bounty."""
    err = require_json()
    if err:
        return err
    bounty_id = (request.json or {}).get('bounty_id')
    if not bounty_id:
        return jsonify({'error': 'bounty_id required'}), 400
    bounty_date = dt.datetime.now(timezone.utc).date()
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if gs.get('bounty_claimed_date') == bounty_date:
                return jsonify({'error': 'Already claimed today'}), 400
            rewards = get_claim_rewards(conn, current_user.id, bounty_date)
            if rewards is None:
                return jsonify({'error': 'Bounty not claimable'}), 400
            cur.execute(
                '''UPDATE game_state SET cosmetic_fragments = cosmetic_fragments + %s,
                    wager_tokens = wager_tokens + %s,
                    bounty_claimed_date = %s
                   WHERE user_id = %s''',
                (rewards['cosmetic_fragments'], rewards['tokens'], bounty_date, current_user.id),
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
    """Get singularity meter status."""
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT total_contributed, target, filled, filled_at, fill_count FROM singularity_meter WHERE id = 1')
            row = cur.fetchone()
    return jsonify({
        'total_contributed': row['total_contributed'] if row else 0,
        'target':            row['target'] if row else 100_000_000,
        'filled':            row['filled'] if row else False,
        'fill_count':        row['fill_count'] if row else 0,
    })


@game_bp.route('/api/singularity/contribute', methods=['POST'])
@login_required
@csrf.exempt
def singularity_contribute():
    """Contribute fish_clicks to the singularity meter (per-player capped, per fill cycle)."""
    err = require_json()
    if err:
        return err
    amount = (request.json or {}).get('amount', 0)
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount'}), 400
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            cur.execute('SELECT fill_count FROM singularity_meter WHERE id = 1 FOR UPDATE')
            meter_row = cur.fetchone()
            fill_count = meter_row['fill_count'] if meter_row else 0

            cur.execute(
                '''SELECT contributed FROM singularity_contributions
                   WHERE user_id = %s AND fill_count = %s''',
                (current_user.id, fill_count),
            )
            contrib_row = cur.fetchone()
            already = contrib_row['contributed'] if contrib_row else 0
            remaining_cap = SINGULARITY_PER_PLAYER_CAP - already

            actual_amount = min(amount, int(gs['fish_clicks']), remaining_cap)
            if actual_amount <= 0:
                return jsonify({'error': 'Nothing to contribute (insufficient fish or cap reached)'}), 403

            cur.execute(
                'UPDATE game_state SET fish_clicks = fish_clicks - %s WHERE user_id = %s',
                (actual_amount, current_user.id),
            )
            cur.execute(
                '''INSERT INTO singularity_contributions (user_id, fill_count, contributed)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (user_id, fill_count) DO UPDATE
                       SET contributed = singularity_contributions.contributed + %s''',
                (current_user.id, fill_count, actual_amount, actual_amount),
            )
            cur.execute(
                '''UPDATE singularity_meter SET total_contributed = total_contributed + %s,
                   filled = CASE WHEN total_contributed + %s >= target THEN TRUE ELSE filled END,
                   filled_at = CASE WHEN total_contributed + %s >= target AND filled_at IS NULL THEN NOW() ELSE filled_at END
                   WHERE id = 1 RETURNING total_contributed, target, filled''',
                (actual_amount, actual_amount, actual_amount),
            )
            row = cur.fetchone()
            amount = actual_amount
            # Season 8: post system message if meter just filled (crossed threshold this contribution)
            if row['filled'] and (row['total_contributed'] - amount) < row['target']:
                post_system_message(conn, chat_triggers.singularity_fill_msg(int(row['total_contributed'])),
                                    'system', event_kind='singularity_fill')
        conn.commit()
    return jsonify({
        'total_contributed': row['total_contributed'],
        'target': row['target'],
        'filled': row['filled'],
        'contributed': amount,
    })


@game_bp.route('/api/loadout', methods=['GET'])
@login_required
def get_loadout():
    """Get saved build loadouts."""
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT slot, config FROM build_loadouts WHERE user_id = %s ORDER BY slot',
                        (current_user.id,))
            rows = cur.fetchall()
    loadouts = {row['slot']: row['config'] for row in rows}
    return jsonify({'loadouts': loadouts})


@game_bp.route('/api/loadout', methods=['POST'])
@login_required
@csrf.exempt
def save_loadout():
    """Save a build loadout to a slot (1-3)."""
    err = require_json()
    if err:
        return err
    data = request.json or {}
    slot = data.get('slot', 1)
    raw = data.get('loadout', {}) or {}
    if not (1 <= slot <= 3):
        return jsonify({'error': 'Slot must be 1-3'}), 400
    # A loadout is equipped_class + active_wheel_mode only (spec S11). Never
    # persist client-supplied owned_items/active_cosmetics — apply_loadout
    # used to write those straight to game_state with no validation, letting
    # any player grant themselves every item in the shop for free.
    loadout_data = {
        'equipped_class':    raw.get('equipped_class'),
        'active_wheel_mode': raw.get('active_wheel_mode', 'steady'),
    }
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''INSERT INTO build_loadouts (user_id, slot, config)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (user_id, slot) DO UPDATE SET config = EXCLUDED.config''',
                (current_user.id, slot, psycopg2.extras.Json(loadout_data)),
            )
        conn.commit()
    return jsonify({'ok': True, 'slot': slot})


_LOADOUT_CLASS_ITEMS = {'earth': 'class_earth', 'moon': 'class_moon', 'star': 'class_star'}


@game_bp.route('/api/loadout/apply', methods=['POST'])
@login_required
@csrf.exempt
def apply_loadout():
    """Apply a saved loadout — sets equipped_class and active_wheel_mode only.

    Re-validates ownership/availability server-side rather than trusting the
    saved blob; falls back to the player's current value for anything that
    no longer checks out (e.g. a class they've since lost, a mode that has
    rotated out of availability).
    """
    err = require_json()
    if err:
        return err
    slot = (request.json or {}).get('slot', 1)
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT config FROM build_loadouts WHERE user_id = %s AND slot = %s',
                        (current_user.id, slot))
            row = cur.fetchone()
            if not row:
                return jsonify({'error': 'No loadout in that slot'}), 404
            loadout = row['config']

            gs = _load_game_state(cur, current_user.id, for_update=True)
            owned = list(gs['owned_items'])

            class_value = loadout.get('equipped_class')  # 'earth' | 'moon' | 'star' | None
            if class_value is None:
                equipped_value = None
            elif class_value in _LOADOUT_CLASS_ITEMS and _LOADOUT_CLASS_ITEMS[class_value] in owned:
                equipped_value = class_value
            else:
                equipped_value = gs['equipped_class']

            mode = loadout.get('active_wheel_mode', 'steady')
            available = get_available_modes(get_week_number())
            if mode != 'steady' and mode not in available:
                mode = gs.get('active_wheel_mode') or 'steady'

            cur.execute(
                '''UPDATE game_state SET equipped_class = %s, active_wheel_mode = %s WHERE user_id = %s''',
                (equipped_value, mode, current_user.id),
            )
        conn.commit()
    return jsonify({'ok': True, 'equipped_class': equipped_value, 'active_wheel_mode': mode})


@game_bp.route('/api/legacy-boards', methods=['GET'])
@login_required
def legacy_boards():
    """Get legacy wins leaderboard (across all seasons)."""
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                '''SELECT u.username, gs.legacy_wins
                   FROM game_state gs JOIN users u ON u.id = gs.user_id
                   WHERE gs.legacy_wins > 0
                   ORDER BY gs.legacy_wins DESC LIMIT 50'''
            )
            rows = cur.fetchall()
    return jsonify({'boards': [{'username': r['username'], 'legacy_wins': int(r['legacy_wins'])} for r in rows]})


@game_bp.route('/api/guard', methods=['POST'])
@login_required
@csrf.exempt
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
@csrf.exempt
def auto_spin_start():
    """Start server-side auto-spin with an optional budget.

    T107: gated on the `auto_spin_unlock` shop item. The auto-spin UI is
    hidden in the wager panel for players who haven't bought the upgrade.
    """
    err = require_json()
    if err:
        return err
    budget = (request.json or {}).get('budget', 0)
    try:
        budget = int(budget)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid budget'}), 400
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'auto_spin_unlock' not in (gs.get('owned_items') or []):
                return jsonify({'error': 'Buy auto_spin_unlock from the shop (5,000 wins)'}), 403
            # Treat as active only when BOTH auto_spin_since is set AND the
            # budget is positive. A stale auto_spin_since (left over from a
            # prior session / test) with budget=0 is limbo state — let the
            # player (or test) restart cleanly. Matches the `auto_spin_active`
            # gate in /api/state's state response.
            if gs.get('auto_spin_since') is not None and int(gs.get('auto_spin_budget', 0)) > 0:
                return jsonify({'error': 'Auto-spin already active'}), 409
            # Wipe any stale auto_spin_since so the new activation starts fresh.
            cur.execute(
                '''UPDATE game_state
                   SET auto_spin_since = NOW(), auto_spin_budget = %s
                   WHERE user_id = %s''',
                (budget, current_user.id),
            )
        conn.commit()
    return jsonify({'ok': True, 'budget': budget})


@game_bp.route('/api/auto-spin/stop', methods=['POST'])
@login_required
@csrf.exempt
def auto_spin_stop():
    """Stop server-side auto-spin."""
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''UPDATE game_state SET auto_spin_since = NULL, auto_spin_budget = 0 WHERE user_id = %s''',
                (current_user.id,),
            )
        conn.commit()
    return jsonify({'ok': True})


@game_bp.route('/api/aquarium', methods=['GET'])
@login_required
def aquarium_status():
    """Get aquarium species collection."""
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id)
    species = list(gs.get('caught_species', []))
    return jsonify({
        'species': species,
        'wager_tokens': gs.get('wager_tokens', 0),
        'luck_bonus': len(species) * 0.001 if 'aquarium' in gs.get('owned_items', []) else 0.0,
    })


@game_bp.route('/api/wheel-mode', methods=['POST'])
@login_required
@csrf.exempt
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
                                              wager_insurance_armed = FALSE,
                                              double_down_pending = FALSE,
                                              gravity_drift = 0
                       WHERE user_id = %s''',
                    (mode, current_user.id))
                response['wager_streak'] = 0
                response['wager_insurance_armed'] = False
                response['double_down_pending'] = False
                response['gravity_drift'] = 0
            else:
                cur.execute('UPDATE game_state SET active_wheel_mode = %s WHERE user_id = %s',
                            (mode, current_user.id))
        conn.commit()
    return jsonify(response)


# Note: there is no separate /api/fish-to-wager endpoint. wager_tokens are
# awarded automatically at catch time in reel() when fish_to_wager is owned —
# a second manual conversion endpoint keyed on the permanent caught_species
# list would let players re-claim the same catch for tokens indefinitely.
