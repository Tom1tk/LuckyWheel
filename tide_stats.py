"""Per-player, per-tide counters (how stakes, dice and Surge are used).

Surge discarded at the tide turn (seasons.py zeroes surge_spins) is not counted.
"""
import datetime as dt
from zoneinfo import ZoneInfo

COLUMNS = frozenset({
    'manual_spins', 'auto_spins', 'staked_spins', 'stake_pct_sum',
    'staked_wins_gained', 'staked_wins_lost', 'stake_wins_sum',
    'double_downs', 'insurance_used', 'dice_rolls',
    'surge_from_catch', 'surge_from_auto_fish', 'surge_from_catch_up',
    'surge_from_bounty', 'surge_spent',
})

_LONDON = ZoneInfo('Europe/London')


def tide_date(now_utc: dt.datetime) -> dt.date:
    """London date of the Friday 21:00 the current tide turned."""
    d = (now_utc.astimezone(_LONDON) - dt.timedelta(hours=21)).date()
    return d - dt.timedelta(days=(d.weekday() - 4) % 7)


def bump(cur, user_id: int, now_utc: dt.datetime, **deltas: int) -> None:
    """Add deltas to this tide's row (upsert). Zero deltas are dropped; nothing to add -> no query."""
    unknown = set(deltas) - COLUMNS
    if unknown:
        raise ValueError(f'unknown tide_stats column(s): {sorted(unknown)}')
    deltas = {k: v for k, v in deltas.items() if v}
    if not deltas:
        return
    cols = list(deltas)
    cur.execute(
        f'INSERT INTO tide_stats (user_id, tide_date, {", ".join(cols)}) '
        f'VALUES (%s, %s, {", ".join(["%s"] * len(cols))}) '
        'ON CONFLICT (user_id, tide_date) DO UPDATE SET '
        + ', '.join(f'{c} = tide_stats.{c} + EXCLUDED.{c}' for c in cols),
        (user_id, tide_date(now_utc), *deltas.values()),
    )
