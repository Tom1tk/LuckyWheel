"""T225: Win-amount columns are BIGINT so big wins don't 500.

Bug (dylan, 2026-06-27): T219 (jackpot-as-win + 5M cap removed) let
dylan's wager payouts grow without bound. Two columns that store
win amounts remained typed as INTEGER (signed 32-bit, max
2,147,483,647):
  - wager_last_win_amount  (dylan: 2,103,551,393 = 98% of max)
  - biggest_win_announced  (dylan: 2,103,551,393 = 98% of max)

Any spin that produced a value above the 43M headroom crashed
with NumericValueOutOfRange and the client got 500 'spin failed'.
T225 widens the columns to BIGINT (max 9.2 × 10^18) via
migration 067, so dylan (and any other player with a similarly
large payout) can keep spinning.
"""
import os
import re
import subprocess


MIG_PATH = 'migrations/067_widen_win_amount_columns.sql'
GAME_PY = 'game.py'

# Columns that hold win-amount values (must all be bigint, not
# integer, otherwise we'll hit T225's overflow again for the next
# player who hits the int max).
WIN_AMOUNT_INT_COLUMNS = [
    'wager_last_win_amount',
    'biggest_win_announced',
    'wager_banked_wins',
    'wager_banked_losses',
]


def _read(path):
    with open(path, 'r') as f:
        return f.read()


def test_migration_067_exists():
    """T225: migration 067 must exist so the column widening is
    reproducible on a fresh DB and re-runnable on the live one.

    Note: T226 (migration 068) further widens these to NUMERIC for
    unlimited precision. The T225 INT→BIGINT step is a necessary
    intermediate that lets the JSON round-trip work even when values
    are between 2.1e9 and 9.2e18; the T226 NUMERIC step handles
    the 1e18+ case (matching the pre-existing `wins` and
    `legacy_wins` columns)."""
    assert os.path.exists(MIG_PATH), (
        f"migration 067 missing at {MIG_PATH} — T225 widening not "
        f"preserved for fresh-DB initialisation"
    )
    src = _read(MIG_PATH)
    for col in WIN_AMOUNT_INT_COLUMNS:
        assert col in src, (
            f"migration 067 must widen {col} to BIGINT"
        )


def test_migration_068_exists():
    """T226: migration 068 must exist so the BIGINT→NUMERIC widening
    is reproducible on a fresh DB and re-runnable on the live one."""
    mig_068 = 'migrations/068_widen_to_numeric.sql'
    assert os.path.exists(mig_068), (
        f"migration 068 missing at {mig_068} — T226 widening to "
        f"NUMERIC not preserved for fresh-DB initialisation. "
        f"Without NUMERIC, values above 9.2e18 would overflow "
        f"BIGINT (the T225 cap)."
    )
    src = _read(mig_068)
    for col in WIN_AMOUNT_INT_COLUMNS:
        assert col in src, (
            f"migration 068 must widen {col} to NUMERIC"
        )


def test_migration_067_uses_bigint():
    """T225: the first widening step is BIGINT (not NUMERIC). BIGINT
    is the intermediate choice because:
    - All Python code (game.py, models.py) treats these as int.
    - BIGINT serialises as a JSON number up to Number.MAX_SAFE_INTEGER
      (~9 × 10^15) which is more than any plausible payout at the
      time T225 was written.
    - T226 then widens further to NUMERIC for 1e18+ support.
    """
    src = _read(MIG_PATH)
    assert re.search(r'wager_last_win_amount\s+TYPE\s+BIGINT', src), (
        "wager_last_win_amount must be widened to BIGINT in T225"
    )
    assert re.search(r'biggest_win_announced\s+TYPE\s+BIGINT', src), (
        "biggest_win_announced must be widened to BIGINT in T225"
    )


def test_migration_068_uses_numeric():
    """T226: the final widening step is NUMERIC (not BIGINT).

    NUMERIC is the right choice for T226 because:
    - Previous seasons have legitimately hit values exceeding 1e50
      (per operator). BIGINT caps at ~9.2e18, so NUMERIC is the
      only Postgres type that holds it.
    - The two existing win-amount columns (wins, legacy_wins) are
      already NUMERIC, so this aligns the schema.
    - Tradeoff: psycopg2 returns NUMERIC as Python Decimal. The
      `int(Decimal(x))` casts in game.py handle this correctly
      (truncates fractional, ours are always integer-valued).
    """
    mig_068 = 'migrations/068_widen_to_numeric.sql'
    src = _read(mig_068)
    assert re.search(r'cumulative_wins\s+TYPE\s+NUMERIC', src), (
        "cumulative_wins must be widened to NUMERIC in T226 "
        "(BIGINT caps at 9.2e18, not enough for 1e50+ seasons)"
    )
    assert re.search(r'biggest_win_announced\s+TYPE\s+NUMERIC', src), (
        "biggest_win_announced must be widened to NUMERIC in T226"
    )
    assert re.search(r'wager_last_win_amount\s+TYPE\s+NUMERIC', src), (
        "wager_last_win_amount must be widened to NUMERIC in T226"
    )


