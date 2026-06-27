import logging
import re
import time
from datetime import datetime, timezone, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import db_connection
from extensions import limiter
from security import require_json

log = logging.getLogger('wheel')
chat_bp = Blueprint('chat', __name__)

# Extreme slurs only — whole-word matching to avoid false positives
_BLOCKED_WORDS = [
    r'\bn[i1!|]gg[e3]r\b',
    r'\bf[a@]gg[o0]t\b',
    r'\bk[i1]k[e3]\b',
    r'\bch[i1]nk\b',
    r'\bsp[i1]c\b',
    r'\bw[e3]tb[a@]ck\b',
]
_BLOCKED_RE = re.compile(
    '|'.join(_BLOCKED_WORDS),
    re.IGNORECASE,
)

MAX_MSG_LEN = 150
SPAM_WINDOW_SECS = 6
SPAM_THRESHOLD = 5
BLOCK_RESET_HOURS = 1
MAX_CHAT_MESSAGES = 200
CHAT_PAGE_SIZE = 50
CHAT_PAGE_MAX = 200


def _build_chat_query(args):
    """Build (sql, params) for chat SELECT with optional cursor pagination.

    args: dict-like with optional 'before' (id cursor) and 'limit' keys.
    Returns (sql, params), or None if 'before' is present but not a valid int.
    """
    try:
        limit = int(args.get('limit', CHAT_PAGE_SIZE))
    except (TypeError, ValueError):
        limit = CHAT_PAGE_SIZE
    limit = max(1, min(limit, CHAT_PAGE_MAX))

    before = args.get('before')
    if before is not None and before != '':
        try:
            before_id = int(before)
        except (TypeError, ValueError):
            return None
        return (
            'SELECT id, username, message, created_at, message_type '
            'FROM chat_messages '
            'WHERE id < %s '
            'ORDER BY id DESC '
            'LIMIT %s',
            (before_id, limit),
        )
    return (
        'SELECT id, username, message, created_at, message_type '
        'FROM chat_messages '
        'ORDER BY id DESC '
        'LIMIT %s',
        (limit,),
    )


def _check_and_update_spam(conn, user_id, is_blocked_word=False):
    """
    Returns (blocked_until_dt, seconds_remaining) if the user is or should be blocked,
    or (None, 0) if the message should be allowed.
    Modifies the DB row as a side effect.
    """
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        # Upsert spam tracking row
        cur.execute(
            '''
            INSERT INTO chat_spam_tracking (user_id, recent_timestamps, blocked_until, block_count, last_block_at)
            VALUES (%s, '{}', NULL, 0, NULL)
            ON CONFLICT (user_id) DO NOTHING
            ''',
            (user_id,),
        )
        cur.execute(
            'SELECT recent_timestamps, blocked_until, block_count, last_block_at '
            'FROM chat_spam_tracking WHERE user_id = %s',
            (user_id,),
        )
        row = cur.fetchone()
        recent_timestamps, blocked_until, block_count, last_block_at = row

        # Check existing block
        if blocked_until and blocked_until > now:
            secs = int((blocked_until - now).total_seconds()) + 1
            return blocked_until, secs

        # Reset block_count if last block was more than 1 hour ago
        if last_block_at and (now - last_block_at).total_seconds() > BLOCK_RESET_HOURS * 3600:
            block_count = 0

        # Prune timestamps outside the spam window
        cutoff = now - timedelta(seconds=SPAM_WINDOW_SECS)
        recent_timestamps = [ts for ts in (recent_timestamps or []) if ts > cutoff]

        # Append current timestamp
        recent_timestamps.append(now)

        if is_blocked_word or len(recent_timestamps) >= SPAM_THRESHOLD:
            # Apply escalating block
            duration_secs = 60 * (2 ** block_count)
            new_blocked_until = now + timedelta(seconds=duration_secs)
            cur.execute(
                '''UPDATE chat_spam_tracking
                   SET recent_timestamps = %s,
                       blocked_until = %s,
                       block_count = %s,
                       last_block_at = %s
                   WHERE user_id = %s''',
                (
                    recent_timestamps,
                    new_blocked_until,
                    block_count + 1,
                    now,
                    user_id,
                ),
            )
            secs = duration_secs + 1
            return new_blocked_until, secs
        else:
            # Update timestamps only
            cur.execute(
                'UPDATE chat_spam_tracking SET recent_timestamps = %s WHERE user_id = %s',
                (recent_timestamps, user_id),
            )
            return None, 0


