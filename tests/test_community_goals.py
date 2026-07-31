"""Tests for community_goals.py.

Covers T93 (per-player cap race fix in increment_goal) and T84
(25/50/75% milestone auto-posting):

1. Mock-based tests verify the SQL pattern is correct:
   INSERT ... ON CONFLICT DO NOTHING  ->  SELECT ... FOR UPDATE  ->  UPDATE ...
2. Mock-based tests verify the per-player cap is enforced (clamp logic).
3. Mock-based test simulates the post-lock invariant with sequential calls.
4. Mock-based tests verify milestone crossings set the milestone_* column
   and post the goal_milestone_{25,50,75} system message.
5. An optional integration test runs two threads against a real PostgreSQL
   to prove the cap is not exceeded under actual concurrency. Skipped
   when DATABASE_URL is unreachable.
"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Best-effort .env load so the integration test can run when DATABASE_URL
# is set in .env but not exported. match migrate.py's pattern.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
except Exception:
    pass

import psycopg2
import pytest

import chat_triggers
import community_goals


# ─── Mock infrastructure ────────────────────────────────────────────────────


class _FakeCursor:
    """Records executed SQL and serves a configurable fetchone() queue.

    Mirrors the post-lock visibility: when an UPDATE bumps the contrib row,
    the next SELECT ... FOR UPDATE in this cursor reports the new value.
    That is what a real FOR UPDATE lock provides to a concurrent reader
    waiting on the lock.
    """

    def __init__(self):
        self.log = []
        self._contributed = 0
        self._fetchone_queue = []
        self._last_was_dedup_select = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def queue_fetchone(self, value):
        self._fetchone_queue.append(value)

    def execute(self, sql, params=None):
        self.log.append((sql, params))
        if 'UPDATE community_goal_contributions' in sql and 'contributed = contributed' in sql:
            # Mirror the row update so the next SELECT FOR UPDATE reports it.
            self._contributed += params[0]
        # T209: dedup SELECT in post_dedup_system_message — the next
        # fetchone() returns None (no prior message exists in this fake).
        self._last_was_dedup_select = (
            'SELECT id FROM chat_messages' in sql
            and 'ORDER BY id DESC' in sql
        )

    def fetchone(self):
        if self._last_was_dedup_select:
            self._last_was_dedup_select = False
            return None
        if self._fetchone_queue:
            return self._fetchone_queue.pop(0)
        # Default: report the tracked contributed value (the lock-visible state).
        # Milestone flags default to FALSE so the milestone check skips them.
        return {'contributed': self._contributed, 'current': self._contributed,
                'target': 100, 'completed': False,
                'milestone_25': False, 'milestone_50': False, 'milestone_75': False}


class _FakeConn:
    """Always hands out the same cursor object so we can pre-configure it.

    The real function does ``with conn.cursor(...) as cur:`` -- each call
    to ``conn.cursor()`` returns a fresh cursor, but by making every call
    return the same pre-configured instance we can pre-load fetchone()
    results and the initial contributed value.
    """

    def __init__(self):
        self.cursor_obj = _FakeCursor()

    def cursor(self, cursor_factory=None):
        return self.cursor_obj


# ─── 1. SQL pattern tests (T93 AC #1) ──────────────────────────────────────


def test_increment_goal_uses_for_update_after_upsert():
    """T93 AC #1: increment_goal uses SELECT ... FOR UPDATE after ON CONFLICT DO NOTHING."""
    conn = _FakeConn()
    community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=10)

    flat = [sql for sql, _ in conn.cursor_obj.log]
    upsert_idx = next(i for i, s in enumerate(flat)
                      if 'INSERT INTO community_goal_contributions' in s)
    for_update_idx = next(i for i, s in enumerate(flat)
                          if 'SELECT contributed FROM community_goal_contributions' in s
                          and 'FOR UPDATE' in s)
    contrib_update_idx = next(i for i, s in enumerate(flat)
                              if s.strip().upper().startswith('UPDATE')
                              and 'community_goal_contributions' in s
                              and 'contributed = contributed' in s)
    goal_update_idx = next(i for i, s in enumerate(flat)
                           if s.strip().upper().startswith('UPDATE')
                           and 'community_goals' in s
                           and 'current = current' in s)

    # The lock must come after the upsert (so the row exists when we lock it).
    assert upsert_idx < for_update_idx, "FOR UPDATE must run after ON CONFLICT DO NOTHING upsert"
    # And before the writes that depend on the locked value.
    assert for_update_idx < contrib_update_idx, "FOR UPDATE must run before the contrib UPDATE"
    assert for_update_idx < goal_update_idx, "FOR UPDATE must run before the goal UPDATE"


