"""Season 8 community goals — replaces the community_pot system.

One goal is active per week, selected by ``week_number % len(COMMUNITY_GOAL_DEFS)``.
All players contribute; on completion, all participants receive a reward.
Contribution is capped per player so one whale cannot solo it.
"""

import psycopg2.extras

import chat
import chat_triggers


COMMUNITY_GOAL_DEFS = [
    {
        'goal_id': 'goal_fish5000',
        'description': 'Catch 5,000 fish server-wide',
        'target': 5000,
        'per_player_cap': 500,
        'metric': 'fish_caught',
        'reward_tokens': 500,
        'reward_fragments': 1,
    },
    {
        'goal_id': 'goal_jackpot500',
        'description': 'Land 500 jackpots server-wide',
        'target': 500,
        'per_player_cap': 50,
        'metric': 'jackpots_landed',
        'reward_tokens': 500,
        'reward_fragments': 1,
    },
    {
        'goal_id': 'goal_prestige50',
        'description': 'Prestige 50 times server-wide',
        'target': 50,
        'per_player_cap': 10,
        'metric': 'prestiges',
        'reward_tokens': 500,
        'reward_fragments': 1,
    },
    {
        'goal_id': 'goal_wager100k',
        'description': 'Wager 100k wins total server-wide',
        'target': 100_000,
        'per_player_cap': 15_000,
        'metric': 'wins_wagered',
        'reward_tokens': 500,
        'reward_fragments': 1,
    },
    {
        'goal_id': 'goal_species100',
        'description': 'Catch 100 unique species server-wide',
        'target': 100,
        'per_player_cap': 15,
        'metric': 'unique_species',
        'reward_tokens': 500,
        'reward_fragments': 1,
    },
]


def get_active_goal(conn, season_number, week_number):
    """Return the active community goal row, creating it if needed.

    The goal is selected by ``week_number % len(COMMUNITY_GOAL_DEFS)``.
    """
    goal_def = COMMUNITY_GOAL_DEFS[week_number % len(COMMUNITY_GOAL_DEFS)]
    goal_id = goal_def['goal_id']

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            '''SELECT * FROM community_goals
               WHERE season_number = %s AND week_number = %s''',
            (season_number, week_number),
        )
        row = cur.fetchone()

        if row is None:
            cur.execute(
                '''INSERT INTO community_goals (goal_id, season_number, week_number, target)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (season_number, week_number) DO NOTHING
                   RETURNING *''',
                (goal_id, season_number, week_number, goal_def['target']),
            )
            row = cur.fetchone()

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
               RETURNING current, target, milestone_25, milestone_50, milestone_75''',
            (actual_amount, goal_id),
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
                        chat.post_system_message(
                            conn, msg, 'system',
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
            tokens_per_player = goal_def.get('reward_tokens', 500)
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
                           SET wager_tokens = wager_tokens + %s,
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
