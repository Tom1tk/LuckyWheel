"""Tests for bin/backfill_season8_theme.py.

The tests target the live staging DB but always run inside a transaction that
the fixture rolls back, so the on-disk state is unchanged after the suite.
Tests that depend on a specific shape of the data force a row into a known
state and verify the backfill fixes it before rollback.
"""
import os
import sys
from pathlib import Path

import psycopg2
import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'bin'))

import backfill_season8_theme as backfill  # noqa: E402

STAGING_ENV = Path('/home/user/wheel-app-staging/.env')


def _staging_db_url() -> str:
    for line in STAGING_ENV.read_text().splitlines():
        if line.startswith('DATABASE_URL='):
            return line.split('=', 1)[1].strip()
    raise RuntimeError(f'DATABASE_URL not found in {STAGING_ENV}')


@pytest.fixture(scope='module')
def db_url() -> str:
    url = _staging_db_url()
    assert backfill.is_staging_url(url), (
        f'Refusing to run tests: DATABASE_URL does not look like staging: {url[:60]}'
    )
    return url


@pytest.fixture
def conn(db_url):
    """Yield a connection wrapped in a transaction that is always rolled back."""
    c = psycopg2.connect(db_url)
    c.autocommit = False
    try:
        yield c
    finally:
        try:
            c.rollback()
        finally:
            c.close()


def _force_user_missing(cur, user_id: int) -> None:
    """Set a user's owned_items / active_cosmetics to a known missing-the-theme state."""
    cur.execute(
        "UPDATE game_state SET "
        "owned_items = ARRAY['wager_unlock'], "
        "active_cosmetics = ARRAY['confetti_1'] "
        "WHERE user_id = %s",
        (user_id,),
    )


def _pick_any_user(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM game_state LIMIT 1")
        row = cur.fetchone()
        assert row is not None, 'staging game_state is empty'
        return row[0]


# ── Refusal logic (no DB needed) ──────────────────────────────────────────

def test_refuses_main_url():
    assert not backfill.is_staging_url('postgresql://wheelapp@localhost/wheeldb')
    assert not backfill.is_staging_url('postgresql://wheelapp@localhost/wheeldb_production')
    assert not backfill.is_staging_url('')
    assert not backfill.is_staging_url('postgresql://wheelapp@localhost/wheeldbmain')


def test_accepts_staging_url():
    assert backfill.is_staging_url(
        'postgresql://wheelapp:secret@localhost/wheeldb_staging'
    )
    # Marker anywhere in the DSN counts — it is a substring check by design.
    assert backfill.is_staging_url('postgresql://wheelapp@localhost/wheeldb_staging_other')


def test_load_db_url_reads_env_file(tmp_path):
    env_path = tmp_path / '.env'
    env_path.write_text(
        'WHEEL_SECRET_KEY=abc\n'
        'DATABASE_URL=postgresql://wheelapp:secret@localhost/wheeldb_staging\n'
    )
    assert backfill.load_db_url(env_path) == \
        'postgresql://wheelapp:secret@localhost/wheeldb_staging'


def test_load_db_url_falls_back_to_environ(tmp_path, monkeypatch):
    env_path = tmp_path / '.env'  # does not exist on disk
    monkeypatch.setenv('DATABASE_URL', 'postgresql://x/y_wheeldb_staging')
    assert backfill.load_db_url(env_path) == 'postgresql://x/y_wheeldb_staging'


# ── SQL behavior (run against staging in a rolled-back transaction) ───────

def test_grants_and_equips_user_missing_both(conn):
    """A user missing the theme in both arrays is granted + equipped after the UPDATE."""
    with conn.cursor() as cur:
        user_id = _pick_any_user(conn)
        _force_user_missing(cur, user_id)

        cur.execute(
            "SELECT NOT ('page_season8' = ANY(owned_items)), "
            "       NOT ('page_season8' = ANY(active_cosmetics)) "
            "FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        assert cur.fetchone() == (True, True)

        affected = backfill.run_backfill(conn, dry_run=False)
        assert affected >= 1

        cur.execute(
            "SELECT owned_items, active_cosmetics FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        owned, active = cur.fetchone()
        assert 'page_season8' in owned
        assert 'page_season8' in active
        # Idempotent: the UPDATE appends, but the rebuild of active_cosmetics
        # strips any page_season* first, so the result is exactly one copy.
        assert owned.count('page_season8') == 1
        assert active.count('page_season8') == 1


def test_idempotent(conn):
    """Running the UPDATE twice leaves the data unchanged on the second pass."""
    with conn.cursor() as cur:
        user_id = _pick_any_user(conn)
        _force_user_missing(cur, user_id)

        first = backfill.run_backfill(conn, dry_run=False)
        assert first >= 1

        cur.execute(
            "SELECT COUNT(*) FROM game_state "
            "WHERE NOT ('page_season8' = ANY(owned_items)) "
            "   OR NOT ('page_season8' = ANY(active_cosmetics))"
        )
        assert cur.fetchone()[0] == 0

        second = backfill.run_backfill(conn, dry_run=False)
        assert second == 0


def test_dry_run_does_not_modify(conn):
    """dry_run=True reports the count but writes nothing."""
    with conn.cursor() as cur:
        user_id = _pick_any_user(conn)
        _force_user_missing(cur, user_id)

        count = backfill.run_backfill(conn, dry_run=True)
        assert count >= 1

        cur.execute(
            "SELECT owned_items, active_cosmetics FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        owned, active = cur.fetchone()
        assert owned == ['wager_unlock']
        assert active == ['confetti_1']


def test_replaces_other_page_season_in_active(conn):
    """If a user has page_season7 equipped, the backfill swaps it for page_season8."""
    with conn.cursor() as cur:
        user_id = _pick_any_user(conn)
        cur.execute(
            "UPDATE game_state SET "
            "owned_items = ARRAY['wager_unlock'], "
            "active_cosmetics = ARRAY['confetti_1', 'page_season7'] "
            "WHERE user_id = %s",
            (user_id,),
        )

        backfill.run_backfill(conn, dry_run=False)

        cur.execute(
            "SELECT active_cosmetics FROM game_state WHERE user_id = %s",
            (user_id,),
        )
        active = cur.fetchone()[0]
        assert 'page_season7' not in active
        assert 'page_season8' in active
        assert 'confetti_1' in active
