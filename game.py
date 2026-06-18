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
                    ITEM_CURRENCY, INFINITE_UPGRADE_CURRENCY,
                    inf_upgrade_cost, win_mult_from_level, bonus_mult_from_level,
                    lure_mastery_mult, jackpot_pct, echo_amp_pct, proc_streak_mult,
                    CLASS_EARTH_FISH_BONUS, CLASS_MOON_PROC_BONUS, CLASS_STAR_WIN_BONUS,
                    streak_bonus, DICE_RECHARGE_SECONDS, dice_max_charges,
                    UPGRADE_TIER_THRESHOLDS, item_tier,
                    FISH_CATALOG, roll_fish, lure_bite_delay_seconds, fish_value, autofisher_catch_rate,
                    AUTO_SPIN_INTERVAL_SECONDS, MAX_SPINS_PER_TICK, CATCH_UP_THRESHOLD,
                    AUTO_FISH_INTERVAL_SECONDS, MAX_FISH_CATCHUP_TICKS, FISH_CATCHUP_THRESHOLD,
                    HAPPY_HOUR_START_UTC, HAPPY_HOUR_END_UTC, FISH_TO_WAGER_RATES)
from seasons import ensure_current_season, get_season_info, advance_season
from security import require_json
from wagers import (validate_stake, compute_hot_streak_bonus, should_reset_streak,
                    apply_safety_net, compute_wager_payout, compute_wager_loss,
                    MAX_STAKE, MIN_STAKE)
from wheel_modes import WHEEL_MODES, get_available_modes, get_rotating_mode, get_week_number, is_mode_available
from prestige import get_prestige_bonus, get_starting_prestige, can_prestige, get_prestige_threshold, get_legacy_keep_count, MAX_PRESTIGE_LEVEL
from replays import generate_replay, should_generate_replay, decode_replay
from bounties import get_daily_bounties, increment_bounty, get_bounty_status, get_claim_rewards, BOUNTY_DEFS
from community_goals import COMMUNITY_GOAL_DEFS, get_active_goal, increment_goal, check_goal_completion, get_player_contribution
from chat import post_system_message

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
           spin_count, win_count, loss_count,
           winmult_inf_level, bonusmult_inf_level, streak_armor_level,
           jackpot_resonance_level, echo_amp_level, proc_streak_level, proc_streak,
           lure_mastery_level, equipped_class, fish_clicks, caught_species, active_cosmetics,
           dice_charges, dice_last_recharge, jackpot_echo_next, dice_rolled_since_spin,
           pending_dice, auto_spin_since, last_spin_at, active_tab_id, tab_last_seen,
           auto_fish_enabled, auto_fish_last_tick,
           prestige_level, prestige_count, legacy_wins, onboarding_step, auto_spin_budget,
           wager_streak, wager_last_stake, double_down_pending, wager_banked_wins,
           wager_insurance_charges, active_wheel_mode,
           wager_tokens, aquarium_species, cosmetic_fragments,
           guard_charges, guard_last_regen_spin, resilience_last_use_spin
    FROM game_state WHERE user_id = %s
