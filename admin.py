"""Admin panel API (users.is_admin only; everyone else gets 404)."""
import datetime as dt
import functools
import json
import logging
from collections import defaultdict
from datetime import timezone
from pathlib import Path

import psycopg2.extras
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

import anticheat
from db import db_connection
from models import DEVICE_COOKIE
from seasons import next_rollover_after
from security import require_json

log = logging.getLogger('wheel')
admin_bp = Blueprint('admin', __name__)

UNINFORMATIVE_IPS = anticheat.UNINFORMATIVE_IPS
CLOSED_UNTIL = dt.datetime(anticheat.CLOSED_YEAR, 12, 31, tzinfo=timezone.utc)
REASON_MAX = 80
# Written by bin/rollover.sh in the app dir (its defaults: $APP_DIR/ROLLOVER_FAILED, $APP_DIR/logs).
APP_DIR = Path(__file__).resolve().parent
ROLLOVER_MARKER = APP_DIR / 'ROLLOVER_FAILED'
ROLLOVER_LOGS = APP_DIR / 'logs'
LOG_TAIL_LINES = 80


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Not found'}), 404
        return view(*args, **kwargs)
    return wrapped


def pending_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM users WHERE NOT approved AND (banned_until IS NULL OR banned_until <= NOW())')
        return cur.fetchone()[0]


@admin_bp.route('/api/fingerprint', methods=['POST'])
@login_required
def fingerprint():
    err = require_json()
    if err:
        return err
    device_id = request.cookies.get(DEVICE_COOKIE)
    if not device_id:
        return jsonify({'error': 'No device cookie'}), 400
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                anticheat.record_fingerprint(cur, current_user.id, device_id,
                                             (request.get_json(silent=True) or {}).get('fp'))
            conn.commit()
        return jsonify({'ok': True})
    except Exception:
        log.exception('FINGERPRINT_ERROR  user_id=%s', current_user.id)
        return jsonify({'error': 'Could not save'}), 500


def _log_tail(path: Path) -> str:
    try:
        return '\n'.join(path.read_text(errors='replace').splitlines()[-LOG_TAIL_LINES:])
    except OSError as e:
        return f'(could not read {path.name}: {e.strerror})'


def _rollover() -> dict:
    """The last tide-turn run and any unresolved failure, for the admin Tide tab."""
    logs = sorted(ROLLOVER_LOGS.glob('rollover-*.log'))
    last = None
    if logs:
        tail = _log_tail(logs[-1])
        last = {'log': logs[-1].name, 'time': _iso(dt.datetime.fromtimestamp(logs[-1].stat().st_mtime, timezone.utc)),
                'result': tail.splitlines()[-1] if tail else '', 'tail': tail}
    failed = None
    if ROLLOVER_MARKER.exists():
        info = dict(line.split('=', 1) for line in ROLLOVER_MARKER.read_text(errors='replace').splitlines() if '=' in line)
        log_path = Path(info.get('log', '')).resolve()
        # Only show logs from our own logs dir, whatever the marker says.
        tail = _log_tail(log_path) if log_path.parent == ROLLOVER_LOGS.resolve() else '(log not found)'
        failed = {'time': info.get('time'), 'step': info.get('step', 'unknown'), 'log': log_path.name, 'tail': tail}
    return {'failed': failed, 'last': last, 'release_hold': (APP_DIR / 'RELEASE_HOLD').exists()}


def _iso(v):
    return v.isoformat() if v else None


def _matches(players, devices):
    """For each account, the other accounts that share a browser, fingerprint or IP with it."""
    owners = defaultdict(set)  # (via, value) -> user ids
    for p in players:
        if p['signup_ip'] not in UNINFORMATIVE_IPS:
            owners[('network', p['signup_ip'])].add(p['id'])
    for d in devices:
        owners[('browser', d['device_id'])].add(d['user_id'])
        if d['fp_hash']:
            owners[('fingerprint', d['fp_hash'])].add(d['user_id'])
        if d['ip'] not in UNINFORMATIVE_IPS:
            owners[('network', d['ip'])].add(d['user_id'])
    found = defaultdict(lambda: defaultdict(set))  # user id -> other id -> {via}
    for (via, _), ids in owners.items():
        for a in ids:
            for b in ids - {a}:
                found[a][b].add(via)
    return found


