"""T209: Chat message dedup tests.

Covers the live dedup behaviour (post_dedup_system_message) and the
retroactive migration 058 cleanup. Uses a stateful fake cursor so the
tests can assert the actual contents of chat_messages after a sequence
of dedup posts, not just the SQL pattern.
"""
import importlib.util
import os
import sys
import types
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Module stubs (mirror test_chat.py / test_auto_spin.py) ──────────────────

def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _StubUser:
    """Replacement for flask_login.current_user. A non-None user (with
    .id and .username) keeps test isolation happy: whichever test file's
    stub "wins" the sys.modules.setdefault race still provides a
    current_user that game.py's exception path can log on."""
    id = 1
    username = 'alice'


@contextmanager
def _fake_db_connection():
    """Context manager yielding None. The tests in this file pass their
    own _FakeConn() directly to post_dedup_system_message and never
    invoke db_connection(). A real context manager keeps the stub
    compatible with files like test_auto_spin.py that do use it."""
    yield None


sys.modules.setdefault('flask', _make_stub(
    'flask', Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
    jsonify=lambda x: x, request=None,
))
sys.modules.setdefault('flask_login', _make_stub(
    'flask_login', current_user=_StubUser(), login_required=lambda f: f,
    UserMixin=type('_UserMixinStub', (), {}),
))
sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))
sys.modules.setdefault('extensions', _make_stub(
    'extensions',
    limiter=types.SimpleNamespace(limit=_noop),
    csrf=types.SimpleNamespace(exempt=lambda f: f),
))
sys.modules.setdefault('security', _make_stub('security', require_json=lambda: None))


_spec = importlib.util.spec_from_file_location(
    'chat', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chat.py'),
)
_chat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_chat)


# ── Stateful fake cursor (supports SELECT/INSERT/DELETE on chat_messages) ──

class _FakeCursor:
    """A minimal chat_messages-backed cursor.

    Tracks rows in a list and serves SELECTs against them, so tests can
    assert the actual state after a sequence of dedup posts.
    """

    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self._next_id = max((r['id'] for r in self.rows), default=0) + 1
        self.log = []          # (op_first_word, params)
        self.sql_log = []      # (full_sql, params)
        self._fetchone_result = None
        self._fetchall_result = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql.strip().split()[0], params))
        self.sql_log.append((sql, params))
        s = sql.strip()
        s_upper = s.upper()

        # Dedup lookup: SELECT id FROM chat_messages WHERE user_id=%s AND event_kind=%s ...
        if (s_upper.startswith('SELECT ID FROM CHAT_MESSAGES')
                and 'ORDER BY ID DESC' in s_upper
                and 'LIMIT 1' in s_upper):
            user_id, event_kind, message_type = params
            matching = [r for r in self.rows
                        if r['user_id'] == user_id
                        and r['event_kind'] == event_kind
                        and r['message_type'] == message_type]
            matching.sort(key=lambda r: r['id'], reverse=True)
            self._fetchone_result = (matching[0]['id'],) if matching else None
            return

        # Single-row delete by id (the dedup DELETE)
        if s_upper.startswith('DELETE FROM CHAT_MESSAGES WHERE ID ='):
            target_id = params[0]
            self.rows = [r for r in self.rows if r['id'] != target_id]
            return

        # INSERT INTO chat_messages ...
        if s_upper.startswith('INSERT INTO CHAT_MESSAGES'):
            # post_dedup_system_message: (user_id, message, message_type, event_kind)
            # post_system_message (fall-through): (message, message_type)
            if len(params) == 4:
                user_id, message, message_type, event_kind = params
                new_row = {
                    'id': self._next_id,
                    'user_id': user_id,
                    'username': 'SYSTEM',
                    'message': message,
                    'message_type': message_type,
                    'event_kind': event_kind,
                }
            else:
                # post_system_message inlines NULL and 'SYSTEM' literally.
                message, message_type = params
                new_row = {
                    'id': self._next_id,
                    'user_id': None,
                    'username': 'SYSTEM',
                    'message': message,
                    'message_type': message_type,
                    'event_kind': None,
                }
            self._next_id += 1
            self.rows.append(new_row)
            return

        # Trim DELETE (DELETE FROM chat_messages WHERE id NOT IN ...) — no-op in tests.
        if s_upper.startswith('DELETE FROM CHAT_MESSAGES'):
            return

    def fetchone(self):
        return self._fetchone_result

    def fetchall(self):
        return list(self._fetchall_result) if self._fetchall_result is not None else []


