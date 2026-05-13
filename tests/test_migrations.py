"""Verify migration file integrity — catches version collisions before they hit the DB."""
import os
import re
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent.parent / 'migrations'
MIGRATION_PATTERN = re.compile(r'^(\d+)_(.+)\.sql$')


def _load_migrations():
    migrations = []
    for f in MIGRATIONS_DIR.glob('*.sql'):
        m = MIGRATION_PATTERN.match(f.name)
        assert m, f"Migration filename doesn't match NNN_description.sql: {f.name}"
        migrations.append((int(m.group(1)), f.name, f))
    migrations.sort(key=lambda x: x[0])
    return migrations


def test_migration_filenames_match_pattern():
    """All .sql files must follow NNN_description.sql naming."""
    _load_migrations()  # assertion inside


def test_migration_versions_are_unique():
    migrations = _load_migrations()
    versions = [v for v, _, _ in migrations]
    duplicates = [v for v in versions if versions.count(v) > 1]
    assert not duplicates, (
        f"Duplicate migration versions: {set(duplicates)}. "
        f"Files: {[n for v, n, _ in migrations if v in set(duplicates)]}"
    )


def test_migration_versions_are_sequential_no_large_gaps():
    """Versions should be roughly sequential (no gaps > 5)."""
    migrations = _load_migrations()
    if len(migrations) < 2:
        return
    versions = [v for v, _, _ in migrations]
    for a, b in zip(versions, versions[1:]):
        assert b - a <= 5, (
            f"Large version gap between {a} and {b} — was a migration accidentally skipped?"
        )


def test_migration_files_are_non_empty():
    for _, name, path in _load_migrations():
        content = path.read_text(encoding='utf-8').strip()
        assert content, f"Migration file is empty: {name}"


def test_migrations_dir_exists():
    assert MIGRATIONS_DIR.is_dir(), f"Migrations directory not found: {MIGRATIONS_DIR}"