@admin_bp.route('/api/admin/overview')
@login_required
@admin_required
def overview():
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                '''SELECT u.id, u.username, u.created_at, u.approved, u.is_admin, u.banned_until, u.ban_reason,
                          host(u.ip_address) AS signup_ip, gs.wins, gs.catch_count,
                          COALESCE(fd.casts, 0) AS casts_today,
                          (SELECT MAX(d.last_seen) FROM user_devices d WHERE d.user_id = u.id) AS last_seen
                   FROM users u
                   LEFT JOIN game_state gs ON gs.user_id = u.id
                   LEFT JOIN fishing_days fd ON fd.user_id = u.id
                        AND fd.day = (NOW() AT TIME ZONE 'Europe/London')::date
                   ORDER BY u.created_at DESC NULLS LAST'''
            )
            players = cur.fetchall()
            cur.execute('''SELECT user_id, device_id, fp, fp_hash, ua, ip, country, first_seen, last_seen
                           FROM user_devices ORDER BY last_seen DESC''')
            devices = cur.fetchall()
            cur.execute('''SELECT f.id, u.username, f.kind, f.started_at, f.last_seen, f.detail
                           FROM cheat_flags f JOIN users u ON u.id = f.user_id
                           ORDER BY f.last_seen DESC LIMIT 50''')
            flags = cur.fetchall()
            require = anticheat.require_approval(cur)

    now = dt.datetime.now(timezone.utc)
    names = {p['id']: p['username'] for p in players}
    banned = {p['id'] for p in players if p['banned_until'] and p['banned_until'] > now}
    found = _matches(players, devices)
    by_user = defaultdict(list)
    for d in devices:
        by_user[d['user_id']].append({
            'device': d['device_id'][:8], 'ua': d['ua'], 'ip': d['ip'], 'country': d['country'],
            'fp': d['fp'], 'fp_hash': d['fp_hash'],
            'first_seen': _iso(d['first_seen']), 'last_seen': _iso(d['last_seen']),
        })

    def player(p):
        return {
            'id': p['id'], 'username': p['username'], 'created_at': _iso(p['created_at']),
            'approved': p['approved'], 'is_admin': p['is_admin'],
            'banned_until': _iso(p['banned_until']) if p['id'] in banned else None,
            'closed': p['id'] in banned and p['banned_until'].year >= anticheat.CLOSED_YEAR,
            'ban_reason': p['ban_reason'] if p['id'] in banned else None,
            'signup_ip': p['signup_ip'] if p['signup_ip'] not in UNINFORMATIVE_IPS else None,
            'wins': float(p['wins'] or 0), 'catches': p['catch_count'] or 0, 'casts_today': p['casts_today'],
            'last_seen': _iso(p['last_seen']),
            'devices': by_user[p['id']],
            'matches': sorted(({'username': names[o], 'via': sorted(via), 'suspended': o in banned}
                               for o, via in found[p['id']].items() if o in names),
                              key=lambda m: (not m['suspended'], m['username'])),
        }

    rows = [player(p) for p in players]
    return jsonify({
        'settings': {'require_approval': require, 'daily_cast_limit': anticheat.DAILY_CAST_LIMIT},
        'pending': [r for r in rows if not r['approved'] and not r['banned_until']],
        'players': [r for r in rows if r['approved'] or r['banned_until']],
        'flags': [{**f, 'started_at': _iso(f['started_at']), 'last_seen': _iso(f['last_seen'])} for f in flags],
        'next_tide': _iso(next_rollover_after(now)),
        'rollover': _rollover(),
    })


@admin_bp.route('/api/admin/rollover-dismiss', methods=['POST'])
@login_required
@admin_required
def rollover_dismiss():
    ROLLOVER_MARKER.unlink(missing_ok=True)
    log.warning('ADMIN_ACTION  admin=%s  action=rollover-dismiss', current_user.username)
    return jsonify({'ok': True})


def _target():
    """The user id an admin action names, or an error response."""
    data = request.get_json(silent=True) or {}
    uid = data.get('user_id')
    if not isinstance(uid, int) or isinstance(uid, bool):
        return None, data, (jsonify({'error': 'user_id must be a number'}), 400)
    return uid, data, None


def _update(sql, params, action, uid, detail=''):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql + ' RETURNING username', params)
            row = cur.fetchone()
        conn.commit()
    if not row:
        return jsonify({'error': "That account can't be changed that way."}), 409
    log.warning('ADMIN_ACTION  admin=%s  action=%s  user=%s  %s', current_user.username, action, row[0], detail)
    return jsonify({'ok': True})


@admin_bp.route('/api/admin/approve', methods=['POST'])
@login_required
@admin_required
def approve():
    uid, _, err = _target()
    return err or _update('UPDATE users SET approved = TRUE WHERE id = %s AND NOT approved', (uid,), 'approve', uid)


@admin_bp.route('/api/admin/reject', methods=['POST'])
@login_required
@admin_required
def reject():
    uid, _, err = _target()
    return err or _update(
        '''UPDATE users SET banned_until = %s, ban_reason = 'sign-up not approved'
           WHERE id = %s AND NOT approved AND NOT is_admin''', (CLOSED_UNTIL, uid), 'reject', uid)


@admin_bp.route('/api/admin/suspend', methods=['POST'])
@login_required
@admin_required
def suspend():
    uid, data, err = _target()
    if err:
        return err
    reason = data.get('reason')
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > REASON_MAX:
        return jsonify({'error': f'Give a reason (up to {REASON_MAX} characters). The player sees it.'}), 400
    until = next_rollover_after(dt.datetime.now(timezone.utc))
    return _update('UPDATE users SET banned_until = %s, ban_reason = %s WHERE id = %s AND NOT is_admin',
                   (until, reason.strip(), uid), 'suspend', uid, f'until={until.isoformat()}  reason={reason.strip()!r}')


@admin_bp.route('/api/admin/unsuspend', methods=['POST'])
@login_required
@admin_required
def unsuspend():
    uid, _, err = _target()
    return err or _update('UPDATE users SET banned_until = NULL, ban_reason = NULL WHERE id = %s AND banned_until IS NOT NULL',
                          (uid,), 'unsuspend', uid)


@admin_bp.route('/api/admin/settings', methods=['POST'])
@login_required
@admin_required
def settings():
    value = (request.get_json(silent=True) or {}).get('require_approval')
    if not isinstance(value, bool):
        return jsonify({'error': 'require_approval must be true or false'}), 400
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''INSERT INTO app_settings (key, value) VALUES ('require_approval', %s)
                           ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value''', (json.dumps(value),))
        conn.commit()
    log.warning('ADMIN_ACTION  admin=%s  action=settings  require_approval=%s', current_user.username, value)
    return jsonify({'ok': True})