class _FakeConn:
    def __init__(self, rows=None):
        self.cursor_obj = _FakeCursor(rows=rows)
        self.log = self.cursor_obj.log
        self.sql_log = self.cursor_obj.sql_log

    def cursor(self, cursor_factory=None):
        return self.cursor_obj


# ── DEDUP_EVENT_KINDS set shape ─────────────────────────────────────────────

def test_dedup_event_kinds_set():
    """DEDUP_EVENT_KINDS is a frozenset with the 6 expected members.

    T222: 'prestige' is now in the set (per-user dedup, latest level only).
    """
    kinds = _chat.DEDUP_EVENT_KINDS
    assert isinstance(kinds, frozenset), f"expected frozenset, got {type(kinds)}"
    assert kinds == frozenset({
        'big_win',
        'hot_streak',
        'goal_milestone_25',
        'goal_milestone_50',
        'goal_milestone_75',
        'prestige',
    })


def test_dedup_event_kinds_excludes_first_spin():
    """first_spin is NOT in DEDUP_EVENT_KINDS — it's a historical record.

    T222: prestige moved INTO the set (it IS deduped now). Only first_spin
    is still excluded.
    """
    assert 'first_spin' not in _chat.DEDUP_EVENT_KINDS


def test_dedup_event_kinds_includes_prestige():
    """T222: prestige is now in DEDUP_EVENT_KINDS — per-user dedup."""
    assert 'prestige' in _chat.DEDUP_EVENT_KINDS


def test_dedup_event_kinds_size():
    """Sanity: exactly 6 members, no more no fewer."""
    assert len(_chat.DEDUP_EVENT_KINDS) == 6


# ── Live dedup behaviour ────────────────────────────────────────────────────

def _reset_throttle():
    _chat._system_message_last_posted.clear()


def _user_id_posts(user_id, event_kind, count, message_prefix=''):
    """Post `count` dedup system messages for the given (user_id, event_kind)."""
    conn = _FakeConn()
    for i in range(count):
        _chat.post_dedup_system_message(
            conn,
            f'{message_prefix}{i}',
            user_id,
            event_kind=event_kind,
        )
    return conn


def test_big_win_dedup():
    """Post 5 big_wins for the same user; only the most recent survives."""
    _reset_throttle()
    conn = _user_id_posts(user_id=42, event_kind='big_win', count=5)
    big_wins = [r for r in conn.cursor_obj.rows
                if r['event_kind'] == 'big_win' and r['user_id'] == 42]
    assert len(big_wins) == 1, (
        f"expected 1 big_win row for user 42, got {len(big_wins)}: {big_wins}"
    )
    # The surviving row is the most recent (i=4 in our loop)
    assert big_wins[0]['message'] == '4'


def test_hot_streak_dedup():
    """Post 5 hot_streak milestones; only the most recent survives."""
    _reset_throttle()
    conn = _user_id_posts(user_id=7, event_kind='hot_streak', count=5)
    hot = [r for r in conn.cursor_obj.rows
           if r['event_kind'] == 'hot_streak' and r['user_id'] == 7]
    assert len(hot) == 1
    assert hot[0]['message'] == '4'


def test_goal_milestone_dedup():
    """All three goal_milestone kinds coexist, each at most one per user."""
    _reset_throttle()
    conn = _FakeConn()
    user_id = 99
    for i in range(3):
        _chat.post_dedup_system_message(
            conn, f'25-{i}', user_id, event_kind='goal_milestone_25',
        )
        _chat.post_dedup_system_message(
            conn, f'50-{i}', user_id, event_kind='goal_milestone_50',
        )
        _chat.post_dedup_system_message(
            conn, f'75-{i}', user_id, event_kind='goal_milestone_75',
        )
    # Trigger a second 25% milestone (e.g. via re-trigger) — should dedup with the first.
    _chat.post_dedup_system_message(
        conn, '25-retrigger', user_id, event_kind='goal_milestone_25',
    )

    by_kind = {}
    for r in conn.cursor_obj.rows:
        if r['user_id'] == user_id:
            by_kind.setdefault(r['event_kind'], []).append(r)
    for kind in ('goal_milestone_25', 'goal_milestone_50', 'goal_milestone_75'):
        assert len(by_kind.get(kind, [])) == 1, (
            f"{kind} should have exactly 1 row, got {len(by_kind.get(kind, []))}: {by_kind.get(kind)}"
        )
    # Most recent 25% message preserved.
    assert by_kind['goal_milestone_25'][0]['message'] == '25-retrigger'


