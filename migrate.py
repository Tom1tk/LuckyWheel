#!/usr/bin/env python3
"""
Lightweight SQL migration runner.

Usage:
    python migrate.py              # apply pending migrations
    python migrate.py --status     # show applied / pending migrations
    python migrate.py --dry-run    # preview what would run, without executing

Reads DATABASE_URL from environment (or .env file if python-dotenv is installed).
Migration files: migrations/NNN_description.sql  (NNN = zero-padded integer)
Tracking table:  schema_migrations (created automatically)
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import psycopg2
except ImportError:
    sys.exit("psycopg2 not installed. Run: pip install psycopg2-binary")

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
TRACKING_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

MIGRATION_PATTERN = re.compile(r'^(\d+)_(.+)\.sql$')


def get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL not set. Create a .env file or export the variable.")
    return psycopg2.connect(db_url)


def ensure_tracking_table(cur):
    cur.execute(TRACKING_TABLE_SQL)


def load_migration_files():
    """Return sorted list of (version, name, path) for all migration files."""
    migrations = []
    for f in MIGRATIONS_DIR.glob("*.sql"):
        m = MIGRATION_PATTERN.match(f.name)
        if m:
            version = int(m.group(1))
            name = m.group(2)
            migrations.append((version, name, f))
    migrations.sort(key=lambda x: x[0])
    return migrations


def get_applied_versions(cur):
    cur.execute("SELECT version FROM schema_migrations ORDER BY version")
    return {row[0] for row in cur.fetchall()}


def get_applied_details(cur):
    cur.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version")
    return cur.fetchall()


def cmd_status(cur):
    migrations = load_migration_files()
    applied = get_applied_versions(cur)
    applied_details = {r[0]: r for r in get_applied_details(cur)}

    print(f"{'VER':>5}  {'STATUS':<10}  {'NAME'}")
    print("-" * 60)
    for version, name, _ in migrations:
        if version in applied:
            ts = applied_details[version][2].strftime("%Y-%m-%d %H:%M")
            status = f"applied ({ts})"
        else:
            status = "PENDING"
        print(f"{version:>5}  {status:<32}  {name}")

    pending = [v for v, _, _ in migrations if v not in applied]
    print(f"\n{len(pending)} pending migration(s).")


def cmd_apply(cur, dry_run=False):
    migrations = load_migration_files()
    applied = get_applied_versions(cur)

    pending = [(v, n, p) for v, n, p in migrations if v not in applied]

    if not pending:
        print("Nothing to apply — database is up to date.")
        return

    for version, name, path in pending:
        sql = path.read_text()
        label = f"{version:03d}_{name}.sql"

        if dry_run:
            print(f"[DRY RUN] Would apply: {label}")
            print("--- SQL ---")
            print(sql.strip())
            print("-----------\n")
            continue

        print(f"Applying {label} ...", end=" ", flush=True)
        # Strip single-line comments and blank lines; skip if nothing executable remains
        executable = "\n".join(
            line for line in sql.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ).strip()
        if executable:
            cur.execute(sql)
        cur.execute(
            "INSERT INTO schema_migrations (version, name) VALUES (%s, %s)",
            (version, name),
        )
        print("done.")

    if not dry_run:
        print(f"\n{len(pending)} migration(s) applied.")


def main():
    parser = argparse.ArgumentParser(description="SQL migration runner")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--dry-run", action="store_true", help="Preview without applying")
    args = parser.parse_args()

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                ensure_tracking_table(cur)

                if args.status:
                    cmd_status(cur)
                else:
                    cmd_apply(cur, dry_run=args.dry_run)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