def test_increment_goal_upsert_uses_on_conflict_do_nothing():
    conn = _FakeConn()
    community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=5)
    upsert_sql = next(s for s, _ in conn.cursor_obj.log
                      if 'INSERT INTO community_goal_contributions' in s)
    assert 'ON CONFLICT' in upsert_sql.upper()
    assert 'DO NOTHING' in upsert_sql.upper()


def test_increment_goal_emits_expected_op_sequence():
    conn = _FakeConn()
    community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=3)

    flat = [sql.strip().split(None, 1)[0].upper() for sql, _ in conn.cursor_obj.log]
    assert 'INSERT' in flat
    assert 'SELECT' in flat
    # Two UPDATEs: contributions row and community_goals total.
    update_count = sum(1 for s in flat if s == 'UPDATE')
    assert update_count == 2, f"expected 2 UPDATEs (contrib + goal), got {update_count}: {flat}"


# ─── 2. Cap-enforcement (clamp) tests ──────────────────────────────────────


def test_increment_goal_clamps_to_cap():
    """If current+amount > cap, only the delta is added; the UPDATE uses the clamped amount."""
    cap = community_goals.COMMUNITY_GOAL_DEFS[0]['per_player_cap']  # 500
    conn = _FakeConn()
    conn.cursor_obj._contributed = 495
    conn.cursor_obj.queue_fetchone({'contributed': 495, 'current': 0, 'target': cap, 'completed': False})

    actual = community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=10)
    assert actual == 5, f"expected clamp to 5 (500 cap - 495 current), got {actual}"

    contrib_update = next(p for s, p in conn.cursor_obj.log
                          if s.strip().upper().startswith('UPDATE')
                          and 'community_goal_contributions' in s
                          and 'contributed = contributed' in s)
    assert contrib_update[0] == 5, f"UPDATE must use clamped amount 5, got {contrib_update[0]}"


def test_increment_goal_returns_zero_when_cap_reached():
    """If the player is already at the cap, return 0 and issue no UPDATEs."""
    cap = community_goals.COMMUNITY_GOAL_DEFS[0]['per_player_cap']
    conn = _FakeConn()
    conn.cursor_obj._contributed = cap
    conn.cursor_obj.queue_fetchone({'contributed': cap, 'current': 0, 'target': cap, 'completed': False})

    actual = community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=999)
    assert actual == 0

    # No UPDATE statements should have been issued.
    for s, _ in conn.cursor_obj.log:
        assert not s.strip().upper().startswith('UPDATE'), (
            f"no UPDATE expected when cap reached, got: {s!r}"
        )


def test_increment_goal_unknown_goal_returns_zero():
    conn = _FakeConn()
    assert community_goals.increment_goal(conn, 'nonexistent_goal', user_id=1, amount=10) == 0
    # No DB access at all when the goal id is unknown.
    assert conn.cursor_obj.log == []


def test_increment_goal_no_clamp_when_under_cap():
    cap = community_goals.COMMUNITY_GOAL_DEFS[0]['per_player_cap']
    conn = _FakeConn()
    conn.cursor_obj._contributed = 100
    conn.cursor_obj.queue_fetchone({'contributed': 100, 'current': 0, 'target': cap, 'completed': False})

    actual = community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=50)
    assert actual == 50
    contrib_update = next(p for s, p in conn.cursor_obj.log
                          if s.strip().upper().startswith('UPDATE')
                          and 'community_goal_contributions' in s
                          and 'contributed = contributed' in s)
    assert contrib_update[0] == 50