def test_first_spin_not_deduped():
    """first_spin is NOT in DEDUP_EVENT_KINDS — post_dedup_system_message
    must NOT issue the dedup SELECT/DELETE pattern for it. We verify by
    checking the SQL log: no SELECT with user_id + event_kind + message_type
    filter (the dedup lookup uses all three; the trim DELETE has a different
    shape — a SELECT id inside its subquery without those WHERE filters).

    We use unique event_kinds (first_spin_1, first_spin_2) so the 30s
    post_system_message throttle doesn't drop the 2nd insert, which would
    otherwise mask the dedup behaviour we want to observe.
    """
    _reset_throttle()
    conn = _FakeConn()
    _chat.post_dedup_system_message(conn, 'first', 1, event_kind='first_spin_1')
    _chat.post_dedup_system_message(conn, 'second', 1, event_kind='first_spin_2')
    assert len(conn.cursor_obj.rows) == 2, (
        f"expected both first_spin messages to persist, got: {conn.cursor_obj.rows}"
    )
    # No dedup SELECT (the dedup lookup filters by user_id + event_kind +
    # message_type — the trim DELETE's subquery has none of those).
    dedup_lookups = [
        sql for sql, _ in conn.cursor_obj.sql_log
        if 'SELECT id FROM chat_messages' in sql
        and 'user_id = %s' in sql
    ]
    assert dedup_lookups == [], (
        f"dedup SELECT should not run for first_spin, got: {dedup_lookups}"
    )


def test_prestige_deduped():
    """T222: prestige is in DEDUP_EVENT_KINDS — multiple prestige posts
    for the same user dedup to the latest. The user's previous prestige
    message is removed; the new one is inserted in its place.
    """
    _reset_throttle()
    conn = _FakeConn()
    # First prestige: Level 1
    _chat.post_dedup_system_message(conn, '⭐ alice reached Prestige Level 1!', 1, event_kind='prestige')
    assert len(conn.cursor_obj.rows) == 1
    assert conn.cursor_obj.rows[0]['message'] == '⭐ alice reached Prestige Level 1!'

    # Re-prestige to Level 2: the old one must be deleted, the new one inserted.
    _chat.post_dedup_system_message(conn, '⭐ alice reached Prestige Level 2!', 1, event_kind='prestige')
    prestige_rows = [r for r in conn.cursor_obj.rows if r.get('event_kind') == 'prestige']
    assert len(prestige_rows) == 1, (
        f"expected exactly 1 prestige row for user 1, got {len(prestige_rows)}: {prestige_rows}"
    )
    assert prestige_rows[0]['message'] == '⭐ alice reached Prestige Level 2!', (
        f"expected latest prestige, got: {prestige_rows[0]['message']}"
    )

    # Re-prestige to Level 3: same story.
    _chat.post_dedup_system_message(conn, '⭐ alice reached Prestige Level 3!', 1, event_kind='prestige')
    prestige_rows = [r for r in conn.cursor_obj.rows if r.get('event_kind') == 'prestige']
    assert len(prestige_rows) == 1
    assert prestige_rows[0]['message'] == '⭐ alice reached Prestige Level 3!'


def test_prestige_dedup_isolated_per_user():
    """T222: prestige dedup is per-user. Alice's Level 2 doesn't
    delete Bob's Level 5 — each player keeps their own latest."""
    _reset_throttle()
    initial = [
        {'id': 1, 'user_id': 1, 'username': 'alice', 'message': 'L1',
         'message_type': 'system', 'event_kind': 'prestige'},
        {'id': 2, 'user_id': 2, 'username': 'bob',   'message': 'L5',
         'message_type': 'system', 'event_kind': 'prestige'},
    ]
    conn = _FakeConn(rows=initial)
    # Alice re-prestiges: only her L1 should be deleted, Bob's L5 stays.
    _chat.post_dedup_system_message(conn, '⭐ alice reached Prestige Level 2!', 1, event_kind='prestige')
    prestige_rows = [r for r in conn.cursor_obj.rows if r.get('event_kind') == 'prestige']
    assert len(prestige_rows) == 2, (
        f"expected 2 prestige rows (alice L2 + bob L5), got {prestige_rows}"
    )
    assert {r['message'] for r in prestige_rows} == {'⭐ alice reached Prestige Level 2!', 'L5'}