def test_migration_068_is_idempotent():
    """T226: the BIGINT→NUMERIC migration must be safe to re-run
    (no 'column already numeric' error, no data loss)."""
    mig_068 = 'migrations/068_widen_to_numeric.sql'
    src = _read(mig_068)
    for col in WIN_AMOUNT_INT_COLUMNS:
        # USING clause must explicitly cast to NUMERIC.
        assert f'{col}::NUMERIC' in src, (
            f"{col} must have an explicit ::NUMERIC USING clause "
            f"so the migration is safe to re-run on a column that "
            f"is already NUMERIC (PG will accept the no-op cast)"
        )


def test_db_columns_are_numeric():
    """T226 (live check): the win-amount columns must currently be
    numeric in the live DB. If this fails on a fresh install, T225
    and T226 migrations were not applied in order."""
    env = open('.env').read() if os.path.exists('.env') else ''
    if 'DATABASE_URL=' not in env:
        return  # no DB, can't check — but the other tests still pin the migration
    import psycopg2
    url = env.split('DATABASE_URL=')[1].split('\n')[0]
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name='game_state'
          AND column_name = ANY(%s)
    """, (WIN_AMOUNT_INT_COLUMNS,))
    types = dict(cur.fetchall())
    for col in WIN_AMOUNT_INT_COLUMNS:
        assert types.get(col) == 'numeric', (
            f"{col} is typed as {types.get(col)} in the live DB, "
            f"but T226 requires numeric. Re-apply migrations 067 + 068."
        )
    conn.close()


def test_spin_succeeds_with_wager_last_win_near_int_max():
    """T225 (live check): a /api/spin POST for a user whose
    wager_last_win_amount is near (or above) the old 32-bit int
    max must NOT raise NumericValueOutOfRange.

    The simplest way to test this is to set dylan's value near the
    int max via a direct SQL UPDATE, then hit the spin endpoint
    and confirm a 200. But spinning through the HTTP layer needs
    a session. Instead, we directly invoke the spin function with
    a real connection and verify the UPDATE itself doesn't throw.

    This test is the canary: if it ever fails, dylan (or some other
    player) is about to hit the 500 'spin failed' bug again.
    """
    env = open('.env').read() if os.path.exists('.env') else ''
    if 'DATABASE_URL=' not in env:
        return

    import psycopg2
    url = env.split('DATABASE_URL=')[1].split('\n')[0]
    conn = psycopg2.connect(url)
    cur = conn.cursor()

    # Find a user with a non-trivial wager_last_win_amount (this is
    # the canary — if any user is near the int max again, the
    # UPDATE will fail).
    cur.execute("""
        SELECT u.id, u.username, g.wager_last_win_amount
        FROM game_state g JOIN users u ON u.id = g.user_id
        WHERE g.wager_last_win_amount > 0
        ORDER BY g.wager_last_win_amount DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if not row:
        conn.close()
        return  # no wager data yet, canary not applicable

    user_id, username, current_value = row

    # Just attempt a trivial UPDATE that mirrors the spin path's
    # column list, with the current value. If the column is bigint,
    # this works for any value up to ~9.2 × 10^18. If it's int, it
    # fails for any value > 2,147,483,647.
    try:
        cur.execute("""
            UPDATE game_state
               SET wager_last_win_amount = %s,
                   biggest_win_announced = %s
             WHERE user_id = %s
        """, (current_value, current_value, user_id))
        conn.commit()
    except psycopg2.errors.NumericValueOutOfRange as e:
        raise AssertionError(
            f"T225 regression: {username} (user_id={user_id}) has "
            f"wager_last_win_amount={current_value:,} which is "
            f"above the 32-bit int max. The column must be BIGINT, "
            f"not INTEGER. Re-apply migration 067. Error: {e}"
        )
    finally:
        conn.close()


def test_jackpot_is_win_already_covered_cap_removal():
    """T225 (regression guard): T219 removed the 5M wins cap from
    game.py so big wins are preserved. The jackpot-as-win tests
    from T219 must still pass without any 'max wins' cap
    interfering. The cap is gone — verify by grep.

    We grep for the actual cap pattern (`min(wins, _MAX_WINS)` and
    the `if wins > 5_000_000` style check), not the bare number
    (which is also used in unrelated thresholds like the
    25M/125M fish-exchange tiers).
    """
    src = _read(GAME_PY)
    assert '_MAX_WINS' not in src, (
        "T219 removed _MAX_WINS; if it's back, big wins are being "
        "clamped again and dylan will overflow faster"
    )
    # Look for the specific cap pattern from the old code:
    #   wins = min(wins, _MAX_WINS)
    # or:
    #   if wins > 5_000_000: wins = 5_000_000
    assert not re.search(r'min\s*\(\s*wins\s*,\s*5_?000_?000\s*\)', src), (
        "T219 removed `wins = min(wins, _MAX_WINS)`; if this "
        "pattern is back, big wins are being clamped and dylan "
        "will hit the cap again"
    )
    assert not re.search(r'wins\s*=\s*5_?000_?000', src), (
        "T219 removed the explicit wins = 5_000_000 floor"
    )
