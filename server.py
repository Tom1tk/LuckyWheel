import os
import random
import math
from datetime import timedelta, datetime, timezone

import bcrypt
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, send_from_directory, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user,
)

# ── App setup ────────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('WHEEL_SECRET_KEY', '8eb08ecc787cc80664bbe71cbf6799a7f00b2247e2e027aa4646a60c923e71be')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)

# ── DB config ────────────────────────────────────────────────────────────────

DB_DSN = os.environ.get(
    'DATABASE_URL',
    'postgresql://wheelapp:a51f2d9685f4d6dca9d2f9d8d6e66374@localhost/wheeldb'
)


def get_db():
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    return conn


# ── Rate limiter ─────────────────────────────────────────────────────────────

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=['200 per minute'],
    storage_uri='memory://',
)

# ── Flask-Login ───────────────────────────────────────────────────────────────

login_manager = LoginManager(app)


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))
            row = cur.fetchone()
        conn.close()
        if row:
            return User(row['id'], row['username'])
    except Exception:
        pass
    return None


# ── Shop catalogue (server-side mirror for validation) ────────────────────────

FISH_SKINS = {
    'fish_tropical': {'cost': 25},
    'fish_puffer':   {'cost': 50},
    'fish_octopus':  {'cost': 75},
    'fish_shark':    {'cost': 100},
    'fish_dolphin':  {'cost': 150},
}

SHOP_ITEMS = {
    'speed_boost':    {'cost': 50,     'requires': None},
    'turbo_spin':     {'cost': 200,    'requires': 'speed_boost'},
    'autospeed_1':    {'cost': 75,     'requires': None},
    'autospeed_2':    {'cost': 300,    'requires': 'autospeed_1'},
    'autospeed_3':    {'cost': 1200,   'requires': 'autospeed_2'},
    'winmult_1':      {'cost': 200,    'requires': None},
    'winmult_2':      {'cost': 800,    'requires': 'winmult_1'},
    'winmult_3':      {'cost': 3200,   'requires': 'winmult_2'},
    'winmult_4':      {'cost': 12800,  'requires': 'winmult_3'},
    'bonusmult_1':    {'cost': 300,    'requires': None},
    'bonusmult_2':    {'cost': 1200,   'requires': 'bonusmult_1'},
    'bonusmult_3':    {'cost': 4800,   'requires': 'bonusmult_2'},
    'fishsize_1':     {'cost': 50,     'requires': None},
    'fishsize_2':     {'cost': 200,    'requires': 'fishsize_1'},
    'fishsize_3':     {'cost': 800,    'requires': 'fishsize_2'},
    'trail_1':        {'cost': 125,    'requires': None},
    'trail_2':        {'cost': 500,    'requires': 'trail_1'},
    'trail_3':        {'cost': 2000,   'requires': 'trail_2'},
    'double_click':   {'cost': 100,    'requires': None},
    'clickfrenzy_1':  {'cost': 150,    'requires': None},
    'clickfrenzy_2':  {'cost': 600,    'requires': 'clickfrenzy_1'},
    'clickfrenzy_3':  {'cost': 2400,   'requires': 'clickfrenzy_2'},
    'shield_1':       {'cost': 150,    'requires': None},
    'iron_shield':    {'cost': 600,    'requires': 'shield_1'},
    'theme_fire':     {'cost': 250,    'requires': None},
    'theme_ice':      {'cost': 1000,   'requires': 'theme_fire'},
    'theme_neon':     {'cost': 4000,   'requires': 'theme_ice'},
    'golden_wheel':   {'cost': 300,    'requires': None},
    'party_mode':     {'cost': 150,    'requires': None},
    'confetti_1':     {'cost': 75,     'requires': None},
    'confetti_2':     {'cost': 300,    'requires': 'confetti_1'},
    'confetti_3':     {'cost': 1200,   'requires': 'confetti_2'},
    'bg_ocean':       {'cost': 100,    'requires': None},
    'bg_royal':       {'cost': 400,    'requires': 'bg_ocean'},
    'bg_inferno':     {'cost': 1600,   'requires': 'bg_royal'},
    'singularity':    {'cost': 1000000000, 'requires': None},
}