'''


def _load_game_state(cur, user_id: int, *, for_update: bool = False):
    sql = _GAME_STATE_SQL + ('FOR UPDATE' if for_update else '')
    cur.execute(sql, (user_id,))
    return cur.fetchone()


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


# Cap wins to prevent JS Infinity display (Number.MAX_VALUE ~1.8e308)
_MAX_WINS = 5_000_000  # Season 8 economy ceiling (was round(9.99e99))


def _build_spin_context(gs: dict) -> dict:
    """Compute immutable per-request spin context from game state. Shared by spin() and tick()."""
    equipped_class = gs['equipped_class']
    moon_bonus = CLASS_MOON_PROC_BONUS if equipped_class == 'moon' else 0.0
    star_win_bonus = CLASS_STAR_WIN_BONUS if equipped_class == 'star' else 0.0
    # Season 8: prestige bonus is flat +2% per level (max +40% at level 20)
    prestige_bonus = get_prestige_bonus(gs.get('prestige_level', 0))
    # Season 8: aquarium luck bonus — +0.1% per unique species
    aquarium_species = gs.get('aquarium_species', [])
    aquarium_count = len(aquarium_species) if aquarium_species else 0
    aquarium_luck = aquarium_count * 0.001 if 'aquarium' in gs.get('owned_items', []) else 0.0

    # Season 8: old inf levels frozen at 0 — use flat values
    base_win_mult = win_mult_from_level(0)  # always 1 (levels frozen)
    base_bonus_mult = bonus_mult_from_level(0)  # always 1

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
    catchup_bonus_active: bool = False,
    # ── Season 8: wager + wheel mode ──
    stake: int = 1,
    wager_streak: int = 0,
    wager_last_stake: int = 0,
    active_wheel_mode: str = 'steady',
    aquarium_luck: float = 0.0,
) -> tuple[dict, dict]:
    """Resolve one spin. Returns (new_state, events). Does not mutate inputs."""
    original_wins   = wins
    original_losses = losses

    # Season 8: auto_guard removed — no auto-purchase logic
    auto_guard_failed = False

    # Season 8: wheel mode outcome determination (replaces singularity/50-50)
    lucky_seven_triggered = False
    mode = WHEEL_MODES.get(active_wheel_mode, WHEEL_MODES['steady'])

    if 'lucky_seven' in owned and spin_count % 7 == 0:
        outcome = 'win'
        lucky_seven_triggered = True
    elif pot_active:
        outcome = 'win' if random.random() < (pot_win_pct + aquarium_luck) else 'lose'
    elif catchup_bonus_active:
        outcome = 'win' if random.random() < (0.55 + aquarium_luck) else 'lose'
    else:
        # Mode-based probability roll
        win_pct = mode['win_pct'] / 100.0 + aquarium_luck
        jackpot_pct = mode['jackpot_pct'] / 100.0
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
    bonus_earned            = 0
    new_owned               = owned

    # Season 8: wager stake multiplier and hot streak
    owns_wager_unlock = 'wager_unlock' in owned
    actual_stake = validate_stake(stake, owns_wager_unlock)
    owns_hot_streak = 'wager_hot_streak' in owned
    if should_reset_streak(actual_stake, wager_last_stake):
        wager_streak = 0
    hot_streak_bonus = compute_hot_streak_bonus(wager_streak, owns_hot_streak)

    if outcome == 'lose':
        if 'regen_shield' in owned and regen_recharge_wins == 0:
            shield_used         = True
            shield_used_type    = 'regen_shield'
            regen_recharge_wins = REGEN_SHIELD_RECHARGE_WINS
            new_streak          = streak
        elif 'guard' in owned:
            guard_triggered = True
            guard_blocked = True
            new_owned  = [x for x in new_owned if x != 'guard']
            new_streak = streak
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
            actual_loss  = compute_wager_loss(base_loss, actual_stake)
            actual_loss  = apply_safety_net(actual_loss, actual_stake, 'wager_safety_net' in owned)
            losses      += actual_loss
            bonus_earned = -loss_bonus if loss_bonus > 0 else 0
    elif outcome == 'jackpot':
        new_streak = streak + 1 if streak >= 0 else 1
        if regen_recharge_wins > 0:
            regen_recharge_wins -= 1
        jackpot_hit = True
        jackpot_mult = mode.get('jackpot_multiplier', 25)
        raw_payout   = (effective_win_mult + bonus_earned) * jackpot_mult
        wager_payout = compute_wager_payout(raw_payout, actual_stake, hot_streak_bonus)
        wins        += wager_payout
        bonus_earned = wager_payout - effective_win_mult
        if random.random() < 0.05:
            new_jackpot_echo_next = True
        if jackpot_echo_pending:
            jackpot_echo_triggered = True
    else:  # win
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

        if jackpot_echo_pending:
            jackpot_echo_triggered = True
            jackpot_hit  = True
            raw_payout   = (effective_win_mult + bonus_earned) * 25
            wager_payout = compute_wager_payout(raw_payout, actual_stake, hot_streak_bonus)
            wins        += wager_payout
            bonus_earned = wager_payout - effective_win_mult
        elif 'jackpot' in owned and random.random() < jackpot_chance:
            jackpot_hit  = True
            raw_payout   = (effective_win_mult + bonus_earned) * 25
            wager_payout = compute_wager_payout(raw_payout, actual_stake, hot_streak_bonus)
            wins        += wager_payout
            bonus_earned = wager_payout - effective_win_mult
            if random.random() < 0.05:
                new_jackpot_echo_next = True
        else:
            if 'win_echo' in owned and random.random() < echo_chance:
                echo_triggered = True
                raw_payout   = (effective_win_mult + bonus_earned) * 2
                wager_payout = compute_wager_payout(raw_payout, actual_stake, hot_streak_bonus)
                wins        += wager_payout
                bonus_earned = wager_payout - effective_win_mult
            else:
                base_payout = effective_win_mult + bonus_earned
                wager_payout = compute_wager_payout(base_payout, actual_stake, hot_streak_bonus)
                wins += wager_payout

        # Update wager streak on win
        if actual_stake == wager_last_stake or wager_last_stake == 0:
            wager_streak += 1
        else:
            wager_streak = 1

    new_best_streak = max(best_streak, new_streak) if new_streak > 0 else best_streak
    wins = min(wins, _MAX_WINS)

    # Map outcome to a CSS rotation angle that lands the pointer in the correct
    # visual segment.  Segments are arranged clockwise from 12-o'clock:
    #   WIN  → LOSE → JACKPOT (tiny sliver back to 12-o'clock)
    # CSS rotation range per zone:
    #   JACKPOT : [0,   J)
    #   LOSE    : [J,   J+L)
    #   WIN     : [J+L, 360)
    _m = WHEEL_MODES.get(active_wheel_mode, WHEEL_MODES['steady'])
    _j_deg = _m['jackpot_pct'] / 100 * 360
    _l_deg = _m['loss_pct']    / 100 * 360
    _w_deg = _m['win_pct']     / 100 * 360
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
    }
    return new_state, events


def _events_to_response(events: dict) -> dict:
    """Convert spin events into the JSON response payload shared by spin() and tick()."""
    return {
        'result':                  events['result'],
        'wins_delta':              events['wins_delta'],
        'losses_delta':            events['losses_delta'],
        'streak':                  events['streak'],
        'owned_items':             events['owned_items'],
        'regen_recharge_wins':     events['regen_recharge_wins'],
        'shield_used':             events['shield_used'],
        'shield_used_type':        events['shield_used_type'],
        'shield_broke':            events['shield_broke'],
        'guard_triggered':         events['guard_triggered'],
        'guard_blocked':           events['guard_blocked'],
        'bonus_earned':            events['bonus_earned'],
        'echo_triggered':          events['echo_triggered'],
        'jackpot_hit':             events['jackpot_hit'],
        'jackpot_echo_triggered':  events['jackpot_echo_triggered'],
        'jackpot_echo_next':       events['jackpot_echo_next'],
        'resilience_triggered':    events['resilience_triggered'],
        'lucky_seven_triggered':   events['lucky_seven_triggered'],
        'fortune_charm_triggered': events['fortune_charm_triggered'],
        'active_cosmetics':        events['active_cosmetics'],
        'auto_guard_failed':       events['auto_guard_failed'],
        'proc_streak':             events['proc_streak'],
        'wager_streak':            events.get('wager_streak', 0),
        'stake':                   events.get('stake', 1),
    }


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
                              active_cosmetics, spin_count, win_count,
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
                              active_wheel_mode, wager_tokens, aquarium_species,
                              cosmetic_fragments, guard_charges
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
            'wager_streak':         gs.get('wager_streak', 0),
            'wager_last_stake':     gs.get('wager_last_stake', 0),
            'double_down_pending':  bool(gs.get('double_down_pending', False)),
            'wager_banked_wins':    gs.get('wager_banked_wins', 0),
            'wager_insurance_charges': gs.get('wager_insurance_charges', 0),
            'active_wheel_mode':    gs.get('active_wheel_mode', 'steady'),
            'available_wheel_modes': available_modes,
            'wager_tokens':         gs.get('wager_tokens', 0),
            'aquarium_species':     list(gs.get('aquarium_species', [])),
            'cosmetic_fragments':   gs.get('cosmetic_fragments', 0),
            'guard_charges':        gs.get('guard_charges', 0),
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

            # Build spin context (immutable for this request)
            ctx = _build_spin_context(gs)
            pot_win_pct_frac = float(pot_row['win_chance_pct']) / 100.0 if pot_row else 0.505

            # Season 8: get stake from request body; resolve double-down if pending
            req_stake = (request.json or {}).get('stake', 1)
            double_down_active = bool(gs.get('double_down_pending', False))
            if double_down_active:
                req_stake = req_stake * 2  # double-down doubles the stake

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
                # Season 8 additions
                stake=req_stake,
                wager_streak=gs.get('wager_streak', 0),
                wager_last_stake=gs.get('wager_last_stake', 0),
                active_wheel_mode=gs.get('active_wheel_mode', 'steady'),
                aquarium_luck=ctx.get('aquarium_luck', 0.0),
            )

            new_win_count  = gs['win_count']  + (1 if events['result'] in ('win', 'jackpot')  else 0)
            new_loss_count = gs['loss_count'] + (1 if events['result'] == 'lose' else 0)

            # Season 8: generate replay string for big wins
            replay_string = None
            if should_generate_replay(events['jackpot_hit'], events.get('stake', 1),
                                      events['result'], False, events.get('wager_streak', 0)):
                replay_string = generate_replay(
                    current_user.username, gs.get('active_wheel_mode', 'steady'),
                    events.get('stake', 1), events['result'], events['wins_delta']
                )
            # Season 8: post system message on jackpot
            if events['jackpot_hit']:
                post_system_message(conn, f'🎰 {current_user.username} hit a JACKPOT for {int(events["wins_delta"]):,} wins!', 'event')
            # Season 8: post system message on big double-down win (5x+ stake doubled = 10x+)
            if double_down_active and events['result'] in ('win', 'jackpot') and events.get('stake', 1) >= 10:
                post_system_message(conn, f'🔥 {current_user.username} won a 10x double-down for {int(events["wins_delta"]):,} wins!', 'event')

            # Season 8: bounty tracking
            bounty_date = dt.datetime.now(timezone.utc).date()
            if events['jackpot_hit']:
                increment_bounty(conn, current_user.id, 'bounty_jackpot', bounty_date)
            if events.get('stake', 1) >= 5 and events['result'] in ('win', 'jackpot'):
                increment_bounty(conn, current_user.id, 'bounty_wager5', bounty_date)
            if events.get('wager_streak', 0) == 10:
                increment_bounty(conn, current_user.id, 'bounty_streak10', bounty_date)
            # Season 8: community goal contribution hooks
            season_info = get_season_info(conn)
            season_num = season_info.get('season_number', 8) if season_info else 8
            week_num = get_week_number(now_utc)
            _, goal_def = get_active_goal(conn, season_num, week_num)
            if goal_def:
                if goal_def['metric'] == 'jackpots_landed' and events['jackpot_hit']:
                    increment_goal(conn, goal_def['goal_id'], current_user.id, 1)
                    check_goal_completion(conn, goal_def['goal_id'])
                elif goal_def['metric'] == 'wins_wagered' and events['result'] in ('win', 'jackpot'):
                    increment_goal(conn, goal_def['goal_id'], current_user.id, int(events.get('wins_delta', 0)))
                    check_goal_completion(conn, goal_def['goal_id'])

            # Season 8: onboarding advance
            onboarding_advance = False
            if gs.get('onboarding_step', 0) == 0:
                onboarding_advance = True
                # Season 8: post system message for new player first spin
                post_system_message(conn, f'🎉 {current_user.username} spun the wheel for the first time! Welcome to Season 8!', 'event')

            # Manual spin: add extra full rotations for the wheel animation
            total_rotation = random.randint(5, 8) * 360 + events['segment_angle']

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET wins = %s, losses = %s, streak = %s, best_streak = %s,
                           regen_recharge_wins = %s,
                           owned_items = %s, spin_count = %s, win_count = %s, loss_count = %s,
                           fish_clicks = %s, active_cosmetics = %s,
                           dice_charges = %s, dice_last_recharge = %s,
                           jackpot_echo_next = %s, proc_streak = %s,
                           dice_rolled_since_spin = FALSE,
                           last_spin_at = NOW(),
                           active_tab_id = %s, tab_last_seen = NOW(),
                          wager_streak = %s, wager_last_stake = %s,
                          double_down_pending = FALSE,
                          onboarding_step = CASE WHEN onboarding_step = 0 THEN 1 ELSE onboarding_step END
                      WHERE user_id = %s''',
                    (new_state['wins'], new_state['losses'],
                     new_state['streak'], new_state['best_streak'],
                     new_state['regen_recharge_wins'],
                     new_state['owned'], new_spin_count, new_win_count, new_loss_count,
                     gs['fish_clicks'], new_state['active_cosmetics'],
                     dice_charges, last_recharge,
                     new_state['jackpot_echo_next'], new_state['proc_streak'],
                     req_tab_id or gs['active_tab_id'],
                     new_state.get('wager_streak', 0), new_state.get('wager_last_stake', 1),
                     current_user.id),
                )
            conn.commit()

        resp = _events_to_response(events)
        resp['angle'] = total_rotation
        resp['new_spin_count'] = new_spin_count
        resp['dice_charges'] = dice_charges
        resp['dice_last_recharge'] = last_recharge.isoformat()
        resp['wager_streak'] = new_state.get('wager_streak', 0)
        resp['stake'] = new_state.get('wager_last_stake', 1)
        resp['replay_string'] = replay_string
        resp['onboarding_advance'] = onboarding_advance
        resp['double_down_active'] = double_down_active
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

            # Check catch-up bonus: last-place active player gets +5% win rate
            catchup_bonus_active = False
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT MIN(wins) AS min_wins, COUNT(*) AS active_count
                       FROM game_state
                       WHERE wins > 0
                         AND last_spin_at > NOW() - INTERVAL '24 hours' '''
                )
                rank_row = cur.fetchone()

            user_wins_now = int(gs['wins'])
            if (rank_row and rank_row['active_count'] >= 2
                    and rank_row['min_wins'] is not None
                    and user_wins_now > 0
                    and user_wins_now <= int(rank_row['min_wins'])
                    and cursor and (now_utc - cursor).total_seconds() < 86400):
                catchup_bonus_active = True

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
            active_cosmetics    = list(gs['active_cosmetics'])
            current_proc_streak = gs['proc_streak']

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
                    catchup_bonus_active=catchup_bonus_active,
                    # Season 8: auto-spin always uses stake=1, no wager streak
                    stake=1,
                    wager_streak=0,
                    wager_last_stake=0,
                    active_wheel_mode=gs.get('active_wheel_mode', 'steady'),
                    aquarium_luck=ctx.get('aquarium_luck', 0.0),
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

                new_win_count  += 1 if events['result'] == 'win'  else 0
                new_loss_count += 1 if events['result'] == 'lose' else 0

                if not is_catch_up:
                    resp = _events_to_response(events)
                    resp['angle'] = events['segment_angle']
                    resp['new_spin_count'] = new_spin_count
                    resp['dice_charges'] = dice_charges
                    resp['dice_last_recharge'] = last_recharge.isoformat()
                    spin_results.append(resp)

            # Advance last_spin_at cursor
            new_last_spin = cursor + timedelta(seconds=spins_due * AUTO_SPIN_INTERVAL_SECONDS)

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET wins = %s, losses = %s, streak = %s, best_streak = %s,
                           regen_recharge_wins = %s,
                           owned_items = %s, spin_count = %s, win_count = %s, loss_count = %s,
                           active_cosmetics = %s, jackpot_echo_next = %s,
                           dice_charges = %s, dice_last_recharge = %s,
                           proc_streak = %s,
                       dice_rolled_since_spin = FALSE, pending_dice = NULL,
                       auto_spin_budget = GREATEST(auto_spin_budget - %s, 0),
                       auto_spin_since = CASE WHEN auto_spin_budget - %s <= 0 THEN NULL ELSE auto_spin_since END,
                       last_spin_at = %s
                      WHERE user_id = %s''',
                    (current_wins, current_losses, streak, best_streak,
                     regen_recharge_wins,
                     owned, new_spin_count, new_win_count, new_loss_count,
                     active_cosmetics, jackpot_echo_next,
                     dice_charges, last_recharge,
                     current_proc_streak,
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
            'catchup_bonus_active':  catchup_bonus_active,
            'dice_rolled_since_spin': False,
            'proc_streak':           current_proc_streak,
            'auto_spin_budget':      budget_remaining,
            'auto_spin_active':      budget_remaining > 0,
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
        currency = INFINITE_UPGRADE_CURRENCY[item_id]  # always 'wins'
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

            # Season 5: tier gating — check win_count threshold
            tier = item_tier(item_id)
            if tier > 1:
                threshold = UPGRADE_TIER_THRESHOLDS[tier]
                if gs['win_count'] < threshold:
                    return jsonify({'error': f'Unlocks at {threshold:,} total wins'}), 403

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
                              catch_of_the_day_date
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
    """Bank wager_banked_wins into wins, reset wager_streak to 0."""
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            banked = int(gs.get('wager_banked_wins', 0))
            if banked <= 0:
                return jsonify({'error': 'No banked wins to claim'}), 400
            new_wins = int(gs['wins']) + banked
            cur.execute(
                '''UPDATE game_state SET wins = %s, wager_banked_wins = 0, wager_streak = 0
                   WHERE user_id = %s''',
                (new_wins, current_user.id),
            )
        conn.commit()
    return jsonify({'wins': new_wins, 'wager_streak': 0, 'banked': banked})

@game_bp.route('/api/wager/stake', methods=['POST'])
@login_required
@csrf.exempt
def wager_set_stake():
    """Set the wager stake for manual spins. Validates against wager_unlock."""
    err = require_json()
    if err:
        return err
    stake = (request.json or {}).get('stake', 1)
    try:
        stake = int(stake)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid stake'}), 400
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            owns_unlock = 'wager_unlock' in gs['owned_items']
            actual_stake = validate_stake(stake, owns_unlock)
            cur.execute('UPDATE game_state SET wager_last_stake = %s WHERE user_id = %s',
                        (actual_stake, current_user.id))
        conn.commit()
    return jsonify({'stake': actual_stake})


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
    """Activate insurance: caps next loss at stake. Only if wager_insurance owned."""
    err = require_json()
    if err:
        return err
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'wager_insurance' not in gs['owned_items']:
                return jsonify({'error': 'Insurance not unlocked'}), 403
            if gs.get('wager_insurance_charges', 0) <= 0:
                return jsonify({'error': 'No insurance charges left'}), 403
            cur.execute('UPDATE game_state SET wager_insurance_charges = wager_insurance_charges - 1 WHERE user_id = %s',
                        (current_user.id,))
        conn.commit()
    return jsonify({'ok': True, 'message': 'Insurance activated'})


@game_bp.route('/api/prestige', methods=['POST'])
@login_required
@csrf.exempt
def prestige_reset():
    """Prestige: reset wins for permanent bonus + legacy_wins preservation."""
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
            threshold = get_prestige_threshold(gs['owned_items'])
            if int(gs['wins']) < threshold:
                return jsonify({'error': f'Need {threshold} wins to prestige', 'current_wins': int(gs['wins'])}), 403
            new_level = current_level + 1
            new_prestige_count = gs.get('prestige_count', 0) + 1
            legacy_keep = get_legacy_keep_count(gs['owned_items'])
            new_legacy_wins = int(gs.get('legacy_wins', 0)) + int(gs['wins'])
            starting_prestige = get_starting_prestige(new_legacy_wins)
            cur.execute(
                '''UPDATE game_state
                   SET prestige_level = %s, prestige_count = %s,
                       legacy_wins = %s, wins = 0, streak = 0, best_streak = 0,
                       win_count = 0, loss_count = 0, losses = 0,
                       spin_count = 0, wager_streak = 0, wager_last_stake = 0,
                       double_down_pending = FALSE, wager_banked_wins = 0
                   WHERE user_id = %s''',
                (new_level, new_prestige_count, new_legacy_wins, current_user.id),
            )
        # Season 8: post system message on prestige
        post_system_message(conn, f'⭐ {current_user.username} reached Prestige Level {new_level}!', 'event')
    conn.commit()
    return jsonify({
        'prestige_level': new_level,
        'prestige_count': new_prestige_count,
        'legacy_wins': new_legacy_wins,
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
            threshold = get_prestige_threshold(owned) if level < MAX_PRESTIGE_LEVEL else None
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
    with db_connection() as conn:
        status = get_bounty_status(conn, current_user.id, bounty_date)
    return jsonify({'bounties': status, 'date': str(bounty_date)})


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
            rewards = get_claim_rewards(conn, current_user.id, bounty_id, bounty_date)
            if rewards is None:
                return jsonify({'error': 'Bounty not claimable'}), 400
            cur.execute(
                '''UPDATE game_state SET cosmetic_fragments = cosmetic_fragments + %s WHERE user_id = %s''',
                (rewards.get('cosmetic_fragments', 0), current_user.id),
            )
            if rewards.get('wins', 0) > 0:
                cur.execute('UPDATE game_state SET wins = wins + %s WHERE user_id = %s',
                            (rewards['wins'], current_user.id))
        # Season 8: post system message on bounty claim
        post_system_message(conn, f'🎯 {current_user.username} completed a bounty: {bounty_id}!', 'event')
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
    """Contribute wins to the singularity meter."""
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
            if int(gs['wins']) < amount:
                return jsonify({'error': 'Insufficient wins'}), 403
            cur.execute(
                '''UPDATE singularity_meter SET total_contributed = total_contributed + %s,
                   filled = CASE WHEN total_contributed + %s >= target THEN TRUE ELSE filled END,
                   filled_at = CASE WHEN total_contributed + %s >= target AND filled_at IS NULL THEN NOW() ELSE filled_at END
                   WHERE id = 1 RETURNING total_contributed, target, filled''',
                (amount, amount, amount),
            )
            row = cur.fetchone()
            # Season 8: post system message if meter just filled (crossed threshold this contribution)
            if row['filled'] and (row['total_contributed'] - amount) < row['target']:
                post_system_message(conn, f'🌀 The Singularity has converged! Total contributed: {int(row["total_contributed"]):,}', 'event')
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
            cur.execute('SELECT slot, loadout_data FROM build_loadouts WHERE user_id = %s ORDER BY slot',
                        (current_user.id,))
            rows = cur.fetchall()
    loadouts = {row['slot']: row['loadout_data'] for row in rows}
    return jsonify({'loadouts': loadouts})


@game_bp.route('/api/loadout', methods=['POST'])
@login_required
@csrf.exempt
def save_loadout():
    """Save a build loadout to a slot (1-5)."""
    err = require_json()
    if err:
        return err
    data = request.json or {}
    slot = data.get('slot', 1)
    loadout_data = data.get('loadout', {})
    if not (1 <= slot <= 5):
        return jsonify({'error': 'Slot must be 1-5'}), 400
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''INSERT INTO build_loadouts (user_id, slot, loadout_data)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (user_id, slot) DO UPDATE SET loadout_data = EXCLUDED.loadout_data''',
                (current_user.id, slot, psycopg2.extras.Json(loadout_data)),
            )
        conn.commit()
    return jsonify({'ok': True, 'slot': slot})


@game_bp.route('/api/loadout/apply', methods=['POST'])
@login_required
@csrf.exempt
def apply_loadout():
    """Apply a saved loadout — sets owned_items to the loadout contents."""
    err = require_json()
    if err:
        return err
    slot = (request.json or {}).get('slot', 1)
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT loadout_data FROM build_loadouts WHERE user_id = %s AND slot = %s',
                        (current_user.id, slot))
            row = cur.fetchone()
            if not row:
                return jsonify({'error': 'No loadout in that slot'}), 404
            loadout = row['loadout_data']
            owned = loadout.get('owned_items', [])
            cosmetics = loadout.get('active_cosmetics', [])
            cur.execute(
                '''UPDATE game_state SET owned_items = %s, active_cosmetics = %s WHERE user_id = %s''',
                (owned, cosmetics, current_user.id),
            )
        conn.commit()
    return jsonify({'ok': True, 'owned_items': owned, 'active_cosmetics': cosmetics})


@game_bp.route('/api/replay/share', methods=['POST'])
@login_required
@csrf.exempt
def share_replay():
    """Decode and validate a replay string for sharing."""
    err = require_json()
    if err:
        return err
    replay_string = (request.json or {}).get('replay', '')
    if not replay_string:
        return jsonify({'error': 'Replay string required'}), 400
    decoded = decode_replay(replay_string)
    if decoded is None:
        return jsonify({'error': 'Invalid replay'}), 400
    return jsonify({'replay': decoded})


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
    """Start server-side auto-spin with an optional budget."""
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
            if gs['auto_spin_since'] is not None:
                return jsonify({'error': 'Auto-spin already active'}), 409
            cur.execute(
                '''UPDATE game_state SET auto_spin_since = NOW(), auto_spin_budget = %s WHERE user_id = %s''',
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
    return jsonify({
        'species': list(gs.get('aquarium_species', [])),
        'wager_tokens': gs.get('wager_tokens', 0),
        'luck_bonus': len(gs.get('aquarium_species', [])) * 0.001 if 'aquarium' in gs.get('owned_items', []) else 0.0,
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
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE game_state SET active_wheel_mode = %s WHERE user_id = %s',
                        (mode, current_user.id))
        conn.commit()
    return jsonify({'ok': True, 'mode': mode})


@game_bp.route('/api/fish-to-wager', methods=['POST'])
@login_required
@csrf.exempt
def fish_to_wager():
    """Convert caught fish to wager_tokens. Rate depends on fish tier."""
    err = require_json()
    if err:
        return err
    fish_id = (request.json or {}).get('fish_id')
    if not fish_id:
        return jsonify({'error': 'fish_id required'}), 400
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if 'fish_to_wager' not in gs['owned_items']:
                return jsonify({'error': 'Fish-to-wager not unlocked'}), 403
            caught = list(gs.get('caught_species', []))
            if fish_id not in caught:
                return jsonify({'error': 'Fish not in collection'}), 400
            # Determine tier from FISH_CATALOG
            fish_info = FISH_CATALOG.get(fish_id, {})
            tier = fish_info.get('tier', 0)
            if tier >= len(FISH_TO_WAGER_RATES):
                tier = len(FISH_TO_WAGER_RATES) - 1
            tokens = FISH_TO_WAGER_RATES[tier]
            # catch_of_the_day: first conversion each UTC day gets 5x
            now_utc = dt.datetime.now(timezone.utc)
            today = now_utc.date()
            last_conversion = gs.get('last_fish_conversion_date')
            if 'catch_of_the_day' in gs['owned_items']:
                if last_conversion is None or last_conversion.date() != today:
                    tokens *= 5
            cur.execute(
                '''UPDATE game_state SET wager_tokens = wager_tokens + %s WHERE user_id = %s
                   RETURNING wager_tokens''',
                (tokens, current_user.id),
            )
            row = cur.fetchone()
        conn.commit()
    return jsonify({'tokens_earned': tokens, 'total_wager_tokens': row['wager_tokens']})
