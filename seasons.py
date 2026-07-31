import logging
from datetime import datetime, timezone, timedelta

import psycopg2.extras

log = logging.getLogger('wheel')


def ensure_current_season(conn):
    """
    Return current season info. Never auto-advances — call advance_season() explicitly.

    Returns dict: {season_number, player_facing_number, ends_at, season_name}
    T238: also fetches `name` so callers that need both this shape and
    get_season_info's `season_name` field can avoid a second `seasons` read.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT season_number, name, player_facing_number, ends_at '
            'FROM seasons ORDER BY id LIMIT 1'
        )
        season = cur.fetchone()

    if season is None:
        return {
            'season_number': 1,
            'season_name': '1',
            'player_facing_number': None,
            'ends_at': None,
        }

    now = datetime.now(timezone.utc)
    if season['ends_at'] and now >= season['ends_at']:
        log.warning('SEASON_EXPIRED  season=%s  ended=%s  (advance manually)',
                    season['season_number'], season['ends_at'].isoformat())

    return {
        'season_number': season['season_number'],
        'season_name': season['name'] or str(season['season_number']),
        'player_facing_number': season['player_facing_number'],
        'ends_at': season['ends_at'].isoformat() if season['ends_at'] else None,
    }


def advance_season(conn, player_facing_number=None):
    """
    Manually advance the season. Snapshots current standings, resets game_state,
    and bumps season_number + ends_at by 7 days. Commits internally.
    Call this explicitly — never called automatically.

    `player_facing_number` (T212) sets the new row's player-facing
    season number. If None, the new row inherits
    `current.player_facing_number + 1` (falling back to
    `season_number + 1` for legacy rows predating migration 055). The
    admin endpoint can pass an explicit value for sub-seasons (e.g.
    8.1 once the column is widened to NUMERIC) or for any
    non-monotonic transition.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            'SELECT id, season_number, player_facing_number, started_at, ends_at '
            'FROM seasons ORDER BY id LIMIT 1 FOR UPDATE'
        )
        season = cur.fetchone()

    if season is None:
        conn.rollback()
        raise RuntimeError('No season row found')

    now = datetime.now(timezone.utc)
    season_id = season['id']
    current_number = season['season_number']
    next_number = current_number + 1
    next_starts = now
    next_ends = now + timedelta(days=7)

    if player_facing_number is None:
        # T212: default to current + 1 so the player-facing number
        # advances monotonically. Legacy rows (player_facing_number
        # IS NULL) fall back to season_number + 1.
        pfn_base = season['player_facing_number']
        if pfn_base is None:
            pfn_base = season['season_number']
        next_player_facing_number = pfn_base + 1
    else:
        next_player_facing_number = player_facing_number

    log.info('SEASON_ROLLOVER_START  season=%s  next_pfn=%s',
             current_number, next_player_facing_number)

    # Snapshot top 3 players (permanent record for every season).
    # T241: filter out test users (127.0.0.1) so a future rollover doesn't
    # freeze a pytest fixture into the permanent season_snapshots table
    # (the "winners" tab in the leaderboard reads from there).
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            '''SELECT gs.user_id, u.username, gs.wins, gs.losses
               FROM game_state gs
               JOIN users u ON u.id = gs.user_id
               WHERE u.ip_address <> '127.0.0.1'
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

    # Record all users' final stats for per-season history (full snapshot — fully reversible)
    with conn.cursor() as cur:
        cur.execute(
            '''INSERT INTO user_season_history (
                   user_id, season_number, finishing_position,
                   final_wins, final_losses, final_fish_clicks,
                   winmult_inf_level, bonusmult_inf_level, clickmult_inf_level,
                   streak_armor_level, lure_mastery_level, jackpot_resonance_level,
                   echo_amp_level, proc_streak_level,
                   owned_items, active_cosmetics, equipped_fish, equipped_class,
                   wager_streak, wager_last_stake, wager_banked_wins, wager_banked_losses,
                   insurance_charges, insurance_armed, wager_last_win_amount,
                   insurance_tokens, double_down_pending, active_wheel_mode,
                   guard_charges, guard_last_regen_spin,
                   resilience_last_use_spin, legacy_wins, prestige_level, prestige_count,
                   cumulative_wins, gravity_drift, biggest_win_announced,
                   cosmetic_fragments, bounty_claimed_date, catch_of_the_day_date,
                   insurance_free_claimed_date, insurance_unlock_grant_given,
                   onboarding_step
                )
                SELECT gs.user_id, %s, NULL,
                       gs.wins, gs.losses, gs.fish_clicks,
                       gs.winmult_inf_level, gs.bonusmult_inf_level, gs.clickmult_inf_level,
                       gs.streak_armor_level, gs.lure_mastery_level, gs.jackpot_resonance_level,
                       gs.echo_amp_level, gs.proc_streak_level,
                       gs.owned_items, gs.active_cosmetics, gs.equipped_fish, gs.equipped_class,
                       gs.wager_streak, gs.wager_last_stake, gs.wager_banked_wins, gs.wager_banked_losses,
                       gs.insurance_charges, gs.insurance_armed, gs.wager_last_win_amount,
                       gs.insurance_tokens, gs.double_down_pending, gs.active_wheel_mode,
                       gs.guard_charges, gs.guard_last_regen_spin,
                      gs.resilience_last_use_spin, gs.legacy_wins, gs.prestige_level, gs.prestige_count,
                      gs.cumulative_wins, gs.gravity_drift, gs.biggest_win_announced,
                      gs.cosmetic_fragments, gs.bounty_claimed_date, gs.catch_of_the_day_date,
                      gs.insurance_free_claimed_date, gs.insurance_unlock_grant_given,
                      gs.onboarding_step
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
    new_theme = 'page_season8'  # Casino era — sub-seasons 8.1/8.2 share the S8 theme
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE game_state SET
                   wins = 0, losses = 0, fish_clicks = 0, streak = 0, best_streak = 0,
                   owned_items = %s, equipped_fish = 'default',
                   regen_recharge_wins = 0,
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
                   season_registered = FALSE,
                   -- T218: do NOT carry over prior-season wins into S{N}'s legacy_wins.
                   -- legacy_wins is now a per-season prestige counter, reset to 0 at
                   -- the season boundary. cumulative_wins is the all-time lifetime
                   -- value, used for tier-2/3 unlock gating (T106).
                   legacy_wins = 0,
                   prestige_level = 0, prestige_count = 0,
                    wager_streak = 0, wager_last_stake = 0, double_down_pending = FALSE,
                    wager_banked_wins = 0, insurance_charges = 0,
                    insurance_armed = FALSE,
                    active_wheel_mode = 'steady',
                   guard_charges = 0, guard_last_regen_spin = 0,
                   resilience_last_use_spin = 0,
                   wager_banked_losses = 0,
                   gravity_drift = 0,
                   wager_last_win_amount = 0,
                   biggest_win_announced = 0""",
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
               SET season_number = %s, name = 'Casino',
                   player_facing_number = %s,
                   started_at = %s, ends_at = %s
               WHERE id = %s''',
            (next_number, next_player_facing_number,
             next_starts, next_ends, season_id),
        )

    log.info('SEASON_ROLLOVER_DONE  old_season=%s  new_season=%s  new_pfn=%s',
             current_number, next_number, next_player_facing_number)

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
        cur.execute(
            'SELECT season_number, name, player_facing_number, ends_at '
            'FROM seasons ORDER BY id LIMIT 1'
        )
        season = cur.fetchone()

    if season is None:
        return {'season_number': 1, 'season_name': '1', 'player_facing_number': None,
                'ends_at': None, 'latest_winners': []}

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
        'season_name':   season['name'] or str(season['season_number']),
        'player_facing_number': season['player_facing_number'],
        'ends_at': season['ends_at'].isoformat() if season['ends_at'] else None,
        'latest_winners': latest_winners,
    }


def get_latest_winners(conn, season_number):
    """Return the top finishers of the previous season (or [] for season 1).

    T238: split out from get_season_info so callers that already loaded the
    current season row via ensure_current_season() can avoid a second read
    of the `seasons` table when they only need the winners list.
    """
    prev = season_number - 1
    if prev < 1:
        return []

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            '''SELECT position, username, wins, losses
               FROM season_snapshots
               WHERE season_number = %s
               ORDER BY position''',
            (prev,),
        )
        return [
            {
                'position': r['position'],
                'username': r['username'],
                'wins': int(r['wins']),
                'losses': r['losses'],
            }
            for r in cur.fetchall()
        ]
