"""Season 8 daily bounty system.

Three bounties are selected per user per UTC day from a pool of definitions.
Selection is deterministic per (user_id, date) using a hash seed, ensuring
the same 3 bounties are shown all day regardless of which worker handles
the request. Bounties reset at the UTC 00:00 boundary (a "day" flips at
23:59 the prior day, per operator UX language) — the previous day's
progress is implicitly discarded because `bounty_date` is recomputed
at request time and yesterday's rows are never queried.
"""

import hashlib
import datetime as dt
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
    """Return today's 3 bounties with current progress for this user.

    Each entry uses `bounty_id` as the key (matching the claim handler's
    request body), includes the 1-indexed `position` in the deterministic
    set (used by the claim handler to award position-based tokens), and
    a `claimed` flag (per-bounty; was a single per-day `bounty_claimed_date`
    on game_state before T117).
    """
    if bounty_date is None:
        bounty_date = date.today()

    selected = get_daily_bounties(user_id, bounty_date)
    result = []

    import psycopg2.extras

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for position, b in enumerate(selected, start=1):
            cur.execute(
                '''SELECT progress, completed, completed_at, claimed, claimed_at
                   FROM bounty_progress
                   WHERE user_id = %s AND bounty_date = %s AND bounty_id = %s''',
                (user_id, bounty_date, b['id']),
            )
            row = cur.fetchone()
            result.append({
                'bounty_id': b['id'],
                'description': b['description'],
                'target': b['target'],
                'progress': row['progress'] if row else 0,
                'completed': row['completed'] if row else False,
                'claimed': row['claimed'] if row else False,
                'position': position,
                'reward_tokens': b['reward_tokens'],
            })

    return result


def get_claim_rewards_for_bounty(conn, user_id, bounty_date, bounty_id):
    """Return per-bounty claim rewards for the given (user, date, bounty_id).

    Per-bounty semantics (T117): the token amount is the bounty's 1-indexed
    position in the deterministic 3-bounty set returned by get_daily_bounties.
    Bounty #1 → 1 token, #2 → 2 tokens, #3 → 3 tokens (max 6/day). No
    cosmetic fragments are awarded (T117 removes the legacy 3/3 fragment
    bonus — fragments are now earned only via other paths TBD).
    """
    if bounty_date is None:
        bounty_date = date.today()
    selected = get_daily_bounties(user_id, bounty_date)
    for i, b in enumerate(selected, start=1):
        if b['id'] == bounty_id:
            return {'tokens': i, 'cosmetic_fragments': 0}
    return None


def get_bounty_reset_seconds(now_utc):
    """Seconds until the next UTC 00:00 boundary (called "23:59" in UX).

    The substantive reset is implicit — `bounty_date` is recomputed at
    request time, so yesterday's rows are simply not queried. This helper
    is for an optional UI countdown ("Resets in 4h 32m") and reflects the
    operator's UX framing of the boundary moment.
    """
    boundary = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    if now_utc >= boundary:
        boundary += dt.timedelta(days=1)
    return int((boundary - now_utc).total_seconds())