def test_user_messages_not_deduped():
    """message_type='user' rows are never touched by dedup (event_kind=NULL)."""
    conn = _FakeConn()
    # Simulate 5 user messages (the post_dedup path doesn't insert these,
    # but we can verify the dedup logic doesn't touch them by pre-populating
    # user messages and running a dedup post for the same user).
    initial_user_rows = [
        {'id': i, 'user_id': 1, 'username': 'u', 'message': f'user{i}',
         'message_type': 'user', 'event_kind': None}
        for i in range(1, 6)
    ]
    conn = _FakeConn(rows=initial_user_rows)
    _reset_throttle()
    _chat.post_dedup_system_message(conn, 'big', 1, event_kind='big_win')
    user_rows = [r for r in conn.cursor_obj.rows if r['message_type'] == 'user']
    assert len(user_rows) == 5, (
        f"user messages must be preserved, got {len(user_rows)}: {user_rows}"
    )


def test_dedup_isolated_per_user():
    """User A's big_win does not delete user B's big_win."""
    _reset_throttle()
    conn = _FakeConn()
    _chat.post_dedup_system_message(conn, 'a1', 1, event_kind='big_win')
    _chat.post_dedup_system_message(conn, 'b1', 2, event_kind='big_win')
    _chat.post_dedup_system_message(conn, 'a2', 1, event_kind='big_win')
    big_wins = [r for r in conn.cursor_obj.rows if r['event_kind'] == 'big_win']
    # user 1: a2 (most recent) survives, a1 deleted
    # user 2: b1 survives
    user1 = [r for r in big_wins if r['user_id'] == 1]
    user2 = [r for r in big_wins if r['user_id'] == 2]
    assert len(user1) == 1 and user1[0]['message'] == 'a2'
    assert len(user2) == 1 and user2[0]['message'] == 'b1'


def test_non_dedup_kind_falls_through_to_post_system_message():
    """A kind NOT in DEDUP_EVENT_KINDS falls through to post_system_message."""
    _reset_throttle()
    conn = _FakeConn()
    # 'jackpot' is not in DEDUP_EVENT_KINDS per T209 (jackpots share big_win's kind).
    _chat.post_dedup_system_message(conn, 'msg', 1, event_kind='jackpot')
    # Falls through to post_system_message, which inserts with user_id=NULL
    # and 'SYSTEM' username. event_kind is NULL (post_system_message doesn't
    # store event_kind on insert).
    assert len(conn.cursor_obj.rows) == 1
    assert conn.cursor_obj.rows[0]['message'] == 'msg'


def test_dedup_empty_message_is_noop():
    """Empty messages are silently dropped, same as post_system_message."""
    _reset_throttle()
    conn = _FakeConn()
    _chat.post_dedup_system_message(conn, '', 1, event_kind='big_win')
    assert conn.cursor_obj.rows == []


def test_dedup_only_matches_same_event_kind():
    """big_win dedup doesn't touch hot_streak rows for the same user."""
    _reset_throttle()
    conn = _FakeConn()
    _chat.post_dedup_system_message(conn, 'bw', 1, event_kind='big_win')
    _chat.post_dedup_system_message(conn, 'hs', 1, event_kind='hot_streak')
    _chat.post_dedup_system_message(conn, 'bw2', 1, event_kind='big_win')
    rows = {r['event_kind']: r for r in conn.cursor_obj.rows}
    assert 'big_win' in rows and rows['big_win']['message'] == 'bw2'
    assert 'hot_streak' in rows and rows['hot_streak']['message'] == 'hs'


# ── Migration 058 retroactive cleanup ───────────────────────────────────────

def _apply_migration_058(conn):
    """Execute the migration 058 DELETE statement against the fake conn.

    The fake's chat_messages state is a list of dicts; we apply the same
    ROW_NUMBER() logic the migration uses. Tests pre-populate `rows` with
    the backlog they want to test.
    """
    cur = conn.cursor_obj
    dedup_set = {
        'big_win', 'hot_streak',
        'goal_milestone_25', 'goal_milestone_50', 'goal_milestone_75',
    }
    # Group rows by (user_id, event_kind) and keep the most recent (highest id)
    # for the dedup-eligible pairs; drop the rest.
    keep_ids = set()
    for r in cur.rows:
        if r['message_type'] == 'system' and r['event_kind'] in dedup_set:
            keep_ids.add(r['id'])  # placeholder; resolved below
    # For each (user_id, event_kind) keep only the row with the highest id.
    survivors = []
    seen = set()
    sorted_rows = sorted(cur.rows, key=lambda r: r['id'], reverse=True)
    for r in sorted_rows:
        if r['message_type'] == 'system' and r['event_kind'] in dedup_set:
            key = (r['user_id'], r['event_kind'])
            if key in seen:
                continue  # older duplicate -> delete
            seen.add(key)
        survivors.append(r)
    cur.rows = survivors