# ─── 3. Race-simulation test (sequential calls, lock semantics) ────────────


def test_sequential_calls_near_cap_never_exceed_cap():
    """Simulates the post-lock invariant: two calls near the cap must
    together contribute at most the cap.

    Under a real FOR UPDATE lock the second caller sees the first's write.
    We simulate that visibility by feeding the second call's SELECT FOR
    UPDATE the post-update state of the first.
    """
    # Use goal_prestige50 (per_player_cap=10) so the math is obvious.
    cap = 10
    # First call: current=8, ask for 6 -> clamps to 2, contrib becomes 10.
    first = _FakeConn()
    first.cursor_obj._contributed = 8
    first.cursor_obj.queue_fetchone({'contributed': 8, 'current': 0, 'target': 100, 'completed': False})
    first_actual = community_goals.increment_goal(first, 'goal_prestige50', user_id=42, amount=6)
    assert first_actual == 2

    # Second call: under the buggy code it would still see 8 and write 6 more
    # -> 14. Under the fix, the locked row shows 10 -> clamps to 0.
    second = _FakeConn()
    second.cursor_obj._contributed = 10
    second.cursor_obj.queue_fetchone({'contributed': 10, 'current': 0, 'target': 100, 'completed': False})
    second_actual = community_goals.increment_goal(second, 'goal_prestige50', user_id=42, amount=6)
    assert second_actual == 0, (
        f"second call should be clamped to 0 (already at cap), got {second_actual}"
    )
    assert first_actual + second_actual <= cap


# ─── 4. T84 milestone tests ────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_chat_throttle():
    """Reset post_system_message throttle between tests so milestone posts
    aren't silently dropped from a prior test's run.
    """
    try:
        import chat
        chat._system_message_last_posted.clear()
    except Exception:
        pass
    yield
    try:
        import chat
        chat._system_message_last_posted.clear()
    except Exception:
        pass


def _has_milestone_update(log, pct):
    """True if the SQL log contains a `SET milestone_{pct} = TRUE` UPDATE."""
    marker = f'SET milestone_{pct} = TRUE'
    return any(marker in sql for sql, _ in log)


def _milestone_chat_messages(log):
    """Return list of (pct, message) for any goal_milestone_* chat inserts."""
    out = []
    for sql, params in log:
        if 'INSERT INTO chat_messages' in sql and params:
            # T209: post_dedup_system_message passes (user_id, message,
            # message_type, event_kind) — message is at index 1. Earlier
            # callers used post_system_message which passed (message, message_type)
            # — message at index 0. Find the position heuristically: the
            # message starts with 'Community goal at '.
            msg = None
            for p in params:
                if isinstance(p, str) and p.startswith('Community goal at '):
                    msg = p
                    break
            if msg is None:
                continue
            for pct in (25, 50, 75):
                if chat_triggers.goal_milestone_msg(pct, 0, 1).split(':')[0] in msg:
                    out.append((pct, msg))
                    break
    return out


def test_increment_goal_crosses_25_percent_sets_milestone_and_posts():
    """T84: crossing 25% sets milestone_25=TRUE and posts goal_milestone_25."""
    conn = _FakeConn()
    conn.cursor_obj._contributed = 0
    conn.cursor_obj.queue_fetchone({'contributed': 0, 'current': 0, 'target': 500,
                                    'completed': False,
                                    'milestone_25': False, 'milestone_50': False,
                                    'milestone_75': False})
    # Post-increment RETURNING row: current=125 (25% of 500), no milestones yet.
    conn.cursor_obj.queue_fetchone({'current': 125, 'target': 500,
                                    'milestone_25': False, 'milestone_50': False,
                                    'milestone_75': False})

    actual = community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=1)
    assert actual == 1

    assert _has_milestone_update(conn.cursor_obj.log, 25), (
        "milestone_25 UPDATE expected when crossing 25%"
    )
    assert not _has_milestone_update(conn.cursor_obj.log, 50)
    assert not _has_milestone_update(conn.cursor_obj.log, 75)

    msgs = _milestone_chat_messages(conn.cursor_obj.log)
    assert any(pct == 25 and '125' in m and '500' in m for pct, m in msgs), (
        f"expected goal_milestone_25 chat message with 125/500, got: {msgs}"
    )
    assert not any(pct == 50 for pct, _ in msgs)
    assert not any(pct == 75 for pct, _ in msgs)