@chat_bp.route('/api/chat', methods=['GET'])
@limiter.limit('30 per minute')
def get_chat():
    query = _build_chat_query(request.args)
    if query is None:
        return jsonify({'error': 'Invalid before id'}), 400
    sql, params = query

    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    # Reverse so oldest is first
    rows = list(reversed(rows))
    messages = [
        {
            'id': r[0],
            'username': r[1],
            'message': r[2],
            'created_at': r[3].isoformat(),
            'message_type': r[4] if r[4] else 'user',
        }
        for r in rows
    ]
    return jsonify(messages)


@chat_bp.route('/api/chat', methods=['POST'])
@login_required
@limiter.limit('1 per second')
def post_chat():
    err = require_json()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()

    # Strip HTML tags
    message = re.sub(r'<[^>]*>', '', message)

    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    if len(message) > MAX_MSG_LEN:
        return jsonify({
            'error': f'Message too long ({len(message)}/{MAX_MSG_LEN} characters)'
        }), 400

    is_blocked_word = bool(_BLOCKED_RE.search(message))

    with db_connection() as conn:
        blocked_until, secs = _check_and_update_spam(conn, current_user.id, is_blocked_word)
        if blocked_until:
            conn.commit()
            return jsonify({
                'error': 'You are timed out.',
                'seconds_remaining': secs,
            }), 429

        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO chat_messages (user_id, username, message, message_type) VALUES (%s, %s, %s, %s)',
                (current_user.id, current_user.username, message, 'user'),
            )
            # Trim to MAX_CHAT_MESSAGES most recent messages
            cur.execute(
                f'''DELETE FROM chat_messages
                   WHERE id NOT IN (
                       SELECT id FROM chat_messages ORDER BY id DESC LIMIT {MAX_CHAT_MESSAGES}
                   )'''
            )
        conn.commit()

    return jsonify({'ok': True}), 201


SYSTEM_MESSAGE_THROTTLE_SECS = 30
# Per-worker, in-memory (same pattern as game.py's _fish_clicks_cache) -- this
# is a chat-spam nicety, not a security boundary, so per-worker approximation
# under gunicorn's multiple workers is an acceptable tradeoff against adding a
# new DB table just for a 30s cooldown.
_system_message_last_posted: dict = {}


# T209: event_kinds whose auto-posted system messages get per-user dedup
# (the user's previous message of the same kind is deleted before the new
# one is inserted). First-spin is intentionally NOT in this set — it's a
# historical record the operator wants preserved.
#
# T222: prestige is now deduped. The player only sees their LATEST
# prestige level in chat; older messages for the same player are removed
# when they re-prestige. This keeps the channel uncluttered for players
# who prestige many times.
DEDUP_EVENT_KINDS = frozenset({
    'big_win',           # covers regular big wins (jackpots no longer post)
    'hot_streak',        # wager-streak milestone
    'goal_milestone_25',
    'goal_milestone_50',
    'goal_milestone_75',
    'prestige',          # T222: per-user dedup; show only latest level
})


