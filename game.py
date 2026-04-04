import datetime as dt
import logging
import random
import secrets
from datetime import timezone

import psycopg2.extras
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import db_connection
from extensions import limiter
from models import (ALL_ITEMS, INFINITE_UPGRADES, REGEN_SHIELD_RECHARGE_WINS, VALID_FISH_IDS,
                    ITEM_CURRENCY, INFINITE_UPGRADE_CURRENCY,
                    inf_upgrade_cost, win_mult_from_level, bonus_mult_from_level, click_mult_from_level)
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
    'page_season1': 'page_theme', 'page_season2': 'page_theme', 'page_season3': 'page_theme',
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
                              low_spec_mode
                       FROM game_state WHERE user_id = %s''',
                    (current_user.id,),
                )
                gs = cur.fetchone()
                cur.execute('SELECT total_contributed, target, fib_prev, win_chance_pct, filled, filled_at FROM community_pot WHERE id = 1')
                pot = cur.fetchone()
        pot_active = bool(
            pot and pot['filled'] and pot['filled_at'] and
            pot['filled_at'] > dt.datetime.now(timezone.utc) - dt.timedelta(hours=1)
        )
        return jsonify({
            'wins':               int(gs['wins']),
            'losses':             gs['losses'],
            'fish_clicks':        gs['fish_clicks'],
            'streak':             gs['streak'],
            'owned_items':        list(gs['owned_items']),
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
            'low_spec_mode':       gs['low_spec_mode'],
            'community_pot': {
                'total_contributed': pot['total_contributed'] if pot else 0,
                'target':            pot['target']            if pot else 10_000,
                'filled':            pot['filled']            if pot else False,
                'active':            pot_active,
                'win_chance_pct':    pot['win_chance_pct']    if pot else 51,
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
                              winmult_inf_level, bonusmult_inf_level,
                              fish_clicks, active_cosmetics
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

                # Community pot: check if bonus is active (within 1 hour of filling)
                cur.execute('SELECT filled, filled_at, win_chance_pct FROM community_pot WHERE id = 1')
                pot_row = cur.fetchone()

            owned               = list(gs['owned_items'])
            streak              = gs['streak']
            best_streak         = gs['best_streak']
            shield_charges      = gs['shield_charges']
            regen_recharge_wins = gs['regen_recharge_wins']
            fish_clicks         = gs['fish_clicks']
            active_cosmetics    = list(gs['active_cosmetics'])

            pot_active = False
            if pot_row and pot_row['filled'] and pot_row['filled_at']:
                pot_active = pot_row['filled_at'] > dt.datetime.now(timezone.utc) - dt.timedelta(hours=1)
            # Auto-reset expired pot: advance to next Fibonacci target, increment win chance
            if pot_row and pot_row['filled'] and not pot_active:
                with conn.cursor() as cur2:
                    cur2.execute(
                        '''UPDATE community_pot
                           SET filled = false, filled_at = NULL,
                               fib_prev = target,
                               target = target + fib_prev,
                               win_chance_pct = LEAST(win_chance_pct + 1, 75)
                           WHERE id = 1'''
                    )

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
            if 'singularity' in owned:
                outcome = 'win'
            elif 'lucky_seven' in owned and new_spin_count % 7 == 0:
                outcome = 'win'
                lucky_seven_triggered = True
            elif pot_active:
                outcome = 'win' if secrets.randbelow(100) < pot_row['win_chance_pct'] else 'lose'
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
            echo_triggered        = False
            jackpot_hit           = False
            resilience_triggered  = False
            lucky_seven_triggered = False
            fortune_charm_triggered = False

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
                        if 'resilience' in owned and streak > 0 and random.random() < 0.50:
                            resilience_triggered = True
                            new_streak = max(0, streak - 1)
                        else:
                            new_streak = streak - 1 if streak <= 0 else -1
                        loss_count   = abs(new_streak) if new_streak < 0 else 0
                        raw_lb       = (1 << (loss_count - 3)) if loss_count >= 3 else 0
                        loss_bonus   = raw_lb * bonus_mult
                        new_losses  += 1 + loss_bonus
                        bonus_earned = -loss_bonus if loss_bonus > 0 else 0

                else:
                    # No protection
                    if 'resilience' in owned and streak > 0 and random.random() < 0.50:
                        resilience_triggered = True
                        new_streak = max(0, streak - 1)
                    else:
                        new_streak = streak - 1 if streak <= 0 else -1
                    loss_count   = abs(new_streak) if new_streak < 0 else 0
                    raw_lb       = (1 << (loss_count - 3)) if loss_count >= 3 else 0
                    loss_bonus   = raw_lb * bonus_mult
                    new_losses  += 1 + loss_bonus
                    bonus_earned = -loss_bonus if loss_bonus > 0 else 0

            else:  # outcome == 'win'
                new_streak = streak + 1 if streak >= 0 else 1
                if regen_recharge_wins > 0:
                    regen_recharge_wins -= 1

                count     = abs(new_streak)
                raw_bonus = (1 << (count - 3)) if count >= 3 else 0
                base_bonus = raw_bonus * bonus_mult
                # Fortune charm: +25% to all streak bonuses
                if 'fortune_charm' in owned and base_bonus > 0 and random.random() < 0.25:
                    base_bonus = int(base_bonus * 1.25)
                    fortune_charm_triggered = True
                bonus_earned = base_bonus

                # Jackpot: 2% chance to multiply wins by 50
                if 'jackpot' in owned and random.random() < 0.01:
                    jackpot_hit = True
                    new_wins += (win_mult + bonus_earned) * 50
                    bonus_earned = (win_mult + bonus_earned) * 50 - win_mult  # show inflated bonus
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
                           fish_clicks = %s, active_cosmetics = %s
                       WHERE user_id = %s''',
                    (new_wins, new_losses, new_streak, new_best_streak,
                     shield_charges, regen_recharge_wins,
                     new_owned, new_spin_count, new_win_count, new_loss_count,
                     fish_clicks, active_cosmetics, current_user.id),
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
            'echo_triggered':          echo_triggered,
            'jackpot_hit':             jackpot_hit,
            'resilience_triggered':    resilience_triggered,
            'lucky_seven_triggered':   lucky_seven_triggered,
            'fortune_charm_triggered': fortune_charm_triggered,
            'active_cosmetics':       active_cosmetics,
            'auto_guard_failed':      auto_guard_failed,
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
                    'SELECT wins, losses, streak, best_streak FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            wins        = int(gs['wins'])
            losses      = int(gs['losses'])
            streak      = gs['streak']
            best_streak = gs['best_streak']
            cost        = losses

            if losses < 1:
                return jsonify({'error': 'Not enough losses to roll'}), 400
            if streak == 0:
                return jsonify({'error': 'No active streak to amplify'}), 400

            die1     = random.randint(1, 6)
            die2     = random.randint(1, 6)
            dice_sum = die1 + die2

            # Amplify whichever streak the player is currently on
            if streak > 0:
                new_streak = streak + dice_sum
            else:
                new_streak = streak - dice_sum

            new_best    = max(best_streak, new_streak) if new_streak > 0 else best_streak
            new_losses  = 0

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET losses = %s, streak = %s, best_streak = %s
                       WHERE user_id = %s''',
                    (new_losses, new_streak, new_best, current_user.id),
                )
            conn.commit()

        return jsonify({
            'die1':     die1,
            'die2':     die2,
            'dice_sum': dice_sum,
            'cost':     cost,
            'losses':   new_losses,
            'wins':     wins,
            'streak':   new_streak,
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
                                   winmult_inf_level, bonusmult_inf_level, clickmult_inf_level
                            FROM game_state WHERE user_id = %s FOR UPDATE''',
                        (current_user.id,),
                    )
                    gs = cur.fetchone()

                owned     = list(gs['owned_items'])
                cur_level = gs[col]
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
                'winmult_inf_level':   new_level if col == 'winmult_inf_level'   else gs['winmult_inf_level'],
                'bonusmult_inf_level': new_level if col == 'bonusmult_inf_level' else gs['bonusmult_inf_level'],
                'clickmult_inf_level': new_level if col == 'clickmult_inf_level' else gs['clickmult_inf_level'],
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
                              winmult_inf_level, bonusmult_inf_level, clickmult_inf_level
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned = list(gs['owned_items'])

            if item_id in owned:
                return jsonify({'error': 'Already owned'}), 409
            if requires and requires not in owned:
                return jsonify({'error': 'Prerequisite not met'}), 400

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
                    return jsonify({'error': 'Insufficient fish clicks'}), 402
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
                cur.execute('SELECT total_contributed, target, fib_prev, win_chance_pct, filled, filled_at FROM community_pot WHERE id = 1')
                pot = cur.fetchone()
        if not pot:
            return jsonify({'total_contributed': 0, 'target': 10_000, 'filled': False, 'active': False, 'win_chance_pct': 51})
        pot_active = bool(
            pot['filled'] and pot['filled_at'] and
            pot['filled_at'] > dt.datetime.now(timezone.utc) - dt.timedelta(hours=1)
        )
        return jsonify({
            'total_contributed': pot['total_contributed'],
            'target':            pot['target'],
            'filled':            pot['filled'],
            'active':            pot_active,
            'filled_at':         pot['filled_at'].isoformat() if pot['filled_at'] else None,
            'win_chance_pct':    pot['win_chance_pct'],
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
    amount_type = data.get('amount', 'all')  # '10000' or 'all'

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT fish_clicks FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()
                cur.execute('SELECT total_contributed, target, fib_prev, win_chance_pct, filled, filled_at FROM community_pot WHERE id = 1 FOR UPDATE')
                pot = cur.fetchone()

            if not pot:
                return jsonify({'error': 'Pot not found'}), 500
            if pot['filled']:
                pot_expired = not (pot['filled_at'] and
                    pot['filled_at'] > dt.datetime.now(timezone.utc) - dt.timedelta(hours=1))
                if not pot_expired:
                    return jsonify({'error': 'Pot is active — wait for the boost to expire'}), 400
                # Expired: reset here so contributions can continue
                with conn.cursor() as cur2:
                    cur2.execute(
                        '''UPDATE community_pot SET filled = false, filled_at = NULL,
                           fib_prev = target, target = target + fib_prev,
                           win_chance_pct = LEAST(win_chance_pct + 1, 75)
                           WHERE id = 1'''
                    )
                old_target = pot['target']
                old_fib_prev = pot['fib_prev']
                pot = dict(pot)
                pot['filled'] = False
                pot['target'] = old_target + old_fib_prev
                pot['fib_prev'] = old_target
                pot['win_chance_pct'] = min(pot['win_chance_pct'] + 1, 75)

            fish_clicks = gs['fish_clicks']
            if amount_type == '10pct':
                contribute = min(max(1, pot['target'] // 10), fish_clicks)
            else:
                contribute = fish_clicks

            if contribute <= 0:
                return jsonify({'error': 'No fish clicks to contribute'}), 400

            # Cap at remaining target
            remaining  = pot['target'] - pot['total_contributed']
            contribute = min(contribute, remaining)
            new_total  = pot['total_contributed'] + contribute
            newly_filled = new_total >= pot['target']

            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET fish_clicks = fish_clicks - %s WHERE user_id = %s',
                    (contribute, current_user.id),
                )
                if newly_filled:
                    cur.execute(
                        '''UPDATE community_pot SET total_contributed = %s, filled = true,
                           filled_at = now() WHERE id = 1''',
                        (new_total,),
                    )
                else:
                    cur.execute(
                        'UPDATE community_pot SET total_contributed = %s WHERE id = 1',
                        (new_total,),
                    )
            conn.commit()

        filled_at_iso = dt.datetime.now(timezone.utc).isoformat() if newly_filled else None
        return jsonify({
            'fish_clicks':   fish_clicks - contribute,
            'contributed':   contribute,
            'pot_total':     new_total,
            'pot_target':      pot['target'],
            'pot_filled':      newly_filled,
            'pot_active':      newly_filled,
            'filled_at':       filled_at_iso,
            'win_chance_pct':  pot['win_chance_pct'],
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