def _make_row(rid, user_id, event_kind, message='m', message_type='system'):
    return {
        'id': rid,
        'user_id': user_id,
        'username': 'SYSTEM' if message_type == 'system' else 'u',
        'message': message,
        'message_type': message_type,
        'event_kind': event_kind,
    }


def test_migration_058_retroactive_cleanup():
    """Migration keeps only the most recent (user_id, event_kind) row;
    older duplicates are deleted."""
    rows = [
        _make_row(1, 42, 'big_win', 'oldest'),
        _make_row(2, 42, 'big_win', 'middle'),
        _make_row(3, 42, 'big_win', 'newest'),
    ]
    conn = _FakeConn(rows=rows)
    _apply_migration_058(conn)
    survivors = [r for r in conn.cursor_obj.rows
                 if r['user_id'] == 42 and r['event_kind'] == 'big_win']
    assert len(survivors) == 1
    assert survivors[0]['message'] == 'newest'
    assert survivors[0]['id'] == 3


def test_migration_058_preserves_first_spin_and_prestige():
    """Migration 058's HISTORICAL behaviour: it preserved first_spin and
    prestige. T222 (migration 064) changed this so prestige is now deduped
    (see test_migration_064_dedups_prestige below). first_spin is still
    preserved."""
    rows = [
        _make_row(1, 42, 'first_spin', 'fs-1'),
        _make_row(2, 42, 'first_spin', 'fs-2'),
        _make_row(3, 42, 'prestige', 'p-1'),
        _make_row(4, 42, 'prestige', 'p-2'),
        _make_row(5, 42, 'prestige', 'p-3'),
    ]
    conn = _FakeConn(rows=rows)
    _apply_migration_058(conn)
    fs = [r for r in conn.cursor_obj.rows if r['event_kind'] == 'first_spin']
    pr = [r for r in conn.cursor_obj.rows if r['event_kind'] == 'prestige']
    assert len(fs) == 2, f"all first_spin rows preserved (058), got: {fs}"
    # 058 did NOT dedup prestige — this is the historical behaviour. T222
    # changed this; see test_migration_064_dedups_prestige for the new rule.
    assert len(pr) == 3, f"058 preserved all prestige rows, got: {pr}"


def _apply_migration_064(conn):
    """Re-implementation of migration 064 for testing.

    064: backfill user_id from message content, then keep only the
    latest prestige message per user. Unlike 058, prestige is now
    dedup-eligible.
    """
    cur = conn.cursor_obj
    # Step 1: backfill user_id by matching the username embedded in
    # the message text (⭐ {user} reached Prestige Level {N}!).
    import re
    for r in cur.rows:
        if r.get('event_kind') == 'prestige' and r.get('user_id') is None:
            m = re.match(r'^⭐ (\S+) reached Prestige Level', r['message'])
            if m:
                # In a real DB we'd look up users.username. For the test
                # FakeConn we just assign a synthetic user_id from the row.
                r['user_id'] = 100 + len(r['message'])  # deterministic
    # Step 2: keep only the latest prestige per user (max id).
    by_user = {}
    for r in cur.rows:
        if r.get('event_kind') == 'prestige' and r.get('user_id') is not None:
            uid = r['user_id']
            if uid not in by_user or r['id'] > by_user[uid]['id']:
                by_user[uid] = r
    cur.rows = [r for r in cur.rows
                if r.get('event_kind') != 'prestige'
                or (r.get('user_id') is not None and r.get('id') == by_user[r['user_id']]['id'])]


def test_migration_064_dedups_prestige():
    """T222 / migration 064: keeps only the latest prestige per user.
    Older prestige messages for the same user are deleted."""
    rows = [
        _make_row(1, 2, 'prestige', '⭐ alice reached Prestige Level 1!'),
        _make_row(2, 2, 'prestige', '⭐ alice reached Prestige Level 2!'),
        _make_row(3, 2, 'prestige', '⭐ alice reached Prestige Level 3!'),
        _make_row(4, 3, 'prestige', '⭐ bob reached Prestige Level 5!'),
        _make_row(5, 3, 'prestige', '⭐ bob reached Prestige Level 6!'),
    ]
    conn = _FakeConn(rows=rows)
    _apply_migration_064(conn)
    alice = [r for r in conn.cursor_obj.rows
             if r['event_kind'] == 'prestige' and 'alice' in r['message']]
    bob = [r for r in conn.cursor_obj.rows
           if r['event_kind'] == 'prestige' and 'bob' in r['message']]
    assert len(alice) == 1, f"alice: expected 1 latest, got {len(alice)}"
    assert alice[0]['id'] == 3, f"alice: expected latest (id=3), got {alice[0]}"
    assert len(bob) == 1, f"bob: expected 1 latest, got {len(bob)}"
    assert bob[0]['id'] == 5, f"bob: expected latest (id=5), got {bob[0]}"


