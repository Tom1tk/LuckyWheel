import logging
from datetime import datetime, timezone, timedelta

import psycopg2.extras

log = logging.getLogger('wheel')


def ensure_current_season(conn):
    """
    Return current season info. Never auto-advances — call advance_season() explicitly.

    Returns dict: {season_number, ends_at}
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT season_number, ends_at FROM seasons ORDER BY id LIMIT 1'
        )
        season = cur.fetchone()

    if season is None:
        return {'season_number': 1, 'ends_at': None}

    now = datetime.now(timezone.utc)
    if season['ends_at'] and now >= season['ends_at']:
        log.warning('SEASON_EXPIRED  season=%s  ended=%s  (advance manually)',
                    season['season_number'], season['ends_at'].isoformat())

    return {
        'season_number': season['season_number'],
        'ends_at': season['ends_at'].isoformat() if season['ends_at'] else None,
    }


def advance_season(conn):
    """
    Manually advance the season. Snapshots current standings, resets game_state,
    and bumps season_number + ends_at by 7 days. Commits internally.
    Call this explicitly — never called automatically.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT id, season_number, started_at, ends_at FROM seasons ORDER BY id LIMIT 1 FOR UPDATE'
        )
        season = cur.fetchone()

    if season is None:
        conn.rollback()
        raise RuntimeError('No season row found')

    _perform_rollover(conn, season)


def _perform_rollover(conn, season):
    """
    Advance the season by exactly one. Snapshots current standings, resets game_state,
    and sets next ends_at to 7 days from now. Commits at the end.
    """
    now = datetime.now(timezone.utc)
    season_id = season['id']
    current_number = season['season_number']
    next_number = current_number + 1
    next_starts = now
    next_ends = now + timedelta(days=7)

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

    # Reset all game_state rows; auto-grant the new season's page theme.
    # Registered users start spinning from season start; others must join manually.
    new_theme = f'page_season{next_number}'
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE game_state SET
                   wins = 0, losses = 0, fish_clicks = 0, streak = 0, best_streak = 0,
                   owned_items = %s, equipped_fish = 'default',
                   shield_charges = 0, regen_recharge_wins = 0,
                   active_cosmetics = %s, spin_count = 0, win_count = 0, loss_count = 0,
                   total_fish_clicks = 0,
                   winmult_inf_level = 0, bonusmult_inf_level = 0, clickmult_inf_level = 0,
                   streak_armor_level = 0,
                   lure_mastery_level = 0, jackpot_resonance_level = 0,
                   echo_amp_level = 0, proc_streak_level = 0,
                   proc_streak = 0, fish_exchange_total = 0, equipped_class = NULL,
                   dice_charges = 1, dice_last_recharge = NOW(), dice_rolled_since_spin = FALSE,
                   pending_dice = NULL,
                   jackpot_echo_next = FALSE,
                   fishing_cast_at = NULL, fishing_bite_at = NULL,
                   fishing_lucky_next = FALSE, caught_species = '{}',
                   fastest_catch_pct = NULL,
                   auto_spin_since = CASE WHEN season_registered THEN %s ELSE NULL END,
                   last_spin_at    = CASE WHEN season_registered THEN %s ELSE NULL END,
                   season_registered = FALSE""",
            ([new_theme], [new_theme], next_starts, next_starts),
        )

    with conn.cursor() as cur:
        cur.execute(
            '''UPDATE community_pot SET
                   total_contributed = 0, target = 40000, filled = false,
                   filled_at = NULL, fib_prev = 0, win_chance_pct = 51.0,
                   last_decay_check = NOW()
               WHERE id = 1''',
        )

    with conn.cursor() as cur:
        cur.execute(
            '''UPDATE seasons
               SET season_number = %s, started_at = %s, ends_at = %s
               WHERE id = %s''',
            (next_number, next_starts, next_ends, season_id),
        )

    log.info('SEASON_ROLLOVER_DONE  old_season=%s  new_season=%s', current_number, next_number)

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