ALL_ITEMS = {**FISH_SKINS, **SHOP_ITEMS}

VALID_FISH_IDS = set(FISH_SKINS.keys()) | {'default'}


# ── Brute-force protection ────────────────────────────────────────────────────

LOCKOUT_RULES = [
    (20, 3600),  # 20+ fails → 1 hour
    (10, 300),   # 10+ fails → 5 minutes
    (5,  60),    # 5+ fails  → 1 minute
]


def check_lockout(conn, identifier):
    """Return seconds remaining in lockout (0 = not locked)."""
    with conn.cursor() as cur:
        cur.execute(
            '''SELECT COUNT(*), MAX(attempted_at)
               FROM login_attempts
               WHERE identifier = %s AND success = FALSE
                 AND attempted_at > NOW() - INTERVAL '1 hour' ''',
            (identifier,),
        )
        row = cur.fetchone()
    fail_count = row[0] or 0
    last_fail = row[1]
    if not last_fail or fail_count == 0:
        return 0
    for threshold, lock_secs in LOCKOUT_RULES:
        if fail_count >= threshold:
            elapsed = (datetime.now(timezone.utc) - last_fail).total_seconds()
            remaining = lock_secs - elapsed
            return max(0, int(remaining))
    return 0


def record_attempt(conn, identifier, success):
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO login_attempts (identifier, success) VALUES (%s, %s)',
            (identifier, success),
        )


def clear_attempts(conn, identifier):
    with conn.cursor() as cur:
        cur.execute('DELETE FROM login_attempts WHERE identifier = %s', (identifier,))


# ── Shield charge calculation ─────────────────────────────────────────────────

def calc_shield_charges(owned_items):
    if 'iron_shield' in owned_items:
        return 3
    if 'shield_1' in owned_items:
        return 1
    return 0


# ── Helper: require JSON Content-Type on POST ─────────────────────────────────

def require_json():
    if request.method == 'POST' and not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    return None


# ── Static route ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


# ── Auth endpoints ────────────────────────────────────────────────────────────

@app.route('/api/me')
def me():
    if current_user.is_authenticated:
        return jsonify({'username': current_user.username})
    return jsonify({'username': None}), 200


