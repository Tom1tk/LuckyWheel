"""Account checks that run before every request."""
import hashlib
import json
import logging
import math
import re
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import jsonify, request, session
from flask_login import current_user

from db import db_connection
from models import AUTO_SPIN_INTERVAL_SECONDS, DEVICE_COOKIE

log = logging.getLogger(__name__)

_LONDON = ZoneInfo('Europe/London')
BOT_UA = re.compile(r'bot\b|bot/|crawl|spider|curl|wget|python|httpx|aiohttp|okhttp|go-http|java/|node-fetch|axios'
                    r'|headless|playwright|puppeteer|selenium', re.I)
LOCAL_ADDRS = frozenset({'127.0.0.1', '::1'})
# Shared addresses that say nothing about who signed up.
UNINFORMATIVE_IPS = frozenset({'192.168.68.10', '127.0.0.1', '::1', None, ''})
PENDING_ALLOWED = frozenset({'/api/logout', '/api/tab/heartbeat', '/api/fingerprint'})
SUSPENDED_ALLOWED = PENDING_ALLOWED | {'/api/chat'}
PENDING_MSG = "Your account is waiting for an admin to approve it. You can look around, but you can't play yet."
CLOSED_YEAR = 9999  # closed account


def _is_local():
    return request.remote_addr in LOCAL_ADDRS and 'X-Forwarded-For' not in request.headers


def _refuse_bots():
    if not request.path.startswith('/api/') or _is_local():
        return None
    ua = request.headers.get('User-Agent', '')
    if ua.startswith('Mozilla/') and not BOT_UA.search(ua):
        return None
    log.warning('BOT_REFUSED  ip=%s  path=%s  ua=%r', request.remote_addr, request.path, ua)
    return jsonify({'error': 'Automated clients are not allowed. Play in a web browser.'}), 403

MANUAL_ACTIONS = frozenset({'/api/cast', '/api/reel', '/api/land', '/api/spin', '/api/roll-dice'})
PLAY_BREAK = timedelta(minutes=15)
FLAG_AFTER = timedelta(hours=6)
TRACK_EVERY_S = 60
_last_tracked = {}

DAILY_CAST_LIMIT = 1000
CAP_MSG = (f"You've cast {DAILY_CAST_LIMIT:,} times today, which is the daily limit. "
           "Fishing opens again at midnight.")
STEADY_WINDOW = 100
STEADY_MAX_GAP_S = 120
STEADY_CV = 0.35


def suspension_message(user) -> str:
    reason = f' ({user.ban_reason})' if user.ban_reason else ''
    if user.banned_until.year >= CLOSED_YEAR:
        return f'Your account has been closed{reason}.'
    t = user.banned_until.astimezone(_LONDON)
    clock = f"{t:%-I:%M}" if t.minute else f"{t:%-I}"
    until = f"{t:%a %-d %b}, {clock}{t.strftime('%p').lower()}"
    return f'Your account is suspended until {until}{reason}.'


def restriction_message(user):
    """The banner text for an account that can't play right now, else None."""
    if user.is_suspended:
        return suspension_message(user)
    if not user.approved:
        return PENDING_MSG
    return None


def _refuse_restricted():
    if request.method in ('GET', 'HEAD', 'OPTIONS') or not request.path.startswith('/api/'):
        return None
    if not current_user.is_authenticated:
        return None
    if current_user.is_suspended:
        if request.path in SUSPENDED_ALLOWED:
            return None
        log.info('SUSPENDED_REFUSED  user=%s  path=%s', current_user.username, request.path)
        return jsonify({'error': suspension_message(current_user), 'restricted': True,
                        'suspended_until': current_user.banned_until.isoformat()}), 403
    if not current_user.approved and request.path not in PENDING_ALLOWED:
        log.info('PENDING_REFUSED  user=%s  path=%s', current_user.username, request.path)
        return jsonify({'error': PENDING_MSG, 'restricted': True}), 403
    return None


def _link_device():
    """Remember each browser an account plays from (once per session)."""
    device_id = request.cookies.get(DEVICE_COOKIE)
    if not device_id or not current_user.is_authenticated or session.get('device_linked') == device_id:
        return None
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO user_devices (user_id, device_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
                            (current_user.id, device_id))
            conn.commit()
        session['device_linked'] = device_id
    except Exception:
        log.warning('DEVICE_LINK_ERROR  user=%s', current_user.id, exc_info=True)
    return None


