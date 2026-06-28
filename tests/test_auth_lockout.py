"""T239: Characterization tests for `security.py` lockout helpers.

The login-lockout logic in `security.py` (`check_lockout` / `record_attempt`
/ `clear_attempts`) was previously untested. These tests cover the
LOCKOUT_RULES threshold table in `models.py`:

  LOCKOUT_RULES = [
      (20, 3600),  # 20+ fails → 1 hour
      (10, 300),   # 10+ fails → 5 minutes
      (5,  60),    # 5+ fails  → 1 minute
  ]

The tests use a real DB connection (conftest `db_url` fixture) so the SQL
the helpers actually run is exercised. Time is mocked with
`unittest.mock.patch` so the remaining-time math can be asserted
deterministically.

Scope (T239 acceptance criteria, AC#2):
  * For each threshold: `check_lockout` returns 0 below threshold and >0
    at/after it.
  * The remaining time decreases as the (mocked) clock advances.
  * `clear_attempts` resets the counter.
  * Failures older than 1 hour are ignored (the `attempted_at > NOW() -
    INTERVAL '1 hour'` clause in `check_lockout`).

These are characterization tests — capture current behaviour. If a future
refactor changes the threshold math, update the assertions here and add a
changelog note.
"""
import os
import sys
import uuid
import types
from datetime import datetime, timezone
from unittest import mock

import psycopg2
import psycopg2.extras
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# T239 / T231 follow-up: install a minimal `flask` stub BEFORE importing
# `security`, so security's `from flask import request, jsonify` resolves
# to the stub and does NOT load the real `flask` into sys.modules. Real
# flask is a werkzeug.LocalProxy-using module; loading it pollutes
# sys.modules and breaks the ~20 sibling test files that rely on the
# stub-flask pattern. The stubs below match what test_chat.py /
# test_auto_spin.py install at their own import time, so whichever
# test's stub "wins" the race, the rest of the suite still works.
def _noop(*a, **kw):
    return lambda f: f
def _maybe_stub(name, attrs):
    existing = sys.modules.get(name)
    if existing is None or not (hasattr(existing, 'Flask') or hasattr(existing, 'LoginManager')):
        mod = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(mod, k, v)
        sys.modules[name] = mod
_maybe_stub('flask', {
    'Blueprint': lambda *a, **kw: types.SimpleNamespace(route=_noop),
    'jsonify': lambda x: x,
    'request': types.SimpleNamespace(method='GET', is_json=True, json=None, get_json=lambda: None),
})
# current_user: match the most common stub shape used by the
# 22 stub-installing test files. Some use `None` (e.g. test_chat.py),
# others use a SimpleNamespace with id+username (e.g.
# test_auto_spin_visibility.py, which calls `current_user.id`).
# A SimpleNamespace with `.id` works for BOTH: tests that don't
# touch current_user still pass (id is just an attribute), and
# tests that touch .id get a valid value.
_maybe_stub('flask_login', {
    'current_user': types.SimpleNamespace(id=42, username='alice', is_authenticated=True),
    'login_required': lambda f: f,
    'UserMixin': type('UserMixin', (), {}),
})

from security import check_lockout, clear_attempts, record_attempt  # noqa: E402


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def _fresh_identifier() -> str:
    """Return an identifier unique to this test run so DB rows don't collide."""
    return f't239-{uuid.uuid4().hex[:16]}'


@pytest.fixture
def db(db_url):
    """Yield a connection; clean up any rows the test wrote for its identifier.

    T239 uses unique identifiers per test so there's no cross-test leak, but
    we still clear them on teardown as a belt-and-braces measure.
    """
    identifiers = []

    def _make(identifier: str | None = None):
        if identifier is None:
            identifier = _fresh_identifier()
        identifiers.append(identifier)
        return psycopg2.connect(db_url)

    yield _make
    if identifiers:
        conn = psycopg2.connect(db_url)
        try:
            with conn.cursor() as cur:
                for ident in identifiers:
                    cur.execute(
                        'DELETE FROM login_attempts WHERE identifier = %s',
                        (ident,),
                    )
            conn.commit()
        finally:
            conn.close()


# ──────────────────────────────────────────────────────────────────────────
# AC#2: For each threshold, check_lockout returns 0 below and >0 at/above
#
# LOCKOUT_RULES is checked top-down, first match wins:
#   (20, 3600)  →  20+ fails  →  1 hour
#   (10, 300)   →  10-19 fails  →  5 minutes
#   (5,  60)    →  5-9 fails   →  1 minute
#   < 5 fails   →  no lockout  (returns 0)
# ──────────────────────────────────────────────────────────────────────────

def test_below_all_thresholds_returns_zero(db):
    """0–4 failed attempts → no threshold reached → check_lockout returns 0."""
    for n_failures in (0, 1, 2, 3, 4):
        conn = db()
        identifier = _fresh_identifier()
        try:
            for i in range(n_failures):
                record_attempt(conn, identifier, False)
            conn.commit()
            remaining = check_lockout(conn, identifier)
            assert remaining == 0, (
                f"with {n_failures} failures (below all thresholds), "
                f"check_lockout should return 0, got {remaining}"
            )
        finally:
            conn.close()


def _at_now_plus(seconds: float) -> datetime:
    """Return real `datetime.now(utc)` plus `seconds` (a fixture-local
    helper for mocking). The mock clock is anchored to wall-clock now so
    the elapsed-since-last-fail math stays small (≈ 0 by default).
    """
    return datetime.now(timezone.utc).fromtimestamp(
        datetime.now(timezone.utc).timestamp() + seconds, tz=timezone.utc,
    )


@pytest.mark.parametrize('threshold, lock_secs', [
    (5,  60),
    (10, 300),
    (20, 3600),
])
def test_at_threshold_returns_positive(db, threshold, lock_secs):
    """Exactly `threshold` failed attempts → locked, remaining ≈ lock_secs.

    The matching rule is whichever is first in LOCKOUT_RULES that the
    count meets. With elapsed ≈ 0 the returned value should equal the
    rule's lock_secs (cast to int).
    """
    with mock.patch('security.datetime') as mock_dt:
        # Anchor the mock clock to NOW (real) so the elapsed-since-last-fail
        # math is small. The DB stamps attempted_at via DEFAULT NOW(), so
        # any fixed future time would cause the elapsed to be huge.
        mock_dt.now.return_value = _at_now_plus(0)
        conn = db()
        identifier = _fresh_identifier()
        try:
            for i in range(threshold):
                record_attempt(conn, identifier, False)
            conn.commit()
            remaining = check_lockout(conn, identifier)
            assert remaining > 0, (
                f"at threshold={threshold}, check_lockout should return >0, "
                f"got {remaining}"
            )
            # With elapsed ≈ 0, remaining should equal the rule's lock_secs
            # (within a small tolerance for test execution time).
            assert abs(remaining - lock_secs) <= 2, (
                f"at threshold={threshold}, check_lockout should return "
                f"~{lock_secs}s (the matching rule's lock_secs), got {remaining}"
            )
        finally:
            conn.close()


@pytest.mark.parametrize('threshold, lock_secs', [
    (5,  60),
    (6,  60),    # one above the 5-fail rule
    (9,  60),    # last value in the 5-fail bucket
    (10, 300),   # first value in the 10-fail bucket
    (15, 300),
    (19, 300),   # last value in the 10-fail bucket
    (20, 3600),  # first value in the 20-fail bucket
    (25, 3600),
])
def test_bucket_boundaries_use_first_matching_rule(db, threshold, lock_secs):
    """`threshold` failed attempts → returns the rule's lock_secs.

    LOCKOUT_RULES is iterated in order; the FIRST rule where
    fail_count >= threshold applies. We sweep the boundaries between
    buckets to lock in the table ordering.
    """
    with mock.patch('security.datetime') as mock_dt:
        mock_dt.now.return_value = _at_now_plus(0)
        conn = db()
        identifier = _fresh_identifier()
        try:
            for i in range(threshold):
                record_attempt(conn, identifier, False)
            conn.commit()
            remaining = check_lockout(conn, identifier)
            assert abs(remaining - lock_secs) <= 2, (
                f"with {threshold} failures, check_lockout should return "
                f"~{lock_secs}s (the first matching rule's lock_secs), "
                f"got {remaining}"
            )
        finally:
            conn.close()


def test_cumulative_higher_threshold_wins(db):
    """Crossing a higher threshold bumps the lockout to that rule's duration.

    The list is ordered high-to-low (20/3600, 10/300, 5/60) so the 20-fail
    rule is the first to match at 20+ fails. With elapsed ≈ 0 the
    remaining should be ~3600.
    """
    with mock.patch('security.datetime') as mock_dt:
        mock_dt.now.return_value = _at_now_plus(0)
        conn = db()
        identifier = _fresh_identifier()
        try:
            # 20 fails → matches the (20, 3600) rule.
            for i in range(20):
                record_attempt(conn, identifier, False)
            conn.commit()
            remaining = check_lockout(conn, identifier)
            assert abs(remaining - 3600) <= 2, (
                f"20 fails should hit the (20, 3600) rule (~3600s), got {remaining}"
            )
            # 25 fails (still 20+ bucket) → same 3600s rule.
            for i in range(5):
                record_attempt(conn, identifier, False)
            conn.commit()
            remaining = check_lockout(conn, identifier)
            assert abs(remaining - 3600) <= 2, (
                f"25 fails still in the (20, 3600) bucket, got {remaining}"
            )
            # Now drop the count by clearing — verify the next attempt
            # brings it back to 0 (no lockout).
            clear_attempts(conn, identifier)
            conn.commit()
            assert check_lockout(conn, identifier) == 0
            # 4 fails — below all thresholds — still no lockout.
            for i in range(4):
                record_attempt(conn, identifier, False)
            conn.commit()
            assert check_lockout(conn, identifier) == 0
        finally:
            conn.close()


# ──────────────────────────────────────────────────────────────────────────
# AC#2: Remaining time decreases as the (mocked) clock advances
# ──────────────────────────────────────────────────────────────────────────

def test_remaining_time_decreases_with_elapsed_time(db):
    """At 5 fails the rule is 60s. As `now` advances past the last attempt,
    `remaining` shrinks (and never goes below 0)."""
    conn = db()
    identifier = _fresh_identifier()
    try:
        for i in range(5):
            record_attempt(conn, identifier, False)
        conn.commit()

        # Step the mocked clock forward in 10s increments, recording the
        # remaining returned by check_lockout. At t=0s → 60s; at t=60s → 0s.
        observed = []
        for elapsed_secs in (0, 10, 30, 59, 60, 120, 600):
            with mock.patch('security.datetime') as mock_dt:
                mock_dt.now.return_value = _at_now_plus(elapsed_secs)
                observed.append((elapsed_secs, check_lockout(conn, identifier)))

        # The sequence must be non-increasing and bounded by [0, 60].
        for elapsed, remaining in observed:
            assert 0 <= remaining <= 60, (
                f"elapsed={elapsed}s: remaining={remaining} not in [0, 60]"
            )
        # Monotonically non-increasing.
        for i in range(1, len(observed)):
            prev = observed[i - 1][1]
            curr = observed[i][1]
            assert curr <= prev, (
                f"remaining should be non-increasing as time advances; "
                f"at elapsed={observed[i][0]}s got {curr}, prev was {prev}"
            )
        # At t=0 we should see ~60s remaining.
        assert abs(observed[0][1] - 60) <= 2, (
            f"at t=0 (just after 5th fail), remaining should be ~60s, "
            f"got {observed[0][1]}"
        )
        # At t >= 60 the lockout is over.
        for elapsed, remaining in observed:
            if elapsed >= 60:
                assert remaining == 0, (
                    f"at t={elapsed}s, lockout should be expired (0), "
                    f"got {remaining}"
                )
    finally:
        conn.close()


def test_remaining_clamps_at_zero_when_lockout_expired(db):
    """When the elapsed time exceeds the lock_secs (i.e. the lockout has
    expired), `max(0, int(remaining))` clamps to 0.

    The function uses `remaining = lock_secs - elapsed` and then
    `max(0, int(remaining))`. When `elapsed > lock_secs`, `remaining` is
    negative, so the clamp kicks in and the function returns 0. This
    tests the path: "the lockout window has fully passed" → not locked.
    """
    conn = db()
    identifier = _fresh_identifier()
    try:
        for i in range(5):
            record_attempt(conn, identifier, False)
        conn.commit()

        # Step the clock forward past the 60s window.
        with mock.patch('security.datetime') as mock_dt:
            mock_dt.now.return_value = _at_now_plus(120)  # 2 minutes later
            remaining = check_lockout(conn, identifier)
            assert remaining == 0, (
                f"with elapsed=120s > lock_secs=60, remaining should clamp "
                f"to 0 (lockout expired), got {remaining}"
            )
    finally:
        conn.close()


def test_remaining_characterizes_negative_elapsed_behavior(db):
    """Characterization: with `now` BEFORE last_fail (negative elapsed),
    `remaining` is `lock_secs - negative` = lock_secs + |elapsed| → a large
    positive value. The `max(0, int(remaining))` clamp only fires on
    negative `remaining`, not on negative `elapsed`.

    This is observed behaviour, not a bug-fix target (T239 captures
    current behaviour; the bugfix would be a separate ticket if it's
    considered a real issue). The assertion below documents what the
    function actually returns in this edge case so any future change
    shows up as a test diff.
    """
    conn = db()
    identifier = _fresh_identifier()
    try:
        for i in range(5):
            record_attempt(conn, identifier, False)
        conn.commit()

        with mock.patch('security.datetime') as mock_dt:
            # 1970 → huge negative elapsed (~-56 years from now).
            mock_dt.now.return_value = datetime(1970, 1, 1, tzinfo=timezone.utc)
            remaining = check_lockout(conn, identifier)
            # The current implementation does NOT clamp this — the clamp
            # is on `remaining`, not on `elapsed`. Assert the observed
            # behaviour: remaining is large and positive.
            assert remaining > 60, (
                f"with now (1970) way before last_fail, remaining is "
                f"lock_secs - negative = huge positive. The current "
                f"implementation returns a large value here, not 0. "
                f"Got {remaining}"
            )
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────────
# AC#2: clear_attempts resets
# ──────────────────────────────────────────────────────────────────────────

def test_clear_attempts_resets_lockout(db):
    """After enough failures to lock, clear_attempts drops remaining to 0."""
    conn = db()
    identifier = _fresh_identifier()
    try:
        for i in range(5):
            record_attempt(conn, identifier, False)
        conn.commit()
        # Sanity: locked.
        with mock.patch('security.datetime') as mock_dt:
            mock_dt.now.return_value = _at_now_plus(0)
            assert check_lockout(conn, identifier) > 0
        # Clear.
        clear_attempts(conn, identifier)
        conn.commit()
        # No longer locked.
        with mock.patch('security.datetime') as mock_dt:
            mock_dt.now.return_value = _at_now_plus(0)
            assert check_lockout(conn, identifier) == 0
    finally:
        conn.close()


def test_clear_attempts_no_rows_is_noop(db):
    """Calling clear_attempts on a clean identifier is a no-op (no error)."""
    conn = db()
    identifier = _fresh_identifier()
    try:
        clear_attempts(conn, identifier)
        conn.commit()
        assert check_lockout(conn, identifier) == 0
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────────
# AC#2 (additional): record_attempt for SUCCESS does not lock; the COUNT()
# in check_lockout filters success=FALSE
# ──────────────────────────────────────────────────────────────────────────

def test_successful_attempts_do_not_contribute_to_lockout(db):
    """record_attempt(success=True) does not increment the fail counter.

    The auth flow records a SUCCESS attempt on every successful login and
    also calls `clear_attempts`. We assert the SQL behavior in isolation:
    10 successful + 4 failed attempts → still below the (5, 60) threshold
    ONLY if success rows are excluded. They are excluded (see the
    `success = FALSE` clause in check_lockout's SELECT).
    """
    conn = db()
    identifier = _fresh_identifier()
    try:
        for i in range(10):
            record_attempt(conn, identifier, True)   # successes
        for i in range(4):
            record_attempt(conn, identifier, False)  # failures
        conn.commit()
        # 4 failures < 5 (the lowest threshold) → not locked.
        assert check_lockout(conn, identifier) == 0
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────────
# AC#2 (additional): old attempts (>1 hour) don't count
# ──────────────────────────────────────────────────────────────────────────

def test_attempts_older_than_one_hour_are_ignored(db):
    """5 failures, but the 5th is more than 1 hour old → not locked.

    The check_lockout SQL includes
    `attempted_at > NOW() - INTERVAL '1 hour'`, so stale rows are
    excluded from the COUNT. We directly UPDATE attempted_at to the past
    to simulate the row aging out.
    """
    conn = db()
    identifier = _fresh_identifier()
    try:
        for i in range(5):
            record_attempt(conn, identifier, False)
        conn.commit()
        # Backdate ALL 5 rows to 2 hours ago.
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE login_attempts "
                "SET attempted_at = NOW() - INTERVAL '2 hours' "
                "WHERE identifier = %s",
                (identifier,),
            )
        conn.commit()
        # They should not count → not locked.
        assert check_lockout(conn, identifier) == 0
    finally:
        conn.close()
