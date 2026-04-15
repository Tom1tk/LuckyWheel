import logging
from datetime import datetime, timezone, timedelta

import psycopg2.extras

log = logging.getLogger('wheel')


def ensure_current_season(conn):
    """
    Check if the current season has expired. If so, perform rollover atomically.

    Uses a non-locking read for the fast path (active season), and FOR UPDATE
    only when a rollover is needed — avoiding lock contention on every request.

    Returns dict: {season_number, ends_at}
    """
    now = datetime.now(timezone.utc)

    # Fast path: non-locking read
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT id, season_number, started_at, ends_at FROM seasons ORDER BY id LIMIT 1'
        )
        season = cur.fetchone()

    if season is None:
        return {'season_number': 1, 'ends_at': None}

    if now < season['ends_at']:
        return {
            'season_number': season['season_number'],
            'ends_at': season['ends_at'].isoformat(),
        }

    # Season may be expired — take exclusive lock and re-check
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT id, season_number, started_at, ends_at FROM seasons ORDER BY id LIMIT 1 FOR UPDATE'
        )
        season = cur.fetchone()

    now = datetime.now(timezone.utc)
    if now < season['ends_at']:
        # Another worker already rolled over while we waited for the lock
        conn.commit()  # release the lock; no writes have been made
        return {
            'season_number': season['season_number'],
            'ends_at': season['ends_at'].isoformat(),
        }

    # We hold the lock and season is still expired — perform rollover
    _perform_rollover(conn, season)  # commits internally

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute('SELECT season_number, ends_at FROM seasons ORDER BY id LIMIT 1')
        updated = cur.fetchone()

    return {
        'season_number': updated['season_number'],
        'ends_at': updated['ends_at'].isoformat(),
    }


def _perform_rollover(conn, season):
    """
    Advance the season by one or more weeks until ends_at is in the future.
    Snapshots top 5, records all users' final stats, resets game_state.
    Commits at the end.
    """
    now = datetime.now(timezone.utc)
    season_id = season['id']
    current_number = season['season_number']
    ends_at = season['ends_at']

    while ends_at <= now:
        log.info('SEASON_ROLLOVER_START  season=%s', current_number)

        # Snapshot top 3 players (permanent record for every season)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                '''SELECT gs.user_id, u.username, gs.wins, gs.losses
                   FROM game_state gs
                   JOIN users u ON u.id = gs.user_id
                   ORDER BY gs.wins DESC
                   LIMIT 3'''
            )
            top3 = cur.fetchall()

        with conn.cursor() as cur:
            for pos, row in enumerate(top3, 1):
                cur.execute(
                    '''INSERT INTO season_snapshots
                           (season_number, position, user_id, username, wins, losses)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (season_number, position) DO NOTHING''',
                    (current_number, pos, row['user_id'], row['username'],
                     row['wins'], row['losses']),
                )

        # Record all users' final stats for per-season history
        with conn.cursor() as cur:
            cur.execute(
                '''INSERT INTO user_season_history
                       (user_id, season_number, finishing_position, final_wins, final_losses)
                   SELECT gs.user_id, %s, NULL, gs.wins, gs.losses
                   FROM game_state gs
                   ON CONFLICT (user_id, season_number) DO NOTHING''',
                (current_number,),
            )
            for pos, row in enumerate(top3, 1):
                cur.execute(
                    '''UPDATE user_season_history
                       SET finishing_position = %s
                       WHERE user_id = %s AND season_number = %s''',
                    (pos, row['user_id'], current_number),
                )

        # Advance season
        next_number = current_number + 1
        next_starts = ends_at
        next_ends = ends_at + timedelta(days=7)

        # Reset all game_state rows; auto-grant the new season's page theme
        new_theme = f'page_season{next_number}'
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE game_state SET
                       wins = 0, losses = 0, fish_clicks = 0, streak = 0, best_streak = 0,
                       owned_items = %s, equipped_fish = 'default',
                       shield_charges = 0, regen_recharge_wins = 0,
                       active_cosmetics = %s, spin_count = 0, win_count = 0, loss_count = 0,
                       total_fish_clicks = 0,
                       winmult_inf_level = 0, bonusmult_inf_level = 0, clickmult_inf_level = 0""",
                ([new_theme], [new_theme]),
            )

        with conn.cursor() as cur:
            cur.execute(
                '''UPDATE seasons
                   SET season_number = %s, started_at = %s, ends_at = %s
                   WHERE id = %s''',
                (next_number, next_starts, next_ends, season_id),
            )

        log.info('SEASON_ROLLOVER_DONE  old_season=%s  new_season=%s', current_number, next_number)
        current_number = next_number
        ends_at = next_ends

    # Force WAL flush for this critical once-per-week transaction.
    # All other commits use the server-level synchronous_commit=off for performance.
    with conn.cursor() as cur:
        cur.execute("SET LOCAL synchronous_commit = on")
    conn.commit()


def get_season_info(conn):
    """
    Return current season info + previous season's top-5 winners.
    Read-only — no locks.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute('SELECT season_number, ends_at FROM seasons ORDER BY id LIMIT 1')
        season = cur.fetchone()

    if season is None:
        return {'season_number': 1, 'ends_at': None, 'latest_winners': []}

    prev = season['season_number'] - 1
    latest_winners = []

    if prev >= 1:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                '''SELECT position, username, wins, losses
                   FROM season_snapshots
                   WHERE season_number = %s
                   ORDER BY position''',
                (prev,),
            )
            latest_winners = [
                {
                    'position': r['position'],
                    'username': r['username'],
                    'wins': int(r['wins']),
                    'losses': r['losses'],
                }
                for r in cur.fetchall()
            ]

    return {
        'season_number': season['season_number'],
        'ends_at': season['ends_at'].isoformat() if season['ends_at'] else None,
        'latest_winners': latest_winners,
    }