def post_system_message(conn, message: str, message_type: str = 'system', event_kind: str | None = None):
    """Insert a system message into chat (user_id=NULL, username='SYSTEM').

    Throttled to at most one message per SYSTEM_MESSAGE_THROTTLE_SECS per
    event_kind (defaults to message_type), so a rapid chain of the same kind
    of event (e.g. repeated jackpots) can't flood the channel. Different
    event kinds throttle independently.

    Used by Season 8 features: bounty completions, singularity fills,
    prestige announcements, jackpots. Must be called within an existing
    db_connection() context — caller manages commit/rollback.
    """
    if not message:
        return
    kind = event_kind or message_type
    now = time.monotonic()
    if now - _system_message_last_posted.get(kind, 0.0) < SYSTEM_MESSAGE_THROTTLE_SECS:
        return
    _system_message_last_posted[kind] = now

    message = message[:MAX_MSG_LEN]
    with conn.cursor() as cur:
        cur.execute(
            '''INSERT INTO chat_messages (user_id, username, message, message_type)
               VALUES (NULL, 'SYSTEM', %s, %s)''',
            (message, message_type),
        )
        # Trim to MAX_CHAT_MESSAGES most recent (system messages share the table with
        # player chat; post_chat() already does this for its own inserts,
        # but a quiet stretch of system-only activity skipped this entirely).
        cur.execute(
            f'''DELETE FROM chat_messages
               WHERE id NOT IN (
                   SELECT id FROM chat_messages ORDER BY id DESC LIMIT {MAX_CHAT_MESSAGES}
               )'''
        )


def post_dedup_system_message(conn, message, user_id, event_kind, *, message_type='system'):
    """Insert a per-user system message with dedup of the user's previous one.

    T209: auto-posted system messages (big_win, hot_streak,
    goal_milestone_*) accumulate over time and crowd the chat. For these
    event_kinds (the DEDUP_EVENT_KINDS set) we look up the user's most
    recent chat message with the same event_kind + message_type, delete
    it, then insert the new one — so the user always sees at most one
    message of each dedup-eligible event_kind.

    For event_kinds NOT in DEDUP_EVENT_KINDS (e.g. first_spin), this
    falls through to post_system_message unchanged. That way future
    system messages that should be preserved can opt in by simply not
    being in the dedup set.

    The 30s per-event_kind throttle from post_system_message is bypassed
    for dedup-eligible kinds (the per-user dedup itself caps the rate);
    non-dedup kinds still get the throttle. Must be called within an
    existing db_connection() context — caller manages commit/rollback.
    """
    if not message:
        return
    if event_kind not in DEDUP_EVENT_KINDS:
        return post_system_message(
            conn, message, message_type=message_type, event_kind=event_kind,
        )

    message = message[:MAX_MSG_LEN]
    with conn.cursor() as cur:
        # Find the user's most recent chat message with the same event_kind
        # and message_type. message_type='system' matches auto-posted system
        # messages; user messages (message_type='user') are never affected
        # because they have event_kind=NULL and don't match event_kind IN (...) here.
        cur.execute(
            '''SELECT id FROM chat_messages
               WHERE user_id = %s
                 AND event_kind = %s
                 AND message_type = %s
               ORDER BY id DESC
               LIMIT 1''',
            (user_id, event_kind, message_type),
        )
        row = cur.fetchone()
        if row is not None:
            # Row can be a tuple (default cursor) or a dict (RealDictCursor).
            prev_id = row[0] if isinstance(row, tuple) else row['id']
            cur.execute(
                'DELETE FROM chat_messages WHERE id = %s',
                (prev_id,),
            )
        cur.execute(
            '''INSERT INTO chat_messages
                  (user_id, username, message, message_type, event_kind)
               VALUES (%s, 'SYSTEM', %s, %s, %s)''',
            (user_id, message, message_type, event_kind),
        )
        # Trim to MAX_CHAT_MESSAGES most recent (same trim post_system_message does).
        cur.execute(
            f'''DELETE FROM chat_messages
               WHERE id NOT IN (
                   SELECT id FROM chat_messages ORDER BY id DESC LIMIT {MAX_CHAT_MESSAGES}
               )'''
        )
