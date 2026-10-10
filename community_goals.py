"""Season 8 community goals — replaces the community_pot system.

One goal is active at a time. Each new row takes the goal after the most
recent row's goal in COMMUNITY_GOAL_DEFS order (see start_weekly_goal).
All players contribute; on completion, all participants receive a reward.
Contribution is capped per player so one whale cannot solo it.
"""

import psycopg2.extras

import chat
import chat_triggers
from wheel_modes import get_week_number


# per_player_cap is target / 5: five players at cap fill a goal exactly, and
# no single player can give more than 20% of it.
# goal_species100 retired for S9: caught species persist across tides, so
# first catches dry up and the goal becomes unfillable.
COMMUNITY_GOAL_DEFS = [
    {
        'goal_id': 'goal_fish5000',
        'description': 'Catch 1,500 fish server-wide',
        'target': 1500,
        'per_player_cap': 300,
        'metric': 'fish_caught',
        'reward_tokens': 10,
        'reward_fragments': 1,
    },
    {
        'goal_id': 'goal_jackpot500',
        'description': 'Land 100 jackpots server-wide',
        'target': 100,
        'per_player_cap': 20,
        'metric': 'jackpots_landed',
        'reward_tokens': 10,
        'reward_fragments': 1,
    },
    {
        'goal_id': 'goal_wager100k',
        'description': 'Wager 25k wins total server-wide',
        'target': 25_000,
        'per_player_cap': 5_000,
        'metric': 'wins_wagered',
        'reward_tokens': 10,
        'reward_fragments': 1,
    },
]


def _next_goal_def(conn):
    """Return the goal after the most recent row's goal, wrapping around the defs.

    Falls back to the first def when there are no rows, or when the latest
    row's goal has been retired from COMMUNITY_GOAL_DEFS.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute('SELECT goal_id FROM community_goals ORDER BY id DESC LIMIT 1')
        last = cur.fetchone()
    goal_ids = [g['goal_id'] for g in COMMUNITY_GOAL_DEFS]
    if last is None or last['goal_id'] not in goal_ids:
        return COMMUNITY_GOAL_DEFS[0]
    return COMMUNITY_GOAL_DEFS[(goal_ids.index(last['goal_id']) + 1) % len(goal_ids)]


def _insert_goal_row(conn, goal_def, season_number, week_number):
    """Insert the (season, week) row for goal_def and make it the only open goal.

    Returns the new row, or None if that (season, week) already has a row.
    Only a fresh insert closes the other open goals and resets this goal's
    contributions, so a repeat call for the same week cannot wipe live progress.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            '''INSERT INTO community_goals (goal_id, season_number, week_number, target)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (season_number, week_number) DO NOTHING
               RETURNING *''',
            (goal_def['goal_id'], season_number, week_number, goal_def['target']),
        )
        row = cur.fetchone()
        if row is None:
            return None
        # Close the old goals. increment_goal matches on goal_id alone, so an
        # open old row with the same goal_id would take this goal's contributions.
        # completed=TRUE with completed_at NULL means "rotated out, not filled".
        cur.execute(
            '''UPDATE community_goals SET completed = TRUE
               WHERE NOT completed AND id <> %s''',
            (row['id'],),
        )
        # Per-player caps are keyed by goal_id only, so progress restarts here.
        cur.execute(
            'DELETE FROM community_goal_contributions WHERE goal_id = %s',
            (goal_def['goal_id'],),
        )
    return row


