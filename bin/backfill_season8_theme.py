"""One-shot backfill: grant + equip page_season8 to all staging users missing it.

Safe to re-run (idempotent). DO NOT run on main — migrations 050/051 already
cover main. The script refuses to run unless DATABASE_URL contains the
"wheeldb_staging" marker, so a copy/paste against the production DSN will
fail loudly.

Usage (from the staging deploy root, where .env lives):
    python bin/backfill_season8_theme.py            # apply
    python bin/backfill_season8_theme.py --dry-run  # count only
"""
import argparse
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import dotenv_values

THEME = 'page_season8'
STAGING_MARKER = 'wheeldb_staging'


def load_db_url(env_path: Path | None = None) -> str:
    """Return DATABASE_URL from the given .env file, falling back to $DATABASE_URL."""
    env_path = env_path or Path('.env')
    if env_path.exists():
        url = dotenv_values(env_path).get('DATABASE_URL') or ''
        if url:
            return url
    return os.environ.get('DATABASE_URL') or ''


def is_staging_url(url: str) -> bool:
    """True iff the URL is safe to run the backfill on (i.e. points at staging)."""
    return STAGING_MARKER in (url or '')


def run_backfill(conn, *, dry_run: bool = False) -> int:
    """Grant + equip THEME for any user that is missing it.

    Returns the number of users that were (or would be) updated. The caller
    is responsible for committing or rolling back the transaction.
    """
    if dry_run:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM game_state "
                "WHERE NOT (%s = ANY(owned_items)) "
                "   OR NOT (%s = ANY(active_cosmetics))",
                (THEME, THEME),
            )
            return cur.fetchone()[0]

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE game_state SET
                owned_items = array_append(owned_items, %s),
                active_cosmetics = array_append(
                    ARRAY(SELECT c FROM unnest(active_cosmetics) AS c
                          WHERE c NOT LIKE 'page_season%%'),
                    %s
                )
            WHERE NOT (%s = ANY(owned_items))
               OR NOT (%s = ANY(active_cosmetics))
            """,
            (THEME, THEME, THEME, THEME),
        )
        return cur.rowcount


def _count_total(conn) -> int:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM game_state')
        return cur.fetchone()[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='One-shot backfill of the page_season8 theme on staging.',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Print the count of users that would be updated without applying.',
    )
    args = parser.parse_args(argv)

    db_url = load_db_url()
    if not db_url:
        print('ERROR: DATABASE_URL is not set (.env missing or empty).', file=sys.stderr)
        return 2
    if not is_staging_url(db_url):
        print(
            f'REFUSING to run: DATABASE_URL does not contain "{STAGING_MARKER}".',
            file=sys.stderr,
        )
        print(
            'This script is for staging only; main already has migrations 050/051.',
            file=sys.stderr,
        )
        return 1

    conn = psycopg2.connect(db_url)
    try:
        count = run_backfill(conn, dry_run=args.dry_run)
        total = _count_total(conn)
        if args.dry_run:
            conn.rollback()
            print(f'[dry-run] Would update {count} users.')
        else:
            conn.commit()
            print(f'Updated {count} users')
            print(f'All {total} staging users now own + equip {THEME}.')
    finally:
        conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
