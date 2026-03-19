import logging
import random
import secrets

import bcrypt
import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify, make_response, request, send_from_directory, session
from flask_limiter.util import get_remote_address
from flask_login import current_user, login_user, logout_user

from db import db_connection
from extensions import limiter, login_manager
from models import DEVICE_COOKIE, DEVICE_COOKIE_MAX_AGE, User
from security import check_lockout, clear_attempts, record_attempt, require_json

log = logging.getLogger('wheel')
auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT id, username, session_token FROM users WHERE id = %s',
                    (user_id,),
                )
                row = cur.fetchone()
        if row and row['session_token'] == session.get('session_token'):
            return User(row['id'], row['username'])
    except Exception:
        log.warning('LOAD_USER_ERROR  user_id=%s', user_id, exc_info=True)
    return None


def issue_session_token(conn, user_id):
    """Generate a new session token, write it to DB, and store in Flask session."""
    token = secrets.token_hex(32)
    with conn.cursor() as cur:
        cur.execute('UPDATE users SET session_token = %s WHERE id = %s', (token, user_id))
    session['session_token'] = token


@auth_bp.route('/')
def index():
    resp = make_response(send_from_directory('static', 'index.html'))
    if not request.cookies.get(DEVICE_COOKIE):
        device_id = secrets.token_hex(32)
        resp.set_cookie(
            DEVICE_COOKIE, device_id,
            max_age=DEVICE_COOKIE_MAX_AGE,
            httponly=True, samesite='Lax',
        )
    return resp


@auth_bp.route('/api/me')
def me():
    if current_user.is_authenticated:
        return jsonify({'username': current_user.username})
    return jsonify({'username': None}), 200


@auth_bp.route('/api/register', methods=['POST'])
@limiter.limit('5 per hour')
def register():
    err = require_json()
    if err:
        return err

    ip = get_remote_address()
    data = request.get_json(silent=True) or {}
    raw_username = data.get('username') or ''
    username = raw_username.strip().lower()
    password = data.get('password') or ''
    device_id = request.cookies.get(DEVICE_COOKIE)
    ua = request.headers.get('User-Agent', 'unknown')

    log.info('REGISTER_ATTEMPT  ip=%s  raw_username=%r  normalised=%r  device_id=%s  ua=%s',
             ip, raw_username, username, device_id or 'none', ua)

    if not username or not username.isalnum() or not (3 <= len(username) <= 32):
        log.warning('REGISTER_REJECT  reason=bad_username  raw=%r  ip=%s', raw_username, ip)
        return jsonify({'error': 'Username must be 3–32 alphanumeric characters'}), 400
    if len(password) < 6:
        log.warning('REGISTER_REJECT  reason=short_password  username=%s  ip=%s', username, ip)
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if device_id:
                    cur.execute('SELECT id, username FROM users WHERE device_id = %s', (device_id,))
                    existing = cur.fetchone()
                    if existing:
                        log.warning(
                            'REGISTER_REJECT  reason=device_taken  device_id=%s  existing_user=%s  new_attempt=%s  ip=%s',
                            device_id, existing['username'], username, ip,
                        )
                        return jsonify({'error': 'An account already exists on this device'}), 409

                cur.execute('SELECT id FROM users WHERE username = %s', (username,))
                if cur.fetchone():
                    log.warning('REGISTER_REJECT  reason=username_taken  username=%s  ip=%s', username, ip)
                    return jsonify({'error': 'Username already taken'}), 409

                cur.execute(
                    'INSERT INTO users (username, password_hash, ip_address, device_id) VALUES (%s, %s, %s, %s) RETURNING id',
                    (username, pw_hash, ip, device_id),
                )
                user_id = cur.fetchone()['id']
                cur.execute('INSERT INTO game_state (user_id) VALUES (%s)', (user_id,))

            issue_session_token(conn, user_id)
            conn.commit()

        user_obj = User(user_id, username)
        login_user(user_obj, remember=False)
        session.permanent = True

        log.info('REGISTER_SUCCESS  username=%s  user_id=%d  device_id=%s  ip=%s',
                 username, user_id, device_id or 'none', ip)
        return jsonify({'username': username}), 201

    except psycopg2.errors.UniqueViolation:
        log.warning('REGISTER_REJECT  reason=unique_violation  username=%s  ip=%s', username, ip)
        return jsonify({'error': 'Username already taken'}), 409
    except Exception:
        log.exception('REGISTER_ERROR  username=%s  ip=%s', username, ip)
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/api/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    err = require_json()
    if err:
        return err

    ip = get_remote_address()
    data = request.get_json(silent=True) or {}
    raw_username = data.get('username') or ''
    username = raw_username.strip().lower()
    password = data.get('password') or ''
    ua = request.headers.get('User-Agent', 'unknown')

    log.info('LOGIN_ATTEMPT  ip=%s  raw_username=%r  normalised=%r  ua=%s',
             ip, raw_username, username, ua)

    if not username:
        log.warning('LOGIN_REJECT  reason=empty_username  ip=%s', ip)
        return jsonify({'error': 'Invalid username or password'}), 401

    try:
        with db_connection() as conn:
            user_wait = check_lockout(conn, f'user:{username}')
            if user_wait > 0:
                log.warning('LOGIN_REJECT  reason=lockout  username=%s  wait_secs=%d  ip=%s',
                            username, user_wait, ip)
                return jsonify({'error': f'Too many failed attempts. Try again in {user_wait}s'}), 429

            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT id, username, password_hash FROM users WHERE username = %s',
                    (username,),
                )
                row = cur.fetchone()

            if not row:
                log.warning('LOGIN_REJECT  reason=username_not_found  username=%r  ip=%s', username, ip)
                record_attempt(conn, f'user:{username}', False)
                conn.commit()
                return jsonify({'error': 'Invalid username or password'}), 401

            pw_ok = bcrypt.checkpw(password.encode(), row['password_hash'].encode())
            if not pw_ok:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM login_attempts WHERE identifier = %s "
                        "AND success = FALSE AND attempted_at > NOW() - INTERVAL '1 hour'",
                        (f'user:{username}',),
                    )
                    fail_count = cur.fetchone()[0] + 1
                log.warning('LOGIN_REJECT  reason=wrong_password  username=%s  fail_count=%d  ip=%s',
                            username, fail_count, ip)
                record_attempt(conn, f'user:{username}', False)
                conn.commit()
                return jsonify({'error': 'Invalid username or password'}), 401

            # Success
            clear_attempts(conn, f'user:{username}')
            # Probabilistic stale-attempt cleanup (1-in-50 chance)
            if random.randint(1, 50) == 1:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM login_attempts WHERE attempted_at < NOW() - INTERVAL '7 days'"
                    )
            issue_session_token(conn, row['id'])
            conn.commit()

        user_obj = User(row['id'], row['username'])
        login_user(user_obj, remember=False)
        session.permanent = True

        log.info('LOGIN_SUCCESS  username=%s  user_id=%d  ip=%s', row['username'], row['id'], ip)
        return jsonify({'username': row['username']}), 200

    except Exception:
        log.exception('LOGIN_ERROR  username=%s  ip=%s', username, ip)
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE users SET session_token = NULL WHERE id = %s',
                        (current_user.id,),
                    )
                conn.commit()
        except Exception:
            log.exception('LOGOUT_ERROR  user_id=%s', current_user.id)
    logout_user()
    return jsonify({'ok': True}), 200
