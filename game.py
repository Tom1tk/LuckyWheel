import logging
import random
import secrets

import psycopg2.extras
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import db_connection
from extensions import limiter
from models import ALL_ITEMS, REGEN_SHIELD_RECHARGE_WINS, VALID_FISH_IDS

COSMETIC_SLOTS = {
    'bg_ocean':   'bg', 'bg_royal':   'bg', 'bg_inferno': 'bg',
    'fishsize_1': 'size', 'fishsize_2': 'size', 'fishsize_3': 'size',
    'confetti_1': 'confetti', 'confetti_2': 'confetti', 'confetti_3': 'confetti',
    'party_mode': 'party',
    'trail_1': 'trail', 'trail_2': 'trail', 'trail_3': 'trail',
    'theme_fire': 'wheel', 'theme_ice': 'wheel', 'theme_neon': 'wheel',
    'golden_wheel': 'golden',
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
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT wins, losses, fish_clicks, streak, owned_items,
                              equipped_fish, shield_charges, regen_recharge_wins,
                              active_cosmetics, spin_count, win_count
                       FROM game_state WHERE user_id = %s''',
                    (current_user.id,),
                )
                gs = cur.fetchone()
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
        })
    except Exception:
        log.exception('GET_STATE_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Failed to load state'}), 500


@game_bp.route('/api/spin', methods=['POST'])
@login_required
@limiter.limit('10 per second')
def spin():
    err = require_json()
    if err:
        return err

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT wins, losses, streak, owned_items, shield_charges, regen_recharge_wins,
                              spin_count, win_count
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned               = list(gs['owned_items'])
            streak              = gs['streak']
            shield_charges      = gs['shield_charges']
            regen_recharge_wins = gs['regen_recharge_wins']

            # Determine outcome
            if 'singularity' in owned:
                outcome = 'win'
            else:
                outcome = secrets.choice(['win', 'lose'])

            # Multipliers
            win_mult = (16 if 'winmult_4' in owned else
                        8  if 'winmult_3' in owned else
                        4  if 'winmult_2' in owned else
                        2  if 'winmult_1' in owned else 1)
            bonus_mult = (10 if 'bonusmult_3' in owned else
                          5  if 'bonusmult_2' in owned else
                          2  if 'bonusmult_1' in owned else 1)

            shield_used      = False
            shield_broke     = False
            shield_used_type = None
            new_wins         = int(gs['wins'])
            new_losses       = gs['losses']
            bonus_earned     = 0
            new_owned        = owned

            # Shields only activate when a win streak is about to be broken
            if outcome == 'lose' and streak > 0:
                if 'shield_1' in owned:
                    shield_used      = True
                    shield_used_type = 'shield_1'
                    shield_broke     = True
                    new_owned        = [x for x in owned if x != 'shield_1']
                    new_streak       = streak

                elif 'iron_shield' in owned and shield_charges > 0:
                    shield_used      = True
                    shield_used_type = 'iron_shield'
                    shield_charges  -= 1
                    if shield_charges <= 0:
                        shield_charges = 0
                        new_owned    = [x for x in owned if x != 'iron_shield']
                        shield_broke = True
                    new_streak = streak

                elif 'regen_shield' in owned and regen_recharge_wins == 0:
                    shield_used         = True
                    shield_used_type    = 'regen_shield'
                    regen_recharge_wins = REGEN_SHIELD_RECHARGE_WINS
                    new_streak          = streak

                else:
                    new_streak   = -1
                    bonus_earned = 0
                    new_losses  += 1

            else:
                if outcome == 'win':
                    new_streak = streak + 1 if streak >= 0 else 1
                    if regen_recharge_wins > 0:
                        regen_recharge_wins -= 1
                else:
                    new_streak = streak - 1 if streak <= 0 else -1

                if outcome == 'win':
                    count        = abs(new_streak)
                    # Integer bitshift avoids float precision loss.
                    # wins is NUMERIC (arbitrary precision) — no overflow cap needed.
                    raw_bonus    = (1 << (count - 3)) if count >= 3 else 0
                    bonus_earned = raw_bonus * bonus_mult
                    new_wins    += win_mult + bonus_earned
                else:
                    bonus_earned = 0
                    new_losses  += 1

            # Stats tracking
            new_spin_count = gs['spin_count'] + 1
            new_win_count  = gs['win_count'] + (1 if outcome == 'win' else 0)

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
                       SET wins = %s, losses = %s, streak = %s,
                           shield_charges = %s, regen_recharge_wins = %s,
                           owned_items = %s, spin_count = %s, win_count = %s
                       WHERE user_id = %s''',
                    (new_wins, new_losses, new_streak,
                     shield_charges, regen_recharge_wins,
                     new_owned, new_spin_count, new_win_count, current_user.id),
                )
            conn.commit()

        return jsonify({
            'result':             outcome,
            'angle':              total_rotation,
            'wins':               new_wins,
            'losses':             new_losses,
            'streak':             new_streak,
            'owned_items':        new_owned,
            'shield_charges':     shield_charges,
            'regen_recharge_wins': regen_recharge_wins,
            'shield_used':        shield_used,
            'shield_used_type':   shield_used_type,
            'shield_broke':       shield_broke,
            'bonus_earned':       bonus_earned,
        })
    except Exception:
        log.exception('SPIN_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Spin failed'}), 500


