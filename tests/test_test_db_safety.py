"""T246: conftest.py's wheeldb refusal check.

T246 routes the test suite at `wheeldb_test` (a clone of the production
schema, not prod itself). The conftest's `_resolve_db_url` refuses to
run any test whose DATABASE_URL points at the production `wheeldb`
database — this is the canonical defense against the pytest-suits-
writing-to-prod problem flagged in §3 of the advisor audit (the
"test suite is hitting the production server" issue surfaced in the
T231–T240 batch when ~1282 localhost users leaked into the live
leaderboard).

This test pins the refusal logic by parsing the same URL-resolution
function and asserting it raises for prod and returns the URL for
test/staging.
"""
import importlib
import os
import sys

import pytest

# Make sure the conftest is importable. Pytest's conftest loading doesn't
# expose the module as `conftest` to test code; we explicitly insert the
# tests/ dir on sys.path so we can import it as a regular module.
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)


def _reload_conftest():
    """Reload the conftest module so its env reads are fresh.

    The conftest pre-loads flask_limiter at import time and runs its
    URL resolver lazily, so a fresh import (or reload) picks up the
    current os.environ values for each test that needs a different URL.
    """
    if 'conftest' in sys.modules:
        return importlib.reload(sys.modules['conftest'])
    import conftest  # noqa: F401
    return conftest


def test_resolve_db_url_refuses_production_wheeldb(monkeypatch):
    """The conftest's URL resolver must refuse wheeldb (production).

    This is the T246 safety check that prevents pytest from running
    against the live production database. A developer who accidentally
    sets DATABASE_URL to the prod URL should see a clear error
    pointing at `make test-db-reset && make test`.
    """
    monkeypatch.setenv('DATABASE_URL',
                       'postgresql://wheelapp:pw@localhost/wheeldb')
    _cf = _reload_conftest()
    with pytest.raises(RuntimeError) as exc_info:
        _cf._resolve_db_url()
    msg = str(exc_info.value)
    assert 'Refusing to run tests' in msg
    assert 'wheeldb_test' in msg  # tells the dev what to do


def test_resolve_db_url_accepts_wheeldb_test(monkeypatch):
    """wheeldb_test is the canonical test database; the resolver returns it."""
    monkeypatch.setenv('DATABASE_URL',
                       'postgresql://wheelapp:pw@localhost/wheeldb_test')
    _cf = _reload_conftest()
    assert _cf._resolve_db_url() == 'postgresql://wheelapp:pw@localhost/wheeldb_test'


def test_resolve_db_url_accepts_wheeldb_staging(monkeypatch):
    """wheeldb_staging is also allowed (the backfill tests run against it)."""
    monkeypatch.setenv('DATABASE_URL',
                       'postgresql://wheelapp:pw@localhost/wheeldb_staging')
    _cf = _reload_conftest()
    assert _cf._resolve_db_url() == 'postgresql://wheelapp:pw@localhost/wheeldb_staging'


def test_resolve_db_url_strips_query_string(monkeypatch):
    """A ?sslmode=... or similar query string on the URL doesn't fool the check."""
    monkeypatch.setenv('DATABASE_URL',
                       'postgresql://wheelapp:pw@localhost/wheeldb?sslmode=require')
    _cf = _reload_conftest()
    with pytest.raises(RuntimeError) as exc_info:
        _cf._resolve_db_url()
    assert 'Refusing to run tests' in str(exc_info.value)

