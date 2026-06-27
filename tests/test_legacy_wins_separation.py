"""T218: prestige panel "Legacy" badge should show S8-specific amount only.

T218 AC summary:
  A. The rollover in `seasons.py::advance_season()` no longer carries
     prior-season wins into the new season's `legacy_wins`. The new
     season starts with `legacy_wins = 0` for every player.
  B. Migration 059 subtracts the S7.7 carryover (looked up from
     `user_season_history.season_number=8`) from each player's current
     `legacy_wins`, clamped at 0 with `GREATEST(..., 0)`.
  C. The S7.7 final_wins snapshot in `user_season_history` is
     preserved (it's the historical record of the rollover).
  D. `cumulative_wins` is NOT touched by migration 059 — only
     `legacy_wins` is reduced.
  E. Migration 059 is idempotent: re-running it is a no-op.

This file mixes source-level assertions (for the rollover SQL string
and the migration file content) with live-DB tests against the
staging database (using the same rolled-back `conn` fixture as
tests/test_backfill_season8_theme.py). The DB tests set up a
synthetic user_season_history row + game_state row, apply the
migration, verify the result, and let the fixture roll back — so
on-disk state is unchanged after the suite.
"""
import os
import re
import sys
import importlib.util
from pathlib import Path

import psycopg2
import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

STAGING_ENV = Path('/home/user/wheel-app-staging/.env')

MIGRATION_PATH = REPO_ROOT / 'migrations' / '059_legacy_wins_remove_s77_carryover.sql'
SEASONS_PY_PATH = REPO_ROOT / 'seasons.py'
JSX_PATH = REPO_ROOT / 'static' / 'app.jsx'


# ── Source-level plumbing ───────────────────────────────────────────────────