@game_bp.route('/api/buy', methods=['POST'])
@login_required
def buy():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id') or ''

    if item_id not in ALL_ITEMS:
        return jsonify({'error': 'Unknown item'}), 400

    item     = ALL_ITEMS[item_id]
    cost     = item['cost']
    requires = item.get('requires')

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT fish_clicks, owned_items, shield_charges, regen_recharge_wins, active_cosmetics
                       FROM game_state WHERE user_id = %s FOR UPDATE''',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned       = list(gs['owned_items'])
            fish_clicks = gs['fish_clicks']

            if item_id in owned:
                return jsonify({'error': 'Already owned'}), 409
            if requires and requires not in owned:
                return jsonify({'error': 'Prerequisite not met'}), 400
            if fish_clicks < cost:
                return jsonify({'error': 'Insufficient fish clicks'}), 402

            new_clicks = fish_clicks - cost
            new_owned  = owned + [item_id]

            if item_id == 'iron_shield':
                new_charges       = 3
                new_regen_recharge = gs['regen_recharge_wins']
            elif item_id == 'regen_shield':
                new_charges       = gs['shield_charges']
                new_regen_recharge = 0
            else:
                new_charges       = gs['shield_charges']
                new_regen_recharge = gs['regen_recharge_wins']

            # Auto-activate cosmetic items when purchased
            new_active_cosmetics = list(gs['active_cosmetics'])
            if item_id in COSMETIC_SLOTS:
                slot = COSMETIC_SLOTS[item_id]
                # Remove all items in the same slot
                new_active_cosmetics = [c for c in new_active_cosmetics if COSMETIC_SLOTS.get(c) != slot]
                new_active_cosmetics.append(item_id)

            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET fish_clicks = %s, owned_items = %s,
                           shield_charges = %s, regen_recharge_wins = %s,
                           active_cosmetics = %s
                       WHERE user_id = %s''',
                    (new_clicks, new_owned, new_charges, new_regen_recharge,
                     new_active_cosmetics, current_user.id),
                )
            conn.commit()

        return jsonify({
            'fish_clicks':        new_clicks,
            'owned_items':        new_owned,
            'shield_charges':     new_charges,
            'regen_recharge_wins': new_regen_recharge,
            'active_cosmetics':   new_active_cosmetics,
        })
    except Exception:
        log.exception('BUY_ERROR  user_id=%s  item_id=%s', current_user.id, item_id)
        return jsonify({'error': 'Purchase failed'}), 500


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
@limiter.limit('10 per second')
def fish_click():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    try:
        count = max(1, min(30, int(data.get('count', 1))))
    except (TypeError, ValueError):
        count = 1

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE game_state
                       SET fish_clicks = fish_clicks +
                           CASE
                               WHEN 'double_click_5' = ANY(owned_items) THEN 6 * %s
                               WHEN 'double_click_4' = ANY(owned_items) THEN 5 * %s
                               WHEN 'double_click_3' = ANY(owned_items) THEN 4 * %s
                               WHEN 'double_click_2' = ANY(owned_items) THEN 3 * %s
                               WHEN 'double_click' = ANY(owned_items) THEN 2 * %s
                               ELSE %s
                           END
                       WHERE user_id = %s
                       RETURNING fish_clicks''',
                    (count, count, count, count, count, count, current_user.id),
                )
                row = cur.fetchone()
            conn.commit()
        return jsonify({'fish_clicks': row[0]})
    except Exception:
        log.exception('FISH_CLICK_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Click failed'}), 500


@game_bp.route('/api/click-frenzy', methods=['POST'])
@login_required
def click_frenzy():
    err = require_json()
    if err:
        return err

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT fish_clicks, owned_items FROM game_state WHERE user_id = %s FOR UPDATE',
                    (current_user.id,),
                )
                gs = cur.fetchone()

            owned = list(gs['owned_items'])

            if 'clickfrenzy_5' in owned:
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

            new_clicks = gs['fish_clicks'] + amount

            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE game_state SET fish_clicks = %s WHERE user_id = %s',
                    (new_clicks, current_user.id),
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
                    'SELECT spin_count, win_count, losses, fish_clicks FROM game_state WHERE user_id = %s',
                    (current_user.id,)
                )
                row = cur.fetchone()
        return jsonify({
            'spin_count':  row['spin_count'],
            'win_count':   row['win_count'],
            'loss_count':  row['losses'],
            'fish_clicks': row['fish_clicks'],
        })
    except Exception:
        log.exception('STATS_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Failed to load stats'}), 500


@game_bp.route('/api/leaderboard')
def leaderboard():
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT u.username, gs.wins, gs.losses
                       FROM game_state gs
                       JOIN users u ON u.id = gs.user_id
                       ORDER BY gs.wins DESC
                       LIMIT 5'''
                )
                rows = cur.fetchall()
        return jsonify([
            {'username': r['username'], 'wins': int(r['wins']), 'losses': r['losses']}
            for r in rows
        ])
    except Exception:
        log.exception('LEADERBOARD_ERROR')
        return jsonify([])
