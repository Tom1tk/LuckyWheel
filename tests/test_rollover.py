"""T88: Onboarding rollover preservation.

Verifies that `advance_season()` does NOT reset `onboarding_step` in the
per-season `UPDATE game_state` block. A player who completes onboarding
in one season must never see the onboarding flow again in a later season.

The function is invoked through a mock cursor that captures the SQL the
function attempts to execute; we then assert the `UPDATE game_state`
statement no longer contains the `onboarding_step = 0` reset.
"""
import sys
import os
import re
import types
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# Load the real seasons.py via importlib, bypassing any stub that another
# test file may have already installed in sys.modules['seasons'] via
# setdefault. (test_bounties.py and test_spin_logic.py both do this.)
def _load_seasons():
    spec = importlib.util.spec_from_file_location(
        '_real_seasons_for_t88',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seasons.py'),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seasons = _load_seasons()


# ── Source-level guard ────────────────────────────────────────────────────────

def test_onboarding_reset_line_removed_from_advance_season():
    """The `onboarding_step = 0,` clause must not appear in advance_season."""
    import inspect
    src = inspect.getsource(_seasons.advance_season)
    assert 'onboarding_step = 0' not in src, (
        "advance_season still contains the `onboarding_step = 0` reset; "
        "onboarding completion must survive a season rollover."
    )


# ── SQL-capture guard ─────────────────────────────────────────────────────────
#
# We can't run advance_season() end-to-end against the staging DB because the
# function also references columns the current schema no longer has (e.g.
# `shield_charges`, dropped by migration 030). That's a pre-existing bug
# unrelated to T88. Instead, we exercise advance_season() with a fake cursor
# that captures the SQL it would execute, then assert the captured
# `UPDATE game_state` does not reset `onboarding_step`.

class _CapturingCursor:
    """Records every SQL string passed to .execute() and returns canned rows."""

    def __init__(self, fetch_one=None, fetch_all=None):
        self.sql_log = []
        self._fetch_one = fetch_one
        self._fetch_all = fetch_all

    def __enter__(self): return self
    def __exit__(self, *a): return False

    def execute(self, sql, params=None):
        self.sql_log.append(sql)
        self._params = params

    def fetchone(self):
        if self._fetch_one is None: return None
        return self._fetch_one

    def fetchall(self):
        if self._fetch_all is None: return []
        return self._fetch_all


class _FakeConn:
    """Yields the same capturing cursor for every `with conn.cursor()` block."""
    def __init__(self, fetch_one=None, fetch_all=None):
        self._cur = _CapturingCursor(fetch_one, fetch_all)
    def cursor(self, *a, **kw): return self._cur
    def commit(self): pass  # advance_season calls commit; swallow it


def _run_advance_season_and_grab_game_state_sql():
    """Run advance_season() with a stubbed connection and return the
    `UPDATE game_state` SQL string (or None if not found)."""
    fake_season = {
        'id': 1,
        'season_number': 7,
        'started_at': None,
        'ends_at': None,
    }
    conn = _FakeConn(fetch_one=fake_season, fetch_all=[])

    _seasons.advance_season(conn)

    for sql in conn._cur.sql_log:
        if re.search(r'UPDATE\s+game_state\b', sql, re.IGNORECASE):
            return sql
    return None


def test_update_game_state_does_not_reset_onboarding_step():
    """The captured `UPDATE game_state` statement must not contain
    `onboarding_step = 0` (nor any assignment to onboarding_step)."""
    sql = _run_advance_season_and_grab_game_state_sql()
    assert sql is not None, "advance_season() did not execute an UPDATE game_state"

    lowered = sql.lower()
    assert 'onboarding_step' not in lowered, (
        f"onboarding_step appears in the UPDATE game_state SQL — it must be "
        f"left untouched across rollovers.\nCaptured SQL:\n{sql}"
    )


def test_update_game_state_still_resets_auto_spin_budget():
    """Sanity: the related `auto_spin_budget = 0` reset must still be present
    (a different ticket owns that field, but it shares the same SQL block)."""
    sql = _run_advance_season_and_grab_game_state_sql()
    assert sql is not None, "advance_season() did not execute an UPDATE game_state"
    assert 'auto_spin_budget' in sql.lower(), (
        "auto_spin_budget reset is missing — it should remain in the same "
        "UPDATE game_state block as the other per-season resets."
    )