def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _load_seasons():
    """Load the real seasons.py via importlib, bypassing any stub another
    test file may have installed in sys.modules['seasons']."""
    spec = importlib.util.spec_from_file_location(
        '_real_seasons_for_t218',
        str(SEASONS_PY_PATH),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── DB fixture (mirrors tests/test_backfill_season8_theme.py) ───────────────

def _staging_db_url() -> str:
    for line in STAGING_ENV.read_text().splitlines():
        if line.startswith('DATABASE_URL='):
            return line.split('=', 1)[1].strip()
    raise RuntimeError(f'DATABASE_URL not found in {STAGING_ENV}')


@pytest.fixture(scope='module')
def db_url() -> str:
    url = _staging_db_url()
    assert 'wheeldb_staging' in url, (
        f'Refusing to run tests: DATABASE_URL does not look like staging: {url[:60]}'
    )
    return url


@pytest.fixture
def conn(db_url):
    """Yield a staging connection wrapped in a transaction that is always
    rolled back. All on-disk state is unchanged after the suite."""
    c = psycopg2.connect(db_url)
    c.autocommit = False
    try:
        yield c
    finally:
        try:
            c.rollback()
        finally:
            c.close()


def _find_or_create_test_user(conn, suffix: str) -> int:
    """Find or create a dedicated test user (`t218_<suffix>`). The user
    is preserved across test runs (no DELETE), so a stale row from a
    prior session is fine — each test sets up its own state and the
    fixture rolls back at the end."""
    username = f't218_{suffix}'
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM users WHERE username = %s', (username,))
        row = cur.fetchone()
        if row:
            return row[0]
        # `users.password_hash` and `users.ip_address` are NOT NULL —
        # we supply inert placeholders that satisfy the constraint.
        cur.execute(
            'INSERT INTO users (username, password_hash, ip_address, created_at) '
            "VALUES (%s, 't218-test', '127.0.0.1', NOW()) RETURNING id",
            (username,),
        )
        new_id = cur.fetchone()[0]
        cur.execute(
            'INSERT INTO game_state (user_id) VALUES (%s) ON CONFLICT DO NOTHING',
            (new_id,),
        )
        return new_id


def _set_legacy_and_history(cur, user_id: int, *,
                            legacy_wins, cumulative_wins,
                            ush_final_wins=None, clear_ush_row=False) -> None:
    """Force a player's game_state + user_season_history to a known state."""
    cur.execute(
        "UPDATE game_state SET legacy_wins = %s, cumulative_wins = %s "
        "WHERE user_id = %s",
        (legacy_wins, cumulative_wins, user_id),
    )
    if clear_ush_row:
        cur.execute(
            "DELETE FROM user_season_history "
            "WHERE user_id = %s AND season_number = 8",
            (user_id,),
        )
    elif ush_final_wins is not None:
        cur.execute(
            "INSERT INTO user_season_history (user_id, season_number, final_wins, final_losses) "
            "VALUES (%s, 8, %s, 0) "
            "ON CONFLICT (user_id, season_number) DO UPDATE SET final_wins = EXCLUDED.final_wins",
            (user_id, ush_final_wins),
        )


# ── Source-level tests (no DB) ──────────────────────────────────────────────

def test_migration_059_exists_and_non_empty():
    """Migration 059 must exist and contain a non-trivial UPDATE."""
    assert MIGRATION_PATH.exists(), (
        f"migration file missing: {MIGRATION_PATH}. Create it with the "
        f"T218 UPDATE that subtracts user_season_history.final_wins "
        f"from game_state.legacy_wins."
    )
    body = _read(MIGRATION_PATH)
    assert body.strip(), "migration 059 is empty"


def test_migration_059_subtracts_ush_final_wins():
    """The migration's UPDATE must reference `user_season_history` and
    use `ush.final_wins` (or equivalent) as the value subtracted from
    `legacy_wins`."""
    body = _read(MIGRATION_PATH)
    assert re.search(r'UPDATE\s+game_state\b', body, re.IGNORECASE), (
        "migration 059 must UPDATE game_state"
    )
    assert 'user_season_history' in body, (
        "migration 059 must source the S7.7 carryover from user_season_history"
    )
    assert re.search(r'final_wins', body), (
        "migration 059 must reference the final_wins column"
    )
    # Must subtract (not just SET to 0 — that would also zero out the
    # S8-specific amount, which is the bug we're avoiding).
    assert re.search(r'legacy_wins\s*-\s*', body), (
        "migration 059 must SUBTRACT the carryover, not just zero legacy_wins"
    )
    # season_number=8 is the lookup key for the S7.7 row.
    assert re.search(r'season_number\s*=\s*8', body), (
        "migration 059 must filter user_season_history by season_number = 8"
    )


def test_migration_059_clamps_at_zero():
    """`GREATEST(..., 0)` ensures legacy_wins never goes negative, even
    if a user has somehow underflowed."""
    body = _read(MIGRATION_PATH)
    assert re.search(r'GREATEST\s*\(', body, re.IGNORECASE), (
        "migration 059 must clamp legacy_wins with GREATEST(..., 0)"
    )


def test_migration_059_idempotent_via_where_clause():
    """Idempotency guard: the UPDATE must have a WHERE clause that
    restricts the rowset to users that still have the S7.7 carryover
    present. Without this, a second run would zero out the S8-specific
    amount (3,736,603 - 297,836,900,436 = negative, GREATEST → 0)."""
    body = _read(MIGRATION_PATH)
    # Find the outer UPDATE statement.
    m = re.search(
        r'UPDATE\s+game_state\s+\w+\s+SET\s+.*?(?:\)|;)\s*WHERE\s+([^;]+)',
        body, re.IGNORECASE | re.DOTALL,
    )
    assert m, (
        "migration 059 must have a WHERE clause on the UPDATE — without "
        "it, a re-run would zero out the S8-specific amount and the "
        "migration is not idempotent."
    )
    where_clause = m.group(1)
    # The WHERE clause must reference `legacy_wins >` and a final_wins
    # lookup, so that already-corrected rows fail the predicate.
    assert 'legacy_wins' in where_clause.lower(), (
        f"WHERE clause must reference legacy_wins to gate the update; got: {where_clause}"
    )
    assert re.search(r'>\s*', where_clause), (
        f"WHERE clause must use a strict-greater-than comparison to "
        f"make the update idempotent; got: {where_clause}"
    )
    assert 'final_wins' in where_clause or 'COALESCE' in where_clause, (
        f"WHERE clause must compare against the S7.7 carryover value "
        f"(final_wins or its COALESCE fallback); got: {where_clause}"
    )


def test_migration_059_does_not_touch_ush_or_cumulative_wins():
    """The migration only writes to game_state.legacy_wins — it must
    NOT delete or modify user_season_history rows, and it must NOT
    touch game_state.cumulative_wins."""
    body = _read(MIGRATION_PATH)
    # No DELETE on user_season_history
    assert not re.search(r'DELETE\s+FROM\s+user_season_history', body, re.IGNORECASE), (
        "migration 059 must NOT delete from user_season_history (it's "
        "the historical record of the rollover)"
    )
    # No UPDATE on user_season_history
    assert not re.search(r'UPDATE\s+user_season_history', body, re.IGNORECASE), (
        "migration 059 must NOT update user_season_history"
    )
    # No reference to cumulative_wins as a target of a write
    assert not re.search(r'cumulative_wins\s*=', body, re.IGNORECASE), (
        "migration 059 must NOT modify cumulative_wins (lifetime value)"
    )


def test_seasons_py_rollover_resets_legacy_wins():
    """seasons.py:155 (the legacy_wins assignment in the rollover's
    `UPDATE game_state` block) must reset legacy_wins to 0, not
    accumulate `legacy_wins + wins`."""
    src = _read(SEASONS_PY_PATH)
    # Pull the UPDATE game_state block (regex is loose because the SQL
    # is wrapped across many lines and there's a trailing comma list).
    m = re.search(
        r'UPDATE\s+game_state\s+SET(.*?)\s*"""\s*,\s*\(\[',
        src, re.IGNORECASE | re.DOTALL,
    )
    assert m, (
        "could not locate `UPDATE game_state SET … \"\"\" , ([` block "
        "in seasons.py — the file structure may have changed; update "
        "this test."
    )
    block = m.group(1)
    # The OLD form was `legacy_wins = legacy_wins + wins,`. The NEW
    # form must be `legacy_wins = 0,`. Both clauses are tested below.
    assert 'legacy_wins = legacy_wins + wins' not in block, (
        "seasons.py still has the OLD `legacy_wins = legacy_wins + wins` "
        "rollover. T218 wants `legacy_wins = 0,` so the new season "
        "starts with a clean prestige counter (no S{N-1} carryover)."
    )
    assert re.search(r'legacy_wins\s*=\s*0\s*,', block), (
        "seasons.py's UPDATE game_state must include `legacy_wins = 0,` "
        "as the new rollover behaviour"
    )


def test_seasons_py_rollover_sql_uses_legacy_wins_equals_zero():
    """Capture-based guard: exercise advance_season() with a stub
    connection and assert the captured `UPDATE game_state` SQL
    contains `legacy_wins = 0` (not `legacy_wins = legacy_wins + wins`)."""
    seasons = _load_seasons()

    class _CapturingCursor:
        def __init__(self):
            self.sql_log = []

        def __enter__(self): return self
        def __exit__(self, *a): return False

        def execute(self, sql, params=None):
            self.sql_log.append(sql)

        def fetchone(self): return {
            'id': 1, 'season_number': 7, 'started_at': None, 'ends_at': None,
        }
        def fetchall(self): return []

    class _FakeConn:
        def __init__(self):
            self._cur = _CapturingCursor()
        def cursor(self, *a, **kw): return self._cur
        def commit(self): pass

    fake = _FakeConn()
    seasons.advance_season(fake)

    update_sql = None
    for sql in fake._cur.sql_log:
        if re.search(r'UPDATE\s+game_state\b', sql, re.IGNORECASE):
            update_sql = sql
            break

    assert update_sql is not None, "advance_season() did not execute an UPDATE game_state"
    assert 'legacy_wins = legacy_wins + wins' not in update_sql, (
        f"advance_season() still uses `legacy_wins = legacy_wins + wins`; "
        f"T218 wants `legacy_wins = 0,`.\nCaptured SQL:\n{update_sql}"
    )
    assert re.search(r'legacy_wins\s*=\s*0\b', update_sql), (
        f"advance_season()'s UPDATE game_state must contain "
        f"`legacy_wins = 0` (reset at rollover).\nCaptured SQL:\n{update_sql}"
    )


def test_panel_format_unchanged():
    """The prestige panel's `legacy-badge` JSX is unchanged by T218 —
    T218 only changes the data behind the badge. The format stays
    `Legacy: {fmt(legacyWins)} wins` (no `Legacy (S8):` prefix; that
    was the optional cosmetic from the ticket's §C and is NOT
    required)."""
    jsx = _read(JSX_PATH)
    assert 'legacy-badge' in jsx, "legacy-badge element must still exist"
    assert 'legacyWins > 0' in jsx, "legacy-badge must still gate on legacyWins > 0"
    assert re.search(r'Legacy:\s*\{fmt\(legacyWins\)\}\s*wins', jsx), (
        "legacy-badge format must remain `Legacy: {fmt(legacyWins)} wins`"
    )


# ── Live DB tests (run against staging, rolled back by fixture) ─────────────

def test_s77_carryover_subtracted(conn):
    """The headline case: a player with S7.7 carryover gets it
    removed, leaving the S8-specific amount.

    Pre:  legacy_wins = 150,000,000  (S7.7 100M + S8 50M)
          user_season_history[season=8].final_wins = 100,000,000
    Post: legacy_wins = 50,000,000   (S8-specific only)"""
    user_id = _find_or_create_test_user(conn, 'carryover')
    with conn.cursor() as cur:
        _set_legacy_and_history(cur, user_id,
            legacy_wins=150_000_000,
            cumulative_wins=999,
            ush_final_wins=100_000_000,
        )
        cur.execute(_read(MIGRATION_PATH))

        cur.execute(
            "SELECT legacy_wins FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        (legacy_wins,) = cur.fetchone()
        assert legacy_wins == 50_000_000, (
            f"expected legacy_wins = 50,000,000 (S8-specific), got {legacy_wins}"
        )


def test_legacy_wins_never_negative(conn):
    """A user with no S7.7 row in user_season_history: migration 059
    must leave their legacy_wins untouched (the WHERE clause skips
    them, and the COALESCE(..., 0) fallback gives no carryover)."""
    user_id = _find_or_create_test_user(conn, 'nos77')
    with conn.cursor() as cur:
        _set_legacy_and_history(cur, user_id,
            legacy_wins=0,
            cumulative_wins=0,
            clear_ush_row=True,
        )
        cur.execute(_read(MIGRATION_PATH))

        cur.execute(
            "SELECT legacy_wins FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        (legacy_wins,) = cur.fetchone()
        assert legacy_wins == 0, (
            f"new S8 player (no S7.7 history) must stay at legacy_wins = 0, "
            f"got {legacy_wins}"
        )


def test_legacy_wins_underflow_row_excluded(conn):
    """If a user has `legacy_wins < S7.7 carryover` (e.g. a manual
    edit, or some future state), the migration's WHERE clause
    excludes the row entirely — the carryover is not in legacy_wins
    to remove, so there is nothing to do. The GREATEST(..., 0) clamp
    is a belt-and-suspenders safety net for the rare case where the
    row passes the WHERE clause but the subtraction would underflow
    (not exercised in normal operation)."""
    user_id = _find_or_create_test_user(conn, 'underflow')
    with conn.cursor() as cur:
        _set_legacy_and_history(cur, user_id,
            legacy_wins=50,                  # tiny — smaller than carryover
            cumulative_wins=999,
            ush_final_wins=100_000_000,      # S7.7 wins = 100M
        )
        cur.execute(_read(MIGRATION_PATH))

        cur.execute(
            "SELECT legacy_wins FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        (legacy_wins,) = cur.fetchone()
        # The row is excluded by the WHERE clause (50 < 100M), so
        # legacy_wins is unchanged.
        assert legacy_wins == 50, (
            f"underflow row must be excluded by the WHERE clause "
            f"(legacy_wins < carryover means there's nothing to remove); "
            f"got {legacy_wins}"
        )


def test_migration_idempotent(conn):
    """Re-running migration 059 must be a no-op. Setup state, run
    once, capture legacy_wins. Run a second time, assert it is
    unchanged."""
    user_id = _find_or_create_test_user(conn, 'idempotent')
    with conn.cursor() as cur:
        _set_legacy_and_history(cur, user_id,
            legacy_wins=150_000_000,
            cumulative_wins=999,
            ush_final_wins=100_000_000,
        )
        migration_sql = _read(MIGRATION_PATH)

        # First run
        cur.execute(migration_sql)
        cur.execute(
            "SELECT legacy_wins FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        (first,) = cur.fetchone()
        assert first == 50_000_000, (
            f"first run expected 50,000,000, got {first}"
        )

        # Second run — must not change anything
        cur.execute(migration_sql)
        cur.execute(
            "SELECT legacy_wins FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        (second,) = cur.fetchone()
        assert second == first, (
            f"second run changed legacy_wins: {first} → {second} "
            f"(migration is not idempotent)"
        )


def test_cumulative_wins_unchanged(conn):
    """Migration 059 must not touch cumulative_wins — the lifetime
    value is preserved; only legacy_wins is reduced."""
    user_id = _find_or_create_test_user(conn, 'cumwins')
    with conn.cursor() as cur:
        _set_legacy_and_history(cur, user_id,
            legacy_wins=150_000_000,
            cumulative_wins=42_000_000,
            ush_final_wins=100_000_000,
        )
        cur.execute(_read(MIGRATION_PATH))

        cur.execute(
            "SELECT cumulative_wins FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        (cum,) = cur.fetchone()
        assert cum == 42_000_000, (
            f"cumulative_wins must be unchanged by migration 059, got {cum}"
        )


def test_user_season_history_preserved(conn):
    """Migration 059 must not touch user_season_history. The S7.7
    final_wins snapshot is the historical record and must remain
    exactly as it was."""
    user_id = _find_or_create_test_user(conn, 'ushkept')
    with conn.cursor() as cur:
        _set_legacy_and_history(cur, user_id,
            legacy_wins=150_000_000,
            cumulative_wins=0,
            ush_final_wins=100_000_000,
        )
        cur.execute(_read(MIGRATION_PATH))

        cur.execute(
            "SELECT final_wins, final_losses FROM user_season_history "
            "WHERE user_id = %s AND season_number = 8",
            (user_id,),
        )
        row = cur.fetchone()
        assert row is not None, "ush[season=8] row was deleted by migration 059"
        final_wins, final_losses = row
        assert final_wins == 100_000_000, (
            f"ush[season=8].final_wins was modified by migration 059: "
            f"got {final_wins}, expected 100,000,000"
        )
        assert final_losses == 0, (
            f"ush[season=8].final_losses was modified by migration 059: "
            f"got {final_losses}, expected 0"
        )
