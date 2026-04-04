import logging
import re
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
    r'\bc[u*]nt\b',
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
def get_chat():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''SELECT id, username, message, created_at
                   FROM chat_messages
                   ORDER BY id DESC
                   LIMIT 30'''
            )
            rows = cur.fetchall()
    # Reverse so oldest is first
    rows = list(reversed(rows))
    messages = [
        {
            'id': r[0],
            'username': r[1],
            'message': r[2],
            'created_at': r[3].isoformat(),
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
                'INSERT INTO chat_messages (user_id, username, message) VALUES (%s, %s, %s)',
                (current_user.id, current_user.username, message),
            )
            # Trim to 50 most recent messages
            cur.execute(
                '''DELETE FROM chat_messages
                   WHERE id NOT IN (
                       SELECT id FROM chat_messages ORDER BY id DESC LIMIT 50
                   )'''
            )
        conn.commit()

    return jsonify({'ok': True}), 201