@app.route('/api/register', methods=['POST'])
@limiter.limit('5 per hour')
def register():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not username.isalnum() or not (3 <= len(username) <= 32):
        return jsonify({'error': 'Username must be 3–32 alphanumeric characters'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    ip = get_remote_address()
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # One account per IP
            cur.execute('SELECT id FROM users WHERE ip_address = %s', (ip,))
            if cur.fetchone():
                return jsonify({'error': 'An account already exists from this IP address'}), 409

            # Username uniqueness
            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cur.fetchone():
                return jsonify({'error': 'Username already taken'}), 409

            cur.execute(
                'INSERT INTO users (username, password_hash, ip_address) VALUES (%s, %s, %s) RETURNING id',
                (username, pw_hash, ip),
            )
            user_id = cur.fetchone()['id']

            # Create game state row
            cur.execute('INSERT INTO game_state (user_id) VALUES (%s)', (user_id,))

        conn.commit()

        user_obj = User(user_id, username)
        login_user(user_obj, remember=True)
        session.permanent = True

        return jsonify({'username': username}), 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({'error': 'Username already taken'}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Registration failed'}), 500
    finally:
        conn.close()


@app.route('/api/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    ip = get_remote_address()

    conn = get_db()
    try:
        # Check lockout by IP and username
        ip_wait = check_lockout(conn, f'ip:{ip}')
        user_wait = check_lockout(conn, f'user:{username}')
        wait = max(ip_wait, user_wait)
        if wait > 0:
            return jsonify({'error': f'Too many failed attempts. Try again in {wait}s'}), 429

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT id, username, password_hash FROM users WHERE username = %s', (username,))
            row = cur.fetchone()

        if not row or not bcrypt.checkpw(password.encode(), row['password_hash'].encode()):
            record_attempt(conn, f'ip:{ip}', False)
            record_attempt(conn, f'user:{username}', False)
            conn.commit()
            return jsonify({'error': 'Invalid username or password'}), 401

        # Success
        clear_attempts(conn, f'ip:{ip}')
        clear_attempts(conn, f'user:{username}')
        conn.commit()

        user_obj = User(row['id'], row['username'])
        login_user(user_obj, remember=True)
        session.permanent = True

        return jsonify({'username': row['username']}), 200

    except Exception:
        conn.rollback()
        return jsonify({'error': 'Login failed'}), 500
    finally:
        conn.close()


@app.route('/api/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'ok': True}), 200


# ── Game endpoints ────────────────────────────────────────────────────────────

@app.route('/api/state')
@login_required
def get_state():
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM game_state WHERE user_id = %s', (current_user.id,))
            gs = cur.fetchone()

        owned = list(gs['owned_items'])
        # Recalculate shield charges on each login/state fetch
        charges = calc_shield_charges(owned)

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE game_state SET shield_charges = %s WHERE user_id = %s',
                (charges, current_user.id),
            )
        conn.commit()

        return jsonify({
            'wins': gs['wins'],
            'losses': gs['losses'],
            'fish_clicks': gs['fish_clicks'],
            'streak': gs['streak'],
            'owned_items': owned,
            'equipped_fish': gs['equipped_fish'],
            'shield_charges': charges,
        })
    except Exception:
        conn.rollback()
        return jsonify({'error': 'Failed to load state'}), 500
    finally:
        conn.close()


@app.route('/api/spin', methods=['POST'])
@login_required
@limiter.limit('10 per second')
def spin():
    err = require_json()
    if err:
        return err

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'SELECT * FROM game_state WHERE user_id = %s FOR UPDATE',
                (current_user.id,),
            )
            gs = cur.fetchone()

        owned = list(gs['owned_items'])
        streak = gs['streak']
        shield_charges = gs['shield_charges']

        # Determine outcome
        if 'singularity' in owned:
            outcome = 'win'
        else:
            outcome = random.choice(['win', 'lose'])

        # Multipliers
        win_mult = (16 if 'winmult_4' in owned else
                    8  if 'winmult_3' in owned else
                    4  if 'winmult_2' in owned else
                    2  if 'winmult_1' in owned else 1)
        bonus_mult = (10 if 'bonusmult_3' in owned else
                      5  if 'bonusmult_2' in owned else
                      2  if 'bonusmult_1' in owned else 1)

        shield_used = False
        new_wins   = gs['wins']
        new_losses = gs['losses']
        bonus_earned = 0

        if outcome == 'lose' and streak > 0 and shield_charges > 0:
            # Shield absorbs the loss — preserve streak
            shield_charges -= 1
            shield_used = True
            new_streak = streak
        else:
            if outcome == 'win':
                new_streak = streak + 1 if streak >= 0 else 1
            else:
                new_streak = streak - 1 if streak <= 0 else -1

            count = abs(new_streak)
            raw_bonus = math.pow(2, count - 3) if count >= 3 else 0
            bonus_earned = int(raw_bonus * bonus_mult)

            if outcome == 'win':
                new_wins += win_mult + bonus_earned
                if 'party_mode' in owned:
                    pass  # confetti handled client-side
            else:
                new_losses += 1 + bonus_earned

        # Calculate wheel rotation angle
        extra_spins = random.randint(5, 8) * 360
        if outcome == 'win':
            segment_angle = random.uniform(200, 340)
        else:
            segment_angle = random.uniform(20, 160)
        total_rotation = extra_spins + segment_angle

        with conn.cursor() as cur:
            cur.execute(
                '''UPDATE game_state
                   SET wins = %s, losses = %s, streak = %s, shield_charges = %s
                   WHERE user_id = %s''',
                (new_wins, new_losses, new_streak, shield_charges, current_user.id),
            )
        conn.commit()

        return jsonify({
            'result': outcome,
            'angle': total_rotation,
            'wins': new_wins,
            'losses': new_losses,
            'streak': new_streak,
            'shield_charges': shield_charges,
            'shield_used': shield_used,
            'bonus_earned': bonus_earned,
        })
    except Exception:
        conn.rollback()
        return jsonify({'error': 'Spin failed'}), 500
    finally:
        conn.close()


@app.route('/api/buy', methods=['POST'])
@login_required
def buy():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id') or ''

    if item_id not in ALL_ITEMS:
        return jsonify({'error': 'Unknown item'}), 400

    item = ALL_ITEMS[item_id]
    cost = item['cost']
    requires = item.get('requires')

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'SELECT fish_clicks, owned_items FROM game_state WHERE user_id = %s FOR UPDATE',
                (current_user.id,),
            )
            gs = cur.fetchone()

        owned = list(gs['owned_items'])
        fish_clicks = gs['fish_clicks']

        if item_id in owned:
            return jsonify({'error': 'Already owned'}), 409
        if requires and requires not in owned:
            return jsonify({'error': 'Prerequisite not met'}), 400
        if fish_clicks < cost:
            return jsonify({'error': 'Insufficient fish clicks'}), 402

        new_clicks = fish_clicks - cost
        new_owned = owned + [item_id]

        # Recalculate shield charges if a shield was purchased
        new_charges = calc_shield_charges(new_owned)

        with conn.cursor() as cur:
            cur.execute(
                '''UPDATE game_state
                   SET fish_clicks = %s, owned_items = %s, shield_charges = %s
                   WHERE user_id = %s''',
                (new_clicks, new_owned, new_charges, current_user.id),
            )
        conn.commit()

        return jsonify({
            'fish_clicks': new_clicks,
            'owned_items': new_owned,
            'shield_charges': new_charges,
        })
    except Exception:
        conn.rollback()
        return jsonify({'error': 'Purchase failed'}), 500
    finally:
        conn.close()


@app.route('/api/equip', methods=['POST'])
@login_required
def equip():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    fish_id = data.get('fish_id') or ''

    if fish_id not in VALID_FISH_IDS:
        return jsonify({'error': 'Invalid fish'}), 400

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT owned_items FROM game_state WHERE user_id = %s', (current_user.id,))
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
        conn.rollback()
        return jsonify({'error': 'Equip failed'}), 500
    finally:
        conn.close()


@app.route('/api/fish-click', methods=['POST'])
@login_required
@limiter.limit('30 per second')
def fish_click():
    err = require_json()
    if err:
        return err

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'SELECT fish_clicks, owned_items FROM game_state WHERE user_id = %s FOR UPDATE',
                (current_user.id,),
            )
            gs = cur.fetchone()

        owned = list(gs['owned_items'])
        amount = 2 if 'double_click' in owned else 1
        new_clicks = gs['fish_clicks'] + amount

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE game_state SET fish_clicks = %s WHERE user_id = %s',
                (new_clicks, current_user.id),
            )
        conn.commit()

        return jsonify({'fish_clicks': new_clicks})
    except Exception:
        conn.rollback()
        return jsonify({'error': 'Click failed'}), 500
    finally:
        conn.close()


@app.route('/api/click-frenzy', methods=['POST'])
@login_required
def click_frenzy():
    err = require_json()
    if err:
        return err

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'SELECT fish_clicks, owned_items FROM game_state WHERE user_id = %s FOR UPDATE',
                (current_user.id,),
            )
            gs = cur.fetchone()

        owned = list(gs['owned_items'])

        if 'clickfrenzy_3' in owned:
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
        conn.rollback()
        return jsonify({'error': 'Frenzy tick failed'}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