def test_migration_064_preserves_first_spin():
    """first_spin is still preserved (not in DEDUP_EVENT_KINDS)."""
    rows = [
        _make_row(1, 2, 'first_spin', 'fs-1'),
        _make_row(2, 2, 'first_spin', 'fs-2'),
        _make_row(3, 2, 'prestige',  'p-1'),
        _make_row(4, 2, 'prestige',  'p-2'),
    ]
    conn = _FakeConn(rows=rows)
    _apply_migration_064(conn)
    fs = [r for r in conn.cursor_obj.rows if r['event_kind'] == 'first_spin']
    pr = [r for r in conn.cursor_obj.rows if r['event_kind'] == 'prestige']
    assert len(fs) == 2, f"first_spin preserved, got: {fs}"
    assert len(pr) == 1, f"prestige deduped to latest, got: {pr}"


def test_migration_058_isolated_per_user():
    """User A's dedup-eligible messages do not affect user B's."""
    rows = [
        _make_row(1, 1, 'big_win', 'a1'),
        _make_row(2, 1, 'big_win', 'a2'),
        _make_row(3, 2, 'big_win', 'b1'),
        _make_row(4, 2, 'big_win', 'b2'),
    ]
    conn = _FakeConn(rows=rows)
    _apply_migration_058(conn)
    a = [r for r in conn.cursor_obj.rows if r['user_id'] == 1 and r['event_kind'] == 'big_win']
    b = [r for r in conn.cursor_obj.rows if r['user_id'] == 2 and r['event_kind'] == 'big_win']
    assert len(a) == 1 and a[0]['id'] == 2
    assert len(b) == 1 and b[0]['id'] == 4


def test_migration_058_handles_all_three_goal_milestones():
    """All three goal_milestone_* kinds dedup independently."""
    rows = [
        _make_row(1, 1, 'goal_milestone_25', '25-old'),
        _make_row(2, 1, 'goal_milestone_25', '25-new'),
        _make_row(3, 1, 'goal_milestone_50', '50-only'),
        _make_row(4, 1, 'goal_milestone_75', '75-only'),
    ]
    conn = _FakeConn(rows=rows)
    _apply_migration_058(conn)
    by_kind = {}
    for r in conn.cursor_obj.rows:
        by_kind.setdefault(r['event_kind'], []).append(r)
    assert len(by_kind['goal_milestone_25']) == 1
    assert by_kind['goal_milestone_25'][0]['id'] == 2
    assert len(by_kind['goal_milestone_50']) == 1
    assert len(by_kind['goal_milestone_75']) == 1


def test_migration_058_idempotent_on_rerun():
    """Re-running the migration on an already-deduped set is a no-op."""
    rows = [
        _make_row(1, 1, 'big_win', 'only'),
    ]
    conn = _FakeConn(rows=rows)
    _apply_migration_058(conn)
    snapshot = list(conn.cursor_obj.rows)
    _apply_migration_058(conn)  # second pass
    assert conn.cursor_obj.rows == snapshot


# ── chat_triggers.big_win_msg format ────────────────────────────────────────
# T221: was_jackpot kwarg is removed. The big_win_msg now only emits the
# regular 💰 format. Jackpots are silenced entirely.

def test_big_win_msg_non_jackpot_default():
    """Default returns the 💰 format."""
    import chat_triggers
    from format_wins import format_wins
    msg = chat_triggers.big_win_msg('alice', 6000, 'steady')
    assert msg == f'💰 alice won {format_wins(6000)} wins in steady mode!'


def test_big_win_msg_rejects_was_jackpot_kwarg():
    """T221: passing was_jackpot raises TypeError (no silent fall-through)."""
    import chat_triggers
    import pytest
    with pytest.raises(TypeError):
        chat_triggers.big_win_msg('bob', 8000, 'mirror', was_jackpot=True)
