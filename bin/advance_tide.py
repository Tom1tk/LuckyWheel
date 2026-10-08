#!/usr/bin/env python3
"""RV-10: advance the Season 9 tide (9.N -> 9.N+1) once its rollover is due.

Usage:
    python3 bin/advance_tide.py --db NAME [--check-only]

Exit codes:
    0   advanced, or not due yet
    2   not in a tide (season launch is manual)
    3   connected database is not NAME (nothing changed)
    10  due (only with --check-only; nothing changed)
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import psycopg2
from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import seasons  # noqa: E402

EXIT_NOT_TIDE = 2
EXIT_WRONG_DB = 3
EXIT_DUE = 10


def load_database_url(env_path=None):
    """DATABASE_URL from the repo .env, falling back to the environment (as backfill_season8_theme.py)."""
    env_path = env_path or REPO_ROOT / '.env'
    if env_path.exists():
        url = dotenv_values(env_path).get('DATABASE_URL') or ''
        if url:
            return url
    return os.environ.get('DATABASE_URL') or ''


def dsn_for(db_name):
    """The configured DSN with only the database name replaced by db_name."""
    url = load_database_url()
    if not url:
        sys.exit('DATABASE_URL is not set (.env missing or empty)')
    return urlsplit(url)._replace(path='/' + db_name).geturl()


def connect_checked(db_name):
    """Connect to db_name; exit 3 unless the server reports exactly db_name."""
    conn = psycopg2.connect(dsn_for(db_name))
    with conn.cursor() as cur:
        cur.execute('SELECT current_database()')
        actual = cur.fetchone()[0]
    if actual != db_name:
        conn.close()
        print(f'refusing: connected to {actual!r}, expected {db_name!r}', file=sys.stderr)
        sys.exit(EXIT_WRONG_DB)
    return conn


def tide_status(sub_number, ends_at, now):
    """'not_tide' (season launch is manual), 'not_due', or 'due'."""
    if sub_number is None:
        return 'not_tide'
    if ends_at is None or ends_at > now:
        return 'not_due'
    return 'due'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Advance the Season 9 tide when it is due.')
    parser.add_argument('--db', required=True, help='database to act on; must be the one connected to')
    parser.add_argument('--check-only', action='store_true',
                        help='report whether a tide is due (exit 10); change nothing')
    args = parser.parse_args(argv)

    conn = connect_checked(args.db)
    try:
        with conn.cursor() as cur:
            # FOR UPDATE holds the row until commit/rollback, so the due check and the advance cannot race.
            cur.execute('SELECT season_number, player_facing_number, sub_number, ends_at '
                        'FROM seasons ORDER BY id LIMIT 1 FOR UPDATE')
            season_number, pfn, sub, ends_at = cur.fetchone()

        status = tide_status(sub, ends_at, datetime.now(timezone.utc))
        if status == 'not_tide':
            conn.rollback()
            print('not in a tide (season launch is manual)')
            return EXIT_NOT_TIDE
        if status == 'not_due':
            conn.rollback()
            print(f'tide not due (ends_at={ends_at.isoformat() if ends_at else None})')
            return 0

        old = seasons.season_label(pfn, sub, season_number)
        print(f'tide due (label={old})')
        if args.check_only:
            conn.rollback()
            return EXIT_DUE

        seasons.advance_season(conn)  # commits internally, releasing the row lock
        new = seasons.ensure_current_season(conn)['season_label']
        print(f'advanced {old} -> {new}')
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
