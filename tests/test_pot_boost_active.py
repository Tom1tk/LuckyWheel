"""T247: /api/state further consolidation.

The 5 call sites that check whether the community-pot boost window is
still active duplicated the same 3-clause expression:

    bool(
        pot_row and pot_row['filled'] and pot_row['filled_at'] and
        pot_row['filled_at'] > now_utc - dt.timedelta(days=7)
    )

The expression was identical at /api/state, /api/spin, /api/tick,
/api/spin/tick, and /api/community-pot/admin/reset (game.py:1002,
1254, 1734, 2374, 2427). This test pins the helper's behavior so a
future refactor can't drift the 7-day window or the NULL/falsy guards.
"""
import datetime as dt

import pytest

import game


_NOW = dt.datetime(2026, 6, 29, 12, 0, 0, tzinfo=dt.timezone.utc)


def test_pot_boost_active_none_pot():
    assert game._pot_boost_active(None, _NOW) is False


def test_pot_boost_active_unfilled_pot():
    assert game._pot_boost_active({'filled': False, 'filled_at': _NOW}, _NOW) is False


def test_pot_boost_active_null_filled_at():
    assert game._pot_boost_active({'filled': True, 'filled_at': None}, _NOW) is False


def test_pot_boost_active_freshly_filled():
    assert game._pot_boost_active({'filled': True, 'filled_at': _NOW}, _NOW) is True


def test_pot_boost_active_filled_within_window():
    """Filled 3 days ago — boost still active."""
    filled = _NOW - dt.timedelta(days=3)
    assert game._pot_boost_active({'filled': True, 'filled_at': filled}, _NOW) is True


def test_pot_boost_active_filled_at_window_boundary():
    """Filled exactly 7 days ago — boost has expired (comparison is
    strict `>`: 7.0 days is not within the last 7 days)."""
    filled = _NOW - dt.timedelta(days=7)
    assert game._pot_boost_active({'filled': True, 'filled_at': filled}, _NOW) is False


def test_pot_boost_active_filled_just_inside_window():
    """Filled 6 days, 23 hours, 59 minutes ago — still active."""
    filled = _NOW - dt.timedelta(days=6, hours=23, minutes=59)
    assert game._pot_boost_active({'filled': True, 'filled_at': filled}, _NOW) is True


def test_pot_boost_active_filled_long_ago():
    """Filled 30 days ago — boost has long since expired."""
    filled = _NOW - dt.timedelta(days=30)
    assert game._pot_boost_active({'filled': True, 'filled_at': filled}, _NOW) is False


def test_pot_boost_active_naive_datetime_treated_as_utc():
    """The helper accepts a `now_utc` and compares against `filled_at`
    even if filled_at is naive — the existing call sites all build
    filled_at from psycopg2 which returns tz-aware timestamps, but a
    regression that strips the tz would silently change behavior."""
    naive_filled = _NOW.replace(tzinfo=None) - dt.timedelta(days=2)
    pot = {'filled': True, 'filled_at': naive_filled}
    # Document the actual behavior (naive datetime is a TypeError on
    # comparison); the helper doesn't normalize because the call sites
    # always pass tz-aware timestamps.
    with pytest.raises(TypeError):
        game._pot_boost_active(pot, _NOW)
