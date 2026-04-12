import datetime as dt
import logging
import random
import secrets
from datetime import timezone, timedelta

import psycopg2.extras
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import db_connection
from extensions import limiter
from models import (ALL_ITEMS, INFINITE_UPGRADES, REGEN_SHIELD_RECHARGE_WINS, VALID_FISH_IDS,
                    ITEM_CURRENCY, INFINITE_UPGRADE_CURRENCY,
                    inf_upgrade_cost, win_mult_from_level, bonus_mult_from_level, click_mult_from_level,
                    streak_bonus, DICE_RECHARGE_SECONDS, dice_max_charges,
                    UPGRADE_TIER_THRESHOLDS, item_tier)
from seasons import ensure_current_season, get_season_info

COSMETIC_SLOTS = {
    'bg_ocean':   'bg', 'bg_royal':   'bg', 'bg_inferno': 'bg',
    'bg_forest':  'bg', 'bg_abyss':   'bg', 'bg_cosmic':  'bg',
    'fishsize_1': 'size', 'fishsize_2': 'size', 'fishsize_3': 'size',
    'confetti_1': 'confetti', 'confetti_2': 'confetti', 'confetti_3': 'confetti',
    'party_mode': 'party',
    'trail_1': 'trail', 'trail_2': 'trail', 'trail_3': 'trail',
    'trail_4': 'trail', 'trail_5': 'trail', 'trail_6': 'trail',
    'theme_fire': 'wheel', 'theme_ice': 'wheel', 'theme_neon': 'wheel',
    'theme_void': 'wheel', 'theme_gold': 'wheel',
    'golden_wheel': 'golden',
    'page_season1': 'page_theme', 'page_season2': 'page_theme', 'page_season3': 'page_theme', 'page_season4': 'page_theme', 'page_season5': 'page_theme',
    'final_frenzy': 'frenzy_mode',
    'auto_guard':   'auto_guard',
}
from security import require_json

log = logging.getLogger('wheel')
game_bp = Blueprint('game', __name__)


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
                              equipped_fish, shield_charges, regen_recharge_wins,
                              active_cosmetics, spin_count, win_count,
                              winmult_inf_level, bonusmult_inf_level, clickmult_inf_level,
                              streak_armor_level, low_spec_mode,
                              dice_charges, dice_last_recharge, jackpot_echo_next,
                              dice_rolled_since_spin
                       FROM game_state WHERE user_id = %s''',
                    (current_user.id,),
                )
                gs = cur.fetchone()
                cur.execute('SELECT total_contributed, target, win_chance_pct, filled, filled_at, last_decay_check FROM community_pot WHERE id = 1')
                pot = cur.fetchone()
                cur.execute('SELECT COALESCE(SUM(fish_clicks), 0) AS total FROM game_state')
                pending_row = cur.fetchone()
        total_pending_clicks = int(pending_row['total']) if pending_row else 0
        now_utc = dt.datetime.now(timezone.utc)
        # Brief 30-minute celebration window after a fill (UI only)
        pot_celebrate = bool(
            pot and pot['filled'] and pot['filled_at'] and
            pot['filled_at'] > now_utc - dt.timedelta(minutes=30)
        )
        # Recharge dice charges based on elapsed time
        owned_items     = list(gs['owned_items'])
        max_charges     = dice_max_charges(owned_items)
        dice_charges    = gs['dice_charges']
        last_recharge   = gs['dice_last_recharge']
        if last_recharge.tzinfo is None:
            last_recharge = last_recharge.replace(tzinfo=timezone.utc)
        elapsed_charges = int((now_utc - last_recharge).total_seconds() // DICE_RECHARGE_SECONDS)
        if elapsed_charges > 0 and dice_charges < max_charges:
            new_dice_charges = min(dice_charges + elapsed_charges, max_charges)
            new_last_recharge = last_recharge + timedelta(seconds=DICE_RECHARGE_SECONDS * elapsed_charges)
            dice_charges   = new_dice_charges
            last_recharge  = new_last_recharge
        return jsonify({
            'wins':               int(gs['wins']),
            'losses':             gs['losses'],
            'fish_clicks':        gs['fish_clicks'],
            'streak':             gs['streak'],
            'owned_items':        owned_items,
            'equipped_fish':      gs['equipped_fish'],
            'shield_charges':     gs['shield_charges'],
            'regen_recharge_wins': gs['regen_recharge_wins'],
            'active_cosmetics':   list(gs['active_cosmetics']),
            'spin_count':         gs['spin_count'],
            'win_count':          gs['win_count'],
            'season':             full_info,
            'winmult_inf_level':   gs['winmult_inf_level'],
            'bonusmult_inf_level': gs['bonusmult_inf_level'],
            'clickmult_inf_level': gs['clickmult_inf_level'],
            'streak_armor_level':  gs['streak_armor_level'],
            'low_spec_mode':       gs['low_spec_mode'],
            'dice_charges':           dice_charges,
            'dice_last_recharge':     last_recharge.isoformat(),
            'jackpot_echo_next':      gs['jackpot_echo_next'],
            'dice_rolled_since_spin': bool(gs['dice_rolled_since_spin']),
            'community_pot': {
                'total_contributed':  pot['total_contributed'] if pot else 0,
                'target':             pot['target']            if pot else 1_000,
                'filled':             pot['filled']            if pot else False,
                'active':             pot_celebrate,
                'win_chance_pct':     float(pot['win_chance_pct']) if pot else 50.0,
                'total_pending_clicks': total_pending_clicks,
            } if pot else None,
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
                cur.execute(
                    '''SELECT wins, losses, streak, best_streak, owned_items, shield_charges, regen_recharge_wins,
                              spin_count, win_count, loss_count,
                              winmult_inf_level, bonusmult_inf_level, streak_armor_level,
                              fish_clicks, active_cosmetics,
                              dice_charges, dice_last_recharge, jackpot_echo_next,
                              dice_rolled_since_spin
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

                cur.execute('SELECT filled, filled_at, win_chance_pct, last_decay_check, total_contributed, target FROM community_pot WHERE id = 1')
                pot_row = cur.fetchone()

            owned               = list(gs['owned_items'])
            streak              = gs['streak']
            best_streak         = gs['best_streak']
            shield_charges      = gs['shield_charges']
            regen_recharge_wins = gs['regen_recharge_wins']
            fish_clicks         = gs['fish_clicks']
            active_cosmetics    = list(gs['active_cosmetics'])
            now_utc             = dt.datetime.now(timezone.utc)

            pot_active = bool(
                pot_row and pot_row['filled'] and pot_row['filled_at'] and
                pot_row['filled_at'] > now_utc - dt.timedelta(minutes=30)
            )
            # Auto-reset expired pot: advance to next target (×1.5), reset contributions
            if pot_row and pot_row['filled'] and not pot_active:
                new_pot_target = max(int(pot_row['target'] * 1.5), 1)
                with conn.cursor() as cur2:
                    cur2.execute(
                        '''UPDATE community_pot SET filled = false, filled_at = NULL,
                           total_contributed = 0, target = %s, last_decay_check = NOW()
                           WHERE id = 1''',
                        (new_pot_target,)
                    )

            # Community pot: apply target decay if 12+ hours since last check (only when pot is not active)
            if pot_row and pot_row['last_decay_check'] and not pot_active:
                last_decay = pot_row['last_decay_check']
                if last_decay.tzinfo is None:
                    last_decay = last_decay.replace(tzinfo=timezone.utc)
                decay_periods = int((now_utc - last_decay).total_seconds() / (12 * 3600))
                if decay_periods > 0:
                    new_target = int(pot_row['target'])
                    for _ in range(decay_periods):
                        new_target = max(500, int(new_target * 0.8))
                    # Safety: never drop below current fill amount + 1
                    if pot_row['total_contributed'] > 0:
                        new_target = max(new_target, int(pot_row['total_contributed']) + 1)
                    new_decay_ts = last_decay + timedelta(hours=12 * decay_periods)
                    with conn.cursor() as cur2:
                        cur2.execute(
                            'UPDATE community_pot SET target = %s, last_decay_check = %s WHERE id = 1',
                            (new_target, new_decay_ts)
                        )

            # Dice recharge
            dice_charges   = gs['dice_charges']
            last_recharge  = gs['dice_last_recharge']
            if last_recharge.tzinfo is None:
                last_recharge = last_recharge.replace(tzinfo=timezone.utc)
            max_charges = dice_max_charges(owned)
            elapsed_charges = int((now_utc - last_recharge).total_seconds() // DICE_RECHARGE_SECONDS)
            if elapsed_charges > 0 and dice_charges < max_charges:
                new_dice_charges  = min(dice_charges + elapsed_charges, max_charges)
                new_last_recharge = last_recharge + timedelta(seconds=DICE_RECHARGE_SECONDS * elapsed_charges)
                dice_charges      = new_dice_charges
                last_recharge     = new_last_recharge

            # Auto-guard: if enabled and guard is gone, buy one before spinning (costs wins)
            auto_guard_failed = False
            original_wins  = int(gs['wins'])
            original_losses = gs['losses']
            new_wins = original_wins
            if 'auto_guard' in owned and 'auto_guard' in active_cosmetics and 'guard' not in owned:
                if new_wins >= 500:
                    owned       = owned + ['guard']
                    new_wins   -= 500
                    wins_delta  = -500
                else:
                    active_cosmetics = [c for c in active_cosmetics if c != 'auto_guard']
                    auto_guard_failed = True

            # New spin count (used by lucky_seven)
            new_spin_count = gs['spin_count'] + 1

            # Determine outcome
            lucky_seven_triggered = False
            if 'singularity' in owned:
                outcome = 'win'
            elif 'lucky_seven' in owned and new_spin_count % 7 == 0:
                outcome = 'win'
                lucky_seven_triggered = True
            elif pot_active:
                pot_win_pct = float(pot_row['win_chance_pct']) if pot_row else 50.5
                outcome = 'win' if random.random() < (pot_win_pct / 100.0) else 'lose'
            else:
                outcome = secrets.choice(['win', 'lose'])

            # Multipliers — derived entirely from inf level columns
            win_mult   = win_mult_from_level(gs['winmult_inf_level'])
            bonus_mult = bonus_mult_from_level(gs['bonusmult_inf_level'])

            shield_used      = False
            shield_broke     = False
            shield_used_type = None
            guard_triggered  = False
            guard_blocked    = False
            # new_wins already initialized above (auto-guard may have deducted from it)
            new_losses       = gs['losses']
            bonus_earned     = 0
            new_owned        = owned
            echo_triggered          = False
            jackpot_hit             = False
            jackpot_echo_triggered  = False
            resilience_triggered    = False
            fortune_charm_triggered = False
            new_jackpot_echo_next   = False  # whether next spin should echo

            # Jackpot echo from previous spin
            jackpot_echo_pending = bool(gs['jackpot_echo_next'])

            # Resilience: dynamic chance based on streak_armor_level (base 50%, +1%/level, cap 60%)
            resilience_chance = min(0.50 + gs['streak_armor_level'] * 0.01, 0.60)

            if outcome == 'lose':
                # Regen shield: protects any loss when charged
                if 'regen_shield' in owned and regen_recharge_wins == 0:
                    shield_used         = True
                    shield_used_type    = 'regen_shield'
                    regen_recharge_wins = REGEN_SHIELD_RECHARGE_WINS
                    new_streak          = streak

                # Guard: 50% chance to block any loss
                elif 'guard' in owned:
                    guard_triggered = True
                    if random.random() < 0.50:
                        guard_blocked = True
                        new_owned     = [x for x in new_owned if x != 'guard']
                        new_streak    = streak  # loss blocked, keep streak
                    else:
                        # Guard failed: take the loss
                        if 'resilience' in owned and streak > 0 and random.random() < resilience_chance:
                            resilience_triggered = True
                            new_streak = max(0, streak - 1)
                        else:
                            new_streak = streak - 1 if streak <= 0 else -1
                        loss_count   = abs(new_streak) if new_streak < 0 else 0
                        loss_bonus   = streak_bonus(loss_count) * bonus_mult
                        new_losses  += 1 + loss_bonus
                        bonus_earned = -loss_bonus if loss_bonus > 0 else 0

                else:
                    # No protection
                    if 'resilience' in owned and streak > 0 and random.random() < resilience_chance:
                        resilience_triggered = True
                        new_streak = max(0, streak - 1)
                    else:
                        new_streak = streak - 1 if streak <= 0 else -1
                    loss_count   = abs(new_streak) if new_streak < 0 else 0
                    loss_bonus   = streak_bonus(loss_count) * bonus_mult
                    new_losses  += 1 + loss_bonus
                    bonus_earned = -loss_bonus if loss_bonus > 0 else 0

            else:  # outcome == 'win'
                new_streak = streak + 1 if streak >= 0 else 1
                if regen_recharge_wins > 0:
                    regen_recharge_wins -= 1

                count      = abs(new_streak)
                raw_bonus  = streak_bonus(count)
                base_bonus = raw_bonus * bonus_mult
                # Fortune charm: +25% to all streak bonuses
                if 'fortune_charm' in owned and base_bonus > 0 and random.random() < 0.25:
                    base_bonus = int(base_bonus * 1.25)
                    fortune_charm_triggered = True
                bonus_earned = base_bonus

                # Jackpot echo: trigger from previous spin's echo flag
                if jackpot_echo_pending:
                    jackpot_echo_triggered = True
                    jackpot_hit = True
                    new_wins += (win_mult + bonus_earned) * 25
                    bonus_earned = (win_mult + bonus_earned) * 25 - win_mult
                # Jackpot: 1% chance to multiply wins by 25
                elif 'jackpot' in owned and random.random() < 0.01:
                    jackpot_hit = True
                    new_wins += (win_mult + bonus_earned) * 25
                    bonus_earned = (win_mult + bonus_earned) * 25 - win_mult
                    # Jackpot Echo: 5% chance to trigger jackpot again next spin
                    if random.random() < 0.05:
                        new_jackpot_echo_next = True
                else:
                    # Win echo: 20% chance to double wins earned
                    if 'win_echo' in owned and random.random() < 0.20:
                        echo_triggered = True
                        new_wins += (win_mult + bonus_earned) * 2
                        bonus_earned = win_mult + bonus_earned  # extra portion shown as bonus
                    else:
                        new_wins += win_mult + bonus_earned

            # Update best streak
            new_best_streak = max(best_streak, new_streak) if new_streak > 0 else best_streak

            # Cap wins to prevent JS Infinity display (Number.MAX_VALUE ~1.8e308)
            _MAX_WINS = round(9.99e99)
            new_wins = min(new_wins, _MAX_WINS)

            # Stats tracking
            new_win_count  = gs['win_count']  + (1 if outcome == 'win'  else 0)
            new_loss_count = gs['loss_count'] + (1 if outcome == 'lose' else 0)

            # Wheel rotation angle
            extra_spins = random.randint(5, 8) * 360
            if outcome == 'win':
                segment_angle = random.uniform(200, 340)
            else:
                segment_angle = random.uniform(20, 160)
            total_rotation = extra_spins + segment_angle

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET wins = %s, losses = %s, streak = %s, best_streak = %s,
                           shield_charges = %s, regen_recharge_wins = %s,
                           owned_items = %s, spin_count = %s, win_count = %s, loss_count = %s,
                           fish_clicks = %s, active_cosmetics = %s,
                           dice_charges = %s, dice_last_recharge = %s,
                           jackpot_echo_next = %s,
                           dice_rolled_since_spin = FALSE
                       WHERE user_id = %s''',
                    (new_wins, new_losses, new_streak, new_best_streak,
                     shield_charges, regen_recharge_wins,
                     new_owned, new_spin_count, new_win_count, new_loss_count,
                     fish_clicks, active_cosmetics,
                     dice_charges, last_recharge,
                     new_jackpot_echo_next,
                     current_user.id),
                )
            conn.commit()

        return jsonify({
            'result':             outcome,
            'angle':              total_rotation,
            'wins_delta':         new_wins   - original_wins,
            'losses_delta':       new_losses - original_losses,
            'streak':             new_streak,
            'owned_items':        new_owned,
            'shield_charges':     shield_charges,
            'regen_recharge_wins': regen_recharge_wins,
            'shield_used':        shield_used,
            'shield_used_type':   shield_used_type,
            'shield_broke':       shield_broke,
            'guard_triggered':    guard_triggered,
            'guard_blocked':      guard_blocked,
            'bonus_earned':       bonus_earned,
            'echo_triggered':           echo_triggered,
            'jackpot_hit':              jackpot_hit,
            'jackpot_echo_triggered':   jackpot_echo_triggered,
            'jackpot_echo_next':        new_jackpot_echo_next,
            'resilience_triggered':     resilience_triggered,
            'lucky_seven_triggered':    lucky_seven_triggered,
            'fortune_charm_triggered':  fortune_charm_triggered,
            'active_cosmetics':        active_cosmetics,
            'auto_guard_failed':       auto_guard_failed,
            'new_spin_count':          new_spin_count,
            'dice_charges':            dice_charges,
            'dice_last_recharge':      last_recharge.isoformat(),
        })
    except Exception:
        log.exception('SPIN_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Spin failed'}), 500


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
            dice_charges  = gs['dice_charges']
            last_recharge = gs['dice_last_recharge']
            if last_recharge.tzinfo is None:
                last_recharge = last_recharge.replace(tzinfo=timezone.utc)
            max_charges = dice_max_charges(owned)
            elapsed_charges = int((now_utc - last_recharge).total_seconds() // DICE_RECHARGE_SECONDS)
            if elapsed_charges > 0 and dice_charges < max_charges:
                dice_charges  = min(dice_charges + elapsed_charges, max_charges)
                last_recharge = last_recharge + timedelta(seconds=DICE_RECHARGE_SECONDS * elapsed_charges)

            # Season 5: dice requires win streak >= 3 (no loss streak amplification)
            if streak < 3:
                return jsonify({'error': 'Need a win streak of 3 or more to roll'}), 400
            if dice_charges < 1:
                return jsonify({'error': 'No dice charges available'}), 400
            if gs['dice_rolled_since_spin']:
                return jsonify({'error': 'You must spin once before rolling again'}), 400

            die1     = random.randint(1, 6)
            die2     = random.randint(1, 6)
            dice_sum = die1 + die2

            # Snake eyes (1,1): lose half the win streak — cursed roll!
            # Double sixes (6,6): double the win streak — blessed roll!
            cursed  = (die1 == 1 and die2 == 1)
            blessed = (die1 == 6 and die2 == 6)
            if cursed:
                new_streak = max(0, streak // 2)
            elif blessed:
                new_streak = streak * 2
            else:
                new_streak = streak + dice_sum

            new_best      = max(best_streak, new_streak) if new_streak > 0 else best_streak
            new_charges   = dice_charges - 1
            # Reset recharge clock from now when a charge is consumed
            new_last_recharge = now_utc if new_charges < max_charges else last_recharge

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET streak = %s, best_streak = %s,
                           dice_charges = %s, dice_last_recharge = %s,
                           dice_rolled_since_spin = TRUE
                       WHERE user_id = %s''',
                    (new_streak, new_best, new_charges, new_last_recharge, current_user.id),
                )
            conn.commit()

        return jsonify({
            'die1':              die1,
            'die2':              die2,
            'dice_sum':          dice_sum,
            'cursed':            cursed,
            'blessed':           blessed,
            'streak':            new_streak,
            'wins':              wins,
            'dice_charges':      new_charges,
            'dice_last_recharge': last_recharge.isoformat(),
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
                    cur.execute(
                        f'''SELECT wins, losses, fish_clicks, owned_items, shield_charges,
                                   regen_recharge_wins, active_cosmetics,
                                   winmult_inf_level, bonusmult_inf_level, clickmult_inf_level,
                                   streak_armor_level
                            FROM game_state WHERE user_id = %s FOR UPDATE''',
                        (current_user.id,),
                    )
                    gs = cur.fetchone()

                owned     = list(gs['owned_items'])
                cur_level = gs[col]

                # streak_armor_inf: requires resilience, hard cap at max_level
                if item_id == 'streak_armor_inf':
                    if 'resilience' not in owned:
                        return jsonify({'error': 'Requires Resilience'}), 400
                    max_level = inf.get('max_level', 999)
                    if cur_level >= max_level:
                        return jsonify({'error': 'Maximum level reached'}), 400

                cost      = inf_upgrade_cost(item_id, cur_level)

                if int(gs['wins']) < cost:
                    return jsonify({'error': 'Insufficient wins'}), 402

                new_wins  = int(gs['wins']) - cost
                new_level = cur_level + 1

                with conn.cursor() as cur:
                    cur.execute(
                        f'UPDATE game_state SET wins = %s, {col} = %s WHERE user_id = %s',
                        (new_wins, new_level, current_user.id),
                    )
                conn.commit()

            return jsonify({
                'wins':                new_wins,
                'losses':              gs['losses'],
                'fish_clicks':         gs['fish_clicks'],
                'owned_items':         owned,
                'shield_charges':      gs['shield_charges'],
                'regen_recharge_wins': gs['regen_recharge_wins'],
                'active_cosmetics':    list(gs['active_cosmetics']),
                'winmult_inf_level':    new_level if col == 'winmult_inf_level'    else gs['winmult_inf_level'],
                'bonusmult_inf_level':  new_level if col == 'bonusmult_inf_level'  else gs['bonusmult_inf_level'],
                'clickmult_inf_level':  new_level if col == 'clickmult_inf_level'  else gs['clickmult_inf_level'],
                'streak_armor_level':   new_level if col == 'streak_armor_level'   else gs['streak_armor_level'],
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
                cur.execute(
                    '''SELECT wins, losses, fish_clicks, owned_items, shield_charges,
                              regen_recharge_wins, active_cosmetics,
                              winmult_inf_level, bonusmult_inf_level, clickmult_inf_level,
                              streak_armor_level, win_count
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned = list(gs['owned_items'])

            if item_id in owned:
                return jsonify({'error': 'Already owned'}), 409
            if requires and requires not in owned:
                return jsonify({'error': 'Prerequisite not met'}), 400

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

            new_owned = owned + [item_id]

            if item_id == 'regen_shield':
                new_charges        = gs['shield_charges']
                new_regen_recharge = 0
            else:
                new_charges        = gs['shield_charges']
                new_regen_recharge = gs['regen_recharge_wins']

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
                           owned_items = %s, shield_charges = %s,
                           regen_recharge_wins = %s, active_cosmetics = %s
                       WHERE user_id = %s''',
                    (new_wins, new_losses, new_clicks, new_owned,
                     new_charges, new_regen_recharge, new_active_cosmetics, current_user.id),
                )
            conn.commit()

        return jsonify({
            'wins':                new_wins,
            'losses':              new_losses,
            'fish_clicks':         new_clicks,
            'owned_items':         new_owned,
            'shield_charges':      new_charges,
            'regen_recharge_wins': new_regen_recharge,
            'active_cosmetics':    new_active_cosmetics,
            'winmult_inf_level':   gs['winmult_inf_level'],
            'bonusmult_inf_level': gs['bonusmult_inf_level'],
            'clickmult_inf_level': gs['clickmult_inf_level'],
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
                cur.execute('SELECT COALESCE(SUM(fish_clicks), 0) AS total FROM game_state')
                pending_row = cur.fetchone()
            total_pending_clicks = int(pending_row['total']) if pending_row else 0
            if not pot:
                return jsonify({'total_contributed': 0, 'target': 1_000, 'filled': False, 'active': False, 'win_chance_pct': 50.0, 'total_pending_clicks': total_pending_clicks})
            now_utc = dt.datetime.now(timezone.utc)
            pot_active = bool(
                pot['filled'] and pot['filled_at'] and
                pot['filled_at'] > now_utc - dt.timedelta(minutes=30)
            )
            # Lazy reset: if window expired, advance target and clear filled state
            if pot['filled'] and not pot_active:
                new_pot_target = max(int(pot['target'] * 1.5), 1)
                with conn.cursor() as cur2:
                    cur2.execute(
                        '''UPDATE community_pot SET filled = false, filled_at = NULL,
                           total_contributed = 0, target = %s, last_decay_check = NOW()
                           WHERE id = 1''',
                        (new_pot_target,)
                    )
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
                pot_window_active = pot['filled_at'] and pot['filled_at'] > now_utc - dt.timedelta(minutes=30)
                if pot_window_active:
                    return jsonify({'error': 'Pot is active — wait for the boost to expire'}), 400
                # Window expired: advance to next target (×1.5), reset contributions
                new_exp_target = max(int(pot['target'] * 1.5), 1)
                with conn.cursor() as cur2:
                    cur2.execute(
                        '''UPDATE community_pot SET filled = false, filled_at = NULL,
                           total_contributed = 0, target = %s, last_decay_check = NOW()
                           WHERE id = 1''',
                        (new_exp_target,)
                    )
                pot = dict(pot)
                pot['filled'] = False
                pot['total_contributed'] = 0
                pot['target'] = new_exp_target

            # Apply decay if 12+ hours since last check
            last_decay = pot['last_decay_check']
            if last_decay.tzinfo is None:
                last_decay = last_decay.replace(tzinfo=timezone.utc)
            decay_periods = int((now_utc - last_decay).total_seconds() / (12 * 3600))
            effective_target = int(pot['target'])
            if decay_periods > 0:
                for _ in range(decay_periods):
                    effective_target = max(500, int(effective_target * 0.8))
                if pot['total_contributed'] > 0:
                    effective_target = max(effective_target, int(pot['total_contributed']) + 1)
                new_decay_ts = last_decay + timedelta(hours=12 * decay_periods)
                with conn.cursor() as cur2:
                    cur2.execute(
                        'UPDATE community_pot SET target = %s, last_decay_check = %s WHERE id = 1',
                        (effective_target, new_decay_ts)
                    )

            fish_clicks = gs['fish_clicks']
            if amount_type == '10pct':
                contribute = min(max(1, effective_target // 10), fish_clicks)
            else:
                contribute = fish_clicks

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


@game_bp.route('/api/fish-click', methods=['POST'])
@login_required
@limiter.limit('5 per second')
def fish_click():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    try:
        count = max(1, min(10, int(data.get('count', 1))))
    except (TypeError, ValueError):
        count = 1

    # Budget: 75 raw clicks per 5-second rolling window.
    # The CTE atomically computes how many of the requested clicks fit within
    # the budget and credits only that many (possibly 0).  FOR UPDATE serialises
    # concurrent workers so no two requests race on the same row.
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''WITH budget AS (
                           SELECT user_id,
                                  (NOW() - click_window_start >= INTERVAL '5 seconds') AS window_expired,
                                  clickmult_inf_level,
                                  CASE
                                      WHEN NOW() - click_window_start >= INTERVAL '5 seconds'
                                      THEN LEAST(%(count)s, 75)
                                      ELSE GREATEST(0, LEAST(%(count)s, 75 - click_window_count))
                                  END AS allowed
                           FROM game_state WHERE user_id = %(uid)s
                           FOR UPDATE
                       )
                       UPDATE game_state gs SET
                           click_window_start = CASE WHEN b.window_expired THEN NOW()
                                                     ELSE gs.click_window_start END,
                           click_window_count = CASE WHEN b.window_expired THEN b.allowed
                                                     ELSE gs.click_window_count + b.allowed END,
                           fish_clicks        = gs.fish_clicks
                                                + b.allowed * (b.clickmult_inf_level + 1),
                           total_fish_clicks  = gs.total_fish_clicks
                                                + b.allowed * (b.clickmult_inf_level + 1)
                       FROM budget b WHERE gs.user_id = b.user_id
                       RETURNING gs.fish_clicks''',
                    {'count': count, 'uid': current_user.id},
                )
                row = cur.fetchone()
            conn.commit()
        return jsonify({'fish_clicks': row[0]})
    except Exception:
        log.exception('FISH_CLICK_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Click failed'}), 500


@game_bp.route('/api/click-frenzy', methods=['POST'])
@login_required
@limiter.limit('1 per second')
def click_frenzy():
    err = require_json()
    if err:
        return err

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT fish_clicks, total_fish_clicks, owned_items, active_cosmetics,
                              clickmult_inf_level, frenzy_last_tick
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned            = list(gs['owned_items'])
            active_cosmetics = list(gs['active_cosmetics'])

            if 'final_frenzy' in active_cosmetics:
                amount = 500
            elif 'clickfrenzy_5' in owned:
                amount = 100
            elif 'clickfrenzy_4' in owned:
                amount = 50
            elif 'clickfrenzy_3' in owned:
                amount = 20
            elif 'clickfrenzy_2' in owned:
                amount = 5
            elif 'clickfrenzy_1' in owned:
                amount = 1
            else:
                return jsonify({'error': 'No frenzy upgrade owned'}), 403

            # Cooldown: must be ≥4 seconds since last frenzy tick
            last_tick = gs['frenzy_last_tick']
            now_utc   = dt.datetime.now(timezone.utc)
            if last_tick.tzinfo is None:
                last_tick = last_tick.replace(tzinfo=timezone.utc)
            if (now_utc - last_tick).total_seconds() < 2:
                return jsonify({'fish_clicks': gs['fish_clicks']})

            # Apply click multiplier to passive clicks
            amount *= click_mult_from_level(gs['clickmult_inf_level'])

            new_clicks = gs['fish_clicks'] + amount
            new_total  = gs['total_fish_clicks'] + amount

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET fish_clicks = %s, total_fish_clicks = %s, frenzy_last_tick = NOW()
                       WHERE user_id = %s''',
                    (new_clicks, new_total, current_user.id),
                )
            conn.commit()

        return jsonify({'fish_clicks': new_clicks})
    except Exception:
        log.exception('CLICK_FRENZY_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Frenzy tick failed'}), 500


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
                    'SELECT spin_count, win_count, loss_count, fish_clicks, total_fish_clicks FROM game_state WHERE user_id = %s',
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
            'spin_count':        row['spin_count'],
            'win_count':         row['win_count'],
            'loss_count':        row['loss_count'],
            'fish_clicks':       row['fish_clicks'],
            'total_fish_clicks': row['total_fish_clicks'],
            'season_history':    season_history,
        })
    except Exception:
        log.exception('STATS_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Failed to load stats'}), 500


@game_bp.route('/api/leaderboard')
def leaderboard():
    try:
        with db_connection() as conn:
            ensure_current_season(conn)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT u.username, gs.wins, gs.losses, gs.streak, gs.best_streak
                       FROM game_state gs
                       JOIN users u ON u.id = gs.user_id
                       WHERE gs.wins > 0
                       ORDER BY gs.wins DESC
                       LIMIT 10'''
                )
                rows = cur.fetchall()
        return jsonify([
            {
                'username':    r['username'],
                'wins':        int(r['wins']),
                'losses':      r['losses'],
                'streak':      r['streak'],
                'best_streak': r['best_streak'],
            }
            for r in rows
        ])
    except Exception:
        log.exception('LEADERBOARD_ERROR')
        return jsonify([])


@game_bp.route('/api/season')
def get_season():
    """Public endpoint for season info. Used by cron safety net and frontend polling."""
    try:
        with db_connection() as conn:
            ensure_current_season(conn)
            info = get_season_info(conn)
        return jsonify(info)
    except Exception:
        log.exception('GET_SEASON_ERROR')
        return jsonify({'error': 'Failed to load season'}), 500