def _track_play():
    if request.method != 'POST' or request.path not in MANUAL_ACTIONS or not current_user.is_authenticated:
        return None
    now = time.monotonic()
    if now - _last_tracked.get(current_user.id, float('-inf')) < TRACK_EVERY_S:
        return None
    _last_tracked[current_user.id] = now
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE users SET
                           active_since = CASE WHEN last_action_at IS NULL OR last_action_at < NOW() - %s
                                               THEN NOW() ELSE active_since END,
                           last_action_at = NOW()
                       WHERE id = %s
                       RETURNING active_since, NOW() - active_since''',
                    (PLAY_BREAK, current_user.id),
                )
                started, played = cur.fetchone()
                if played >= FLAG_AFTER:
                    _flag(cur, 'continuous_play', started,
                          f'{played.total_seconds() / 3600:.1f}h of manual play with no 15-minute break')
            conn.commit()
    except Exception:
        log.warning('TRACK_PLAY_ERROR  user=%s', current_user.id, exc_info=True)
    return None


def _flag(cur, kind, started_at, detail):
    """Record (or refresh) one flag per player, kind and run/day."""
    cur.execute(
        '''INSERT INTO cheat_flags (user_id, kind, started_at, detail)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (user_id, kind, started_at)
           DO UPDATE SET last_seen = NOW(), detail = EXCLUDED.detail
           RETURNING xmax = 0''',
        (current_user.id, kind, started_at, detail),
    )
    if cur.fetchone()[0]:
        log.warning('CHEAT_FLAG  user=%s  kind=%s  detail=%s', current_user.username, kind, detail)


def _limit_fishing():
    """Daily cast limit and cast stats."""
    if request.method != 'POST' or request.path != '/api/cast' or not current_user.is_authenticated:
        return None
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # The upsert locks the row, so one player's casts on different workers queue up here.
                cur.execute(
                    '''INSERT INTO fishing_days (user_id, day, casts, last_cast_at)
                       VALUES (%s, (NOW() AT TIME ZONE 'Europe/London')::date, 1, NOW())
                       ON CONFLICT (user_id, day) DO UPDATE SET casts = fishing_days.casts + 1
                       RETURNING day, casts, EXTRACT(EPOCH FROM NOW() - last_cast_at)::float8,
                                 gap_n, gap_mean, gap_m2''',
                    (current_user.id,),
                )
                day, casts, gap, n, mean, m2 = cur.fetchone()
                if casts > DAILY_CAST_LIMIT:
                    if casts == DAILY_CAST_LIMIT + 1:
                        _flag(cur, 'daily_cap', day, f'Reached the limit of {DAILY_CAST_LIMIT:,} casts in a day')
                    conn.commit()
                    return jsonify({'error': CAP_MSG}), 429
                if gap and 0 < gap <= STEADY_MAX_GAP_S:
                    n += 1
                    delta = gap - mean
                    mean += delta / n
                    m2 += delta * (gap - mean)
                    if n >= STEADY_WINDOW:
                        cv = math.sqrt(m2 / n) / mean
                        if cv < STEADY_CV:
                            _flag(cur, 'steady_timing', day,
                                  f'{n} casts, mean gap {mean:.1f}s, cv {cv:.2f}')
                        n, mean, m2 = 0, 0.0, 0.0
                cur.execute('''UPDATE fishing_days SET last_cast_at = NOW(), gap_n = %s, gap_mean = %s, gap_m2 = %s
                               WHERE user_id = %s AND day = %s''', (n, mean, m2, current_user.id, day))
            conn.commit()
    except Exception:
        log.warning('LIMIT_FISHING_ERROR  user=%s', current_user.id, exc_info=True)
    return None


MIN_SPIN_GAP = timedelta(seconds=AUTO_SPIN_INTERVAL_SECONDS)
SPIN_PACE_MSG = 'The wheel is still spinning.'


def pace_spin(last_spin_at) -> bool:
    """False if a manual spin comes sooner than auto-spin would turn the wheel."""
    if last_spin_at is None or _is_local():
        return True
    return datetime.now(timezone.utc) - last_spin_at >= MIN_SPIN_GAP


def linked_to_suspended(cur, ip) -> bool:
    """True if a suspended account signed up or played from this address."""
    if ip in UNINFORMATIVE_IPS:
        return False
    cur.execute('''SELECT 1 FROM users u WHERE u.banned_until > NOW()
                   AND (host(u.ip_address) = %s
                        OR EXISTS (SELECT 1 FROM user_devices d WHERE d.user_id = u.id AND d.ip = %s))
                   LIMIT 1''', (ip, ip))
    return cur.fetchone() is not None


def device_is_banned(cur, device_id) -> bool:
    """True if any account that has played from this browser is suspended right now."""
    cur.execute('''SELECT 1 FROM user_devices d JOIN users u ON u.id = d.user_id
                   WHERE d.device_id = %s AND u.banned_until > NOW() LIMIT 1''', (device_id,))
    return cur.fetchone() is not None


def require_approval(cur) -> bool:
    cur.execute("SELECT value FROM app_settings WHERE key = 'require_approval'")
    row = cur.fetchone()
    return bool(row and (row['value'] if isinstance(row, dict) else row[0]))


# Untrusted client input: unknown keys dropped, strings capped, numbers finite.
FP_TEXT = ('platform', 'languages', 'tz', 'screen', 'gpu', 'canvas')
FP_NUMBERS = ('dpr', 'depth', 'cores', 'memory', 'touch')


def clean_fingerprint(raw) -> dict:
    if not isinstance(raw, dict):
        return {}
    fp = {k: raw[k][:200] for k in FP_TEXT if isinstance(raw.get(k), str) and raw[k]}
    fp.update({k: raw[k] for k in FP_NUMBERS
               if isinstance(raw.get(k), (int, float)) and not isinstance(raw[k], bool) and math.isfinite(raw[k])})
    return fp


def record_fingerprint(cur, user_id, device_id, raw):
    fp = clean_fingerprint(raw)
    fp_hash = hashlib.sha256(json.dumps(fp, sort_keys=True).encode()).hexdigest()[:16] if fp else None
    cur.execute(
        '''INSERT INTO user_devices (user_id, device_id, fp, fp_hash, ua, ip, country, last_seen)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
           ON CONFLICT (user_id, device_id) DO UPDATE SET
               fp = EXCLUDED.fp, fp_hash = EXCLUDED.fp_hash, ua = EXCLUDED.ua,
               ip = EXCLUDED.ip, country = EXCLUDED.country, last_seen = NOW()''',
        (user_id, device_id, json.dumps(fp), fp_hash, request.headers.get('User-Agent', '')[:400],
         request.remote_addr, request.headers.get('Cf-Ipcountry')),
    )
    return fp_hash


def register(app):
    app.before_request(_refuse_bots)
    app.before_request(_refuse_restricted)
    app.before_request(_link_device)
    app.before_request(_track_play)
    app.before_request(_limit_fishing)