def get_active_goal(conn, season_number, week_number):
    """Return ``(row, goal_def)`` for the (season, week) goal, creating it if needed.

    An existing row keeps its own goal (looked up by goal_id), so changing the
    defs never relabels a live row. A row whose goal is retired returns
    ``(None, None)``, which every caller treats as "no goal".
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            # Keyed on the tide (season_number) alone: a Fri-Fri tide spans an
            # ISO-week Monday, and that must not rotate the goal mid-tide.
            '''SELECT * FROM community_goals
               WHERE season_number = %s ORDER BY id DESC LIMIT 1''',
            (season_number,),
        )
        row = cur.fetchone()

    if row is None:
        goal_def = _next_goal_def(conn)
        return _insert_goal_row(conn, goal_def, season_number, week_number), goal_def

    goal_def = next((g for g in COMMUNITY_GOAL_DEFS if g['goal_id'] == row['goal_id']), None)
    return (row, goal_def) if goal_def else (None, None)


def _tide_key(conn):
    """Return (season_number, ISO week) for the goal row a rollover creates.

    Each tide bumps season_number, so the goal is per tide; week_number is
    only stored to satisfy the (season_number, week_number) unique key.
    """
    with conn.cursor() as cur:
        cur.execute('SELECT season_number FROM seasons ORDER BY id LIMIT 1')
        row = cur.fetchone()
    if row is None:
        raise RuntimeError('no seasons row; cannot activate a community goal')
    return row[0], get_week_number()


def start_weekly_goal(conn):
    """Close the open community goal and activate the next one in rotation.

    Call from the tide rollover after advance_season() has bumped the season,
    inside the rollover's transaction. This function does not commit. It is
    not wired into seasons.py; the orchestrator calls it there.

    Returns (row, goal_def) like get_active_goal. If the new (season, week)
    already has a row, that row is returned unchanged.
    """
    season_number, week_number = _tide_key(conn)
    goal_def = _next_goal_def(conn)
    row = _insert_goal_row(conn, goal_def, season_number, week_number)
    if row is None:
        return get_active_goal(conn, season_number, week_number)
    return row, goal_def


def increment_goal(conn, goal_id, user_id, amount):
    """Increment the community goal total and the player's contribution.

    Enforces the per-player cap. Returns the amount actually contributed
    (may be less than requested if the cap is reached).

    After updating, checks for 25/50/75% milestone crossings (T84). Each
    crossed milestone is marked TRUE in community_goals and a system
    message is posted to chat (event_kind=goal_milestone_{25,50,75}).
    The 100% completion is handled by check_goal_completion, not here.
    """
    goal_def = next((g for g in COMMUNITY_GOAL_DEFS if g['goal_id'] == goal_id), None)
    if not goal_def:
        return 0

    cap = goal_def['per_player_cap']

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Ensure the row exists, then lock it before reading -- without the
        # lock, two concurrent calls near the cap could each read the same
        # stale current_contrib and both clamp independently, together
        # pushing the player's total past the cap by up to one extra amount.
        cur.execute(
            '''INSERT INTO community_goal_contributions (goal_id, user_id, contributed)
               VALUES (%s, %s, 0)
               ON CONFLICT (goal_id, user_id) DO NOTHING''',
            (goal_id, user_id),
        )
        cur.execute(
            '''SELECT contributed FROM community_goal_contributions
               WHERE goal_id = %s AND user_id = %s FOR UPDATE''',
            (goal_id, user_id),
        )
        row = cur.fetchone()
        current_contrib = row['contributed'] if row else 0

        # Enforce cap
        remaining_cap = cap - current_contrib
        actual_amount = min(amount, remaining_cap)
        if actual_amount <= 0:
            return 0

        cur.execute(
            '''UPDATE community_goal_contributions
               SET contributed = contributed + %s
               WHERE goal_id = %s AND user_id = %s''',
            (actual_amount, goal_id, user_id),
        )

        # Increment goal total; also fetch the milestone flags so we can
        # detect threshold crossings from the new (post-increment) value.
        cur.execute(
            '''UPDATE community_goals
               SET current = current + %s
               WHERE goal_id = %s AND NOT completed
                 -- test accounts (127.0.0.1) never move the shared goal
                 AND NOT EXISTS (SELECT 1 FROM users WHERE id = %s AND ip_address = '127.0.0.1')
               RETURNING current, target, milestone_25, milestone_50, milestone_75''',
            (actual_amount, goal_id, user_id),
        )
        goal_row = cur.fetchone()

        if goal_row:
            new_current = goal_row['current']
            new_target = goal_row['target']
            if new_target > 0:
                for pct in (25, 50, 75):
                    if not goal_row.get(f'milestone_{pct}', False) and new_current * 100 >= pct * new_target:
                        cur.execute(
                            f'''UPDATE community_goals
                                SET milestone_{pct} = TRUE
                                WHERE goal_id = %s AND NOT milestone_{pct}''',
                            (goal_id,),
                        )
                        msg = chat_triggers.goal_milestone_msg(pct, new_current, new_target)
                        chat.post_dedup_system_message(
                            conn, msg, user_id,
                            event_kind=f'goal_milestone_{pct}',
                        )

    return actual_amount


def check_goal_completion(conn, goal_id):
    """Check if the goal is complete and mark it. Returns True if newly completed.

    On completion, distributes reward_tokens and reward_fragments to all
    players who contributed at least 1 unit to the goal.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            '''UPDATE community_goals
               SET completed = TRUE, completed_at = NOW()
               WHERE goal_id = %s AND current >= target AND NOT completed
               RETURNING *''',
            (goal_id,),
        )
        row = cur.fetchone()

    if row:
        # Find the goal definition for reward info
        goal_def = next((g for g in COMMUNITY_GOAL_DEFS if g['goal_id'] == goal_id), None)
        if goal_def:
            tokens_per_player = goal_def.get('reward_tokens', 10)
            fragments_per_player = goal_def.get('reward_fragments', 1)

            # Distribute rewards to all contributors
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    '''SELECT user_id FROM community_goal_contributions
                       WHERE goal_id = %s AND contributed >= 1''',
                    (goal_id,),
                )
                contributors = cur.fetchall()

                for c in contributors:
                    cur.execute(
                        '''UPDATE game_state
                           SET insurance_tokens = insurance_tokens + %s,
                               cosmetic_fragments = cosmetic_fragments + %s
                           WHERE user_id = %s''',
                        (tokens_per_player, fragments_per_player, c['user_id']),
                    )

        # Activate the community pot buff: +5% win% for 1 week
        with conn.cursor() as cur:
            cur.execute(
                '''UPDATE community_pot
                   SET filled = TRUE, filled_at = NOW(), win_chance_pct = 55.0
                   WHERE id = 1''',
            )

    return row is not None


def get_player_contribution(conn, goal_id, user_id):
    """Return the player's contribution to a goal."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            '''SELECT contributed FROM community_goal_contributions
               WHERE goal_id = %s AND user_id = %s''',
            (goal_id, user_id),
        )
        row = cur.fetchone()
    return row['contributed'] if row else 0