def test_increment_goal_crosses_50_percent_sets_milestone_and_posts():
    """T84: crossing 50% sets milestone_50=TRUE and posts goal_milestone_50."""
    conn = _FakeConn()
    conn.cursor_obj._contributed = 0
    conn.cursor_obj.queue_fetchone({'contributed': 0, 'current': 0, 'target': 500,
                                    'completed': False,
                                    'milestone_25': False, 'milestone_50': False,
                                    'milestone_75': False})
    # Post-increment: current=250 (50%), milestone_25 already TRUE.
    conn.cursor_obj.queue_fetchone({'current': 250, 'target': 500,
                                    'milestone_25': True, 'milestone_50': False,
                                    'milestone_75': False})

    community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=1)

    assert not _has_milestone_update(conn.cursor_obj.log, 25)
    assert _has_milestone_update(conn.cursor_obj.log, 50), (
        "milestone_50 UPDATE expected when crossing 50%"
    )
    assert not _has_milestone_update(conn.cursor_obj.log, 75)

    msgs = _milestone_chat_messages(conn.cursor_obj.log)
    assert any(pct == 50 and '250' in m and '500' in m for pct, m in msgs)
    assert not any(pct == 25 for pct, _ in msgs)
    assert not any(pct == 75 for pct, _ in msgs)


def test_increment_goal_crosses_75_percent_sets_milestone_and_posts():
    """T84: crossing 75% sets milestone_75=TRUE and posts goal_milestone_75."""
    conn = _FakeConn()
    conn.cursor_obj._contributed = 0
    conn.cursor_obj.queue_fetchone({'contributed': 0, 'current': 0, 'target': 500,
                                    'completed': False,
                                    'milestone_25': False, 'milestone_50': False,
                                    'milestone_75': False})
    # Post-increment: current=375 (75%), 25 and 50 already TRUE.
    conn.cursor_obj.queue_fetchone({'current': 375, 'target': 500,
                                    'milestone_25': True, 'milestone_50': True,
                                    'milestone_75': False})

    community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=1)

    assert not _has_milestone_update(conn.cursor_obj.log, 25)
    assert not _has_milestone_update(conn.cursor_obj.log, 50)
    assert _has_milestone_update(conn.cursor_obj.log, 75), (
        "milestone_75 UPDATE expected when crossing 75%"
    )

    msgs = _milestone_chat_messages(conn.cursor_obj.log)
    assert any(pct == 75 and '375' in m and '500' in m for pct, m in msgs)
    assert not any(pct == 25 for pct, _ in msgs)
    assert not any(pct == 50 for pct, _ in msgs)


def test_increment_goal_at_100_percent_does_not_post_milestone():
    """T84 AC #4: 100% is the completion event (handled by
    check_goal_completion). increment_goal must not post a separate
    goal_milestone_* message at 100%, and must not re-fire milestones
    that are already TRUE.
    """
    conn = _FakeConn()
    conn.cursor_obj._contributed = 0
    conn.cursor_obj.queue_fetchone({'contributed': 0, 'current': 0, 'target': 500,
                                    'completed': False,
                                    'milestone_25': False, 'milestone_50': False,
                                    'milestone_75': False})
    # Post-increment: current=500 (100%), all milestones already TRUE.
    conn.cursor_obj.queue_fetchone({'current': 500, 'target': 500,
                                    'milestone_25': True, 'milestone_50': True,
                                    'milestone_75': True})

    community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=1)

    for pct in (25, 50, 75):
        assert not _has_milestone_update(conn.cursor_obj.log, pct), (
            f"no milestone_{pct} UPDATE expected when already TRUE, got one"
        )
    msgs = _milestone_chat_messages(conn.cursor_obj.log)
    assert msgs == [], f"no goal_milestone chat messages expected at 100%, got: {msgs}"


