"""T109 prep: Season 8 `user_season_history` INSERT guard.

Verifies that the `INSERT INTO user_season_history` statement in
`seasons.py::advance_season()` references all 26 S8 columns by name in
BOTH the column list and the SELECT list. Without this guard the
edit in §6.2 would silently drift (someone adds a column to
migration 052 but forgets the INSERT, or adds it to one list and not
the other) and the rollover would write NULLs/defaults into the new
history columns.

Also guards two adjacent §6.1 fixes in the same `UPDATE game_state`
block:

- `shield_charges` must NO LONGER be reset (column was dropped by
  migration 030; the old `shield_charges = 0,` clause would crash the
  rollover with `column "shield_charges" does not exist`).
- the four defensive reset clauses added by §6.1 (
  `wager_banked_losses`, `gravity_drift`, `wager_last_win_amount`,
  `biggest_win_announced`) must remain present so future 8.1 → 8.2
  sub-seasons don't leak transient state.

The 26 columns mirror migration `052_user_season_history_s8.sql` and
SEASON_8_MIGRATION_PLAN.md §6.2.
"""
import os
import re
import importlib.util

import pytest


# Load the real seasons.py via importlib, bypassing any stub that another
# test file may have already installed in sys.modules['seasons'] via
# setdefault. (test_bounties.py and test_spin_logic.py both do this.)
def _load_seasons():
    spec = importlib.util.spec_from_file_location(
        '_real_seasons_for_t109_history',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seasons.py'),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seasons = _load_seasons()


S8_HISTORY_COLUMNS = [
    'wager_streak', 'wager_last_stake', 'wager_banked_wins',
    'wager_banked_losses',
    'insurance_charges', 'insurance_armed', 'wager_last_win_amount',
    'insurance_tokens', 'double_down_pending', 'active_wheel_mode',
    'auto_spin_budget', 'guard_charges', 'guard_last_regen_spin',
    'resilience_last_use_spin', 'legacy_wins', 'prestige_level',
    'prestige_count', 'cumulative_wins', 'gravity_drift',
    'biggest_win_announced', 'cosmetic_fragments', 'bounty_claimed_date',
    'catch_of_the_day_date', 'insurance_free_claimed_date',
    'insurance_unlock_grant_given', 'onboarding_step',
]


def _insert_sql():
    """Return the `INSERT INTO user_season_history` SQL string from
    advance_season()'s source, or None if not found."""
    import inspect
    src = inspect.getsource(_seasons.advance_season)
    m = re.search(
        r'INSERT INTO user_season_history \((.*?)\)\s*SELECT (.*?)\s*FROM game_state gs',
        src, re.DOTALL | re.IGNORECASE,
    )
    return m


# ── INSERT column + SELECT list parity guard ──────────────────────────────────

def test_history_insert_references_all_s8_columns():
    """Every one of the 26 S8 columns must appear in BOTH the INSERT's
    column list AND the SELECT's `gs.<col>` reference list, and the two
    lists must have equal length (else PostgreSQL raises
    'INSERT has more/fewer expressions than target columns' at rollover
    time). Fail with the names of the missing columns."""
    m = _insert_sql()
    assert m is not None, (
        "could not find `INSERT INTO user_season_history … SELECT … FROM "
        "game_state gs` in seasons.advance_season source"
    )
    col_list = m.group(1)
    select_list = m.group(2)

    missing_from_cols = [c for c in S8_HISTORY_COLUMNS if c not in col_list]
    missing_from_select = [
        c for c in S8_HISTORY_COLUMNS
        if 'gs.' + c not in select_list
    ]

    assert not missing_from_cols, (
        f"INSERT column list is missing {len(missing_from_cols)} S8 "
        f"column(s): {missing_from_cols}. Add them to the column list of "
        f"the INSERT INTO user_season_history in seasons.advance_season "
        f"(see SEASON_8_MIGRATION_PLAN.md §6.2)."
    )
    assert not missing_from_select, (
        f"SELECT list is missing {len(missing_from_select)} S8 "
        f"column(s): {missing_from_select}. Add the corresponding "
        f"`gs.<col>` references to the SELECT list of the INSERT INTO "
        f"user_season_history in seasons.advance_season (see "
        f"SEASON_8_MIGRATION_PLAN.md §6.2)."
    )

    # Also assert the two lists have equal cardinality — drift between
    # them (a column added to one but not the other) would crash the
    # rollover INSERT at runtime.
    n_cols = len([c for c in col_list.split(',') if c.strip()])
    n_sels = len([s for s in select_list.split(',') if s.strip()])
    assert n_cols == n_sels, (
        f"INSERT column list ({n_cols}) and SELECT value list ({n_sels}) "
        f"differ in length — the rollover INSERT would fail at runtime. "
        f"Ensure every column added to one list is added to the other."
    )


# ── capture-based guards on the UPDATE game_state block ───────────────────────
#
# Mirrors tests/test_rollover.py:91-107 — exercise advance_season() with a
# stub connection that records the SQL it would execute, then assert on the
# captured `UPDATE game_state` string. We can't run end-to-end against the
# staging DB (the §0 audit notes the function referenced shield_charges,
# now removed by §6.1).

class _CapturingCursor:
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
    def __init__(self, fetch_one=None, fetch_all=None):
        self._cur = _CapturingCursor(fetch_one, fetch_all)
    def cursor(self, *a, **kw): return self._cur
    def commit(self): pass


def _grab_game_state_sql():
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


def test_update_game_state_no_longer_resets_shield_charges():
    """§6.1 critical fix: the `shield_charges = 0,` clause must be gone
    from the UPDATE game_state block. The column was dropped by migration
    030; leaving the clause in would make the rollover throw
    `column "shield_charges" does not exist`."""
    sql = _grab_game_state_sql()
    assert sql is not None, "advance_season() did not execute an UPDATE game_state"
    assert 'shield_charges' not in sql.lower(), (
        f"shield_charges still appears in the UPDATE game_state SQL — "
        f"migration 030 dropped this column, so the clause would crash the "
        f"rollover. Remove the `shield_charges = 0,` line.\n"
        f"Captured SQL:\n{sql}"
    )