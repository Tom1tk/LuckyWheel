"""Season 8 daily bounty system.

Three bounties are selected per user per UTC day from a pool of definitions.
Selection is deterministic per (user_id, date) using a hash seed, ensuring
the same 3 bounties are shown all day regardless of which worker handles
the request. Bounties reset at UTC midnight — incomplete progress is discarded.
"""

import hashlib
from datetime import date


# Bounty definitions (from spec S8). Each has an id, description, tracking
# metric, and target.
BOUNTY_DEFS = [
    {
        'id': 'bounty_wager5',
        'description': 'Win 5 spins at 5x+ stake',
        'metric': 'wager_wins_5x',
        'target': 5,
        'reward_tokens': 100,
    },
    {
        'id': 'bounty_fish10',
        'description': 'Catch 10 fish',
        'metric': 'fish_caught_today',
        'target': 10,
        'reward_tokens': 100,
    },
    {
        'id': 'bounty_jackpot',
        'description': 'Land a jackpot in any mode',
        'metric': 'jackpots_today',
        'target': 1,
        'reward_tokens': 100,
    },
    {
        'id': 'bounty_prestige',
        'description': 'Prestige once',
        'metric': 'prestige_today',
        'target': 1,
        'reward_tokens': 100,
    },
    {
        'id': 'bounty_mirror',
        'description': 'Win 3 mirror-mode doubles',
        'metric': 'mirror_wins_today',
        'target': 3,
        'reward_tokens': 100,
    },
    {
        'id': 'bounty_streak10',
        'description': 'Reach a 10-spin win streak',
        'metric': 'max_streak_today',
        'target': 10,
        'reward_tokens': 100,
    },
    {
        'id': 'bounty_bank',
        'description': 'Bank winnings 3 times',
        'metric': 'banks_today',
        'target': 3,
        'reward_tokens': 100,
    },
    {
        'id': 'bounty_double',
        'description': 'Win 2 double-downs',
        'metric': 'double_downs_won_today',
        'target': 2,
        'reward_tokens': 100,
    },
]


def get_daily_bounties(user_id, bounty_date=None):
    """Return 3 bounty definitions for this user on this date.

    Selection is deterministic per (user_id, date).
    """
    if bounty_date is None:
        bounty_date = date.today()

    # Deterministic seed from user_id + date
    seed_str = f'{user_id}:{bounty_date.isoformat()}'
    seed_hash = hashlib.md5(seed_str.encode()).hexdigest()
    seed_int = int(seed_hash, 16)

    # Select 3 distinct bounties from the pool
    pool = list(BOUNTY_DEFS)
    selected = []
    remaining = seed_int
    available = list(range(len(pool)))

    for _ in range(3):
        idx = remaining % len(available)
        chosen_pos = available.pop(idx)
        selected.append(pool[chosen_pos])
        remaining = remaining // len(available) if available else 0

    return selected


def increment_bounty(conn, user_id, bounty_id, bounty_date, amount=1):
    """Increment progress for a bounty. Returns the updated progress row."""
    import psycopg2.extras

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            '''INSERT INTO bounty_progress (user_id, bounty_date, bounty_id, progress)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (user_id, bounty_date, bounty_id)
               DO UPDATE SET progress = bounty_progress.progress + %s
               RETURNING *''',
            (user_id, bounty_date, bounty_id, amount, amount),
        )
        row = cur.fetchone()

        # Mark completed if target reached
        bounty_def = next((b for b in BOUNTY_DEFS if b['id'] == bounty_id), None)
        if bounty_def and row['progress'] >= bounty_def['target'] and not row['completed']:
            cur.execute(
                '''UPDATE bounty_progress
                   SET completed = TRUE, completed_at = NOW()
                   WHERE user_id = %s AND bounty_date = %s AND bounty_id = %s
                   RETURNING *''',
                (user_id, bounty_date, bounty_id),
            )
            row = cur.fetchone()

    return row


def get_bounty_status(conn, user_id, bounty_date=None):
    """Return today's 3 bounties with current progress for this user."""
    if bounty_date is None:
        bounty_date = date.today()

    selected = get_daily_bounties(user_id, bounty_date)
    result = []

    import psycopg2.extras

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for b in selected:
            cur.execute(
                '''SELECT progress, completed, completed_at
                   FROM bounty_progress
                   WHERE user_id = %s AND bounty_date = %s AND bounty_id = %s''',
                (user_id, bounty_date, b['id']),
            )
            row = cur.fetchone()
            result.append({
                'id': b['id'],
                'description': b['description'],
                'target': b['target'],
                'progress': row['progress'] if row else 0,
                'completed': row['completed'] if row else False,
                'reward_tokens': b['reward_tokens'],
            })

    return result


def get_claim_rewards(conn, user_id, bounty_date=None):
    """Return a dict of rewards for the given user on the given date.

    Rewards are based on how many of today's 3 bounties are completed:
    | 1 bounty | 100 tokens, 0 fragments |
    | 2 bounties | 250 tokens, 0 fragments |
    | 3 bounties (all) | 500 tokens, 1 fragment |
    """
    if bounty_date is None:
        bounty_date = date.today()
    import psycopg2.extras
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            '''SELECT COUNT(*) AS cnt FROM bounty_progress
               WHERE user_id = %s AND bounty_date = %s AND completed = TRUE''',
            (user_id, bounty_date),
        )
        row = cur.fetchone()
        completed_count = row['cnt'] if row else 0
    tokens, fragments = {
        3: (500, 1),
        2: (250, 0),
        1: (100, 0),
    }.get(completed_count, (0, 0))
    return {'tokens': tokens, 'cosmetic_fragments': fragments}