def test_increment_goal_already_set_milestone_does_not_double_fire():
    """T84: if a milestone column is already TRUE, crossing that threshold
    again must not re-issue the UPDATE or re-post the chat message.
    """
    conn = _FakeConn()
    conn.cursor_obj._contributed = 0
    conn.cursor_obj.queue_fetchone({'contributed': 0, 'current': 0, 'target': 500,
                                    'completed': False,
                                    'milestone_25': False, 'milestone_50': False,
                                    'milestone_75': False})
    # Post-increment: current=125 (25%), but milestone_25 is already TRUE.
    conn.cursor_obj.queue_fetchone({'current': 125, 'target': 500,
                                    'milestone_25': True, 'milestone_50': False,
                                    'milestone_75': False})

    community_goals.increment_goal(conn, 'goal_fish5000', user_id=1, amount=1)

    assert not _has_milestone_update(conn.cursor_obj.log, 25), (
        "milestone_25 UPDATE must not re-fire when already TRUE"
    )
    msgs = _milestone_chat_messages(conn.cursor_obj.log)
    assert not any(pct == 25 for pct, _ in msgs), (
        f"no goal_milestone_25 chat message expected when already set, got: {msgs}"
    )


# ─── 5. Optional integration test (real DB, real threads) ──────────────────


def _db_available():
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        return False
    try:
        c = psycopg2.connect(dsn, connect_timeout=2)
        c.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _db_available(), reason="DATABASE_URL unreachable; skipping integration test")
def test_concurrent_increment_goal_never_exceeds_cap():
    """T93 AC #3: two threads concurrently incrementing near the cap must
    together contribute at most the cap. The FOR UPDATE row lock is what
    guarantees this in production.
    """
    dsn = os.environ['DATABASE_URL']

    user_id = 990001 + (int(time.time()) % 1000)
    goal_id = 'goal_species100'  # per_player_cap = 15
    cap = next(g['per_player_cap'] for g in community_goals.COMMUNITY_GOAL_DEFS
               if g['goal_id'] == goal_id)
    amount_each = cap // 2 + 1  # 8; two threads * 8 = 16 > 15
    expected_total = cap        # 15, the per-player cap

    setup = psycopg2.connect(dsn)
    setup.autocommit = True
    with setup.cursor() as cur:
        # Ensure a users row exists for the FK on community_goal_contributions.
        cur.execute(
            "INSERT INTO users (id, username, password_hash, ip_address) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (user_id, f't93_{user_id}', 'x', '127.0.0.1'),
        )
        cur.execute(
            "DELETE FROM community_goal_contributions WHERE user_id = %s",
            (user_id,),
        )
    setup.close()

    results = []
    errors = []

    def worker():
        try:
            conn = psycopg2.connect(dsn)
            try:
                actual = community_goals.increment_goal(conn, goal_id, user_id, amount_each)
                conn.commit()
                results.append(actual)
            finally:
                conn.close()
        except Exception as e:  # pragma: no cover
            errors.append(repr(e))

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start(); t2.start()
    t1.join(); t2.join()

    assert not errors, f"thread errors: {errors}"
    assert len(results) == 2

    verify = psycopg2.connect(dsn)
    with verify.cursor() as cur:
        cur.execute(
            "SELECT contributed FROM community_goal_contributions "
            "WHERE goal_id = %s AND user_id = %s",
            (goal_id, user_id),
        )
        row = cur.fetchone()
    verify.close()

    contributed = row[0] if row else 0
    assert contributed == expected_total, (
        f"per-player cap violated: contributed={contributed}, expected={expected_total}, "
        f"individual results={results}"
    )
    assert sum(results) == expected_total, (
        f"sum of returned contributions {sum(results)} != cap {expected_total}; results={results}"
    )

    cleanup = psycopg2.connect(dsn)
    cleanup.autocommit = True
    with cleanup.cursor() as cur:
        cur.execute(
            "DELETE FROM community_goal_contributions WHERE user_id = %s",
            (user_id,),
        )
    cleanup.close()
