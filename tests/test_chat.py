"""Unit tests for chat.py's post_system_message throttle (no DB/Flask needed)."""
import sys
import os
import types
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import importlib.util


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)

sys.modules.setdefault('flask', _make_stub(
    'flask', Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
    jsonify=lambda x: x, request=None,
))
class _UserMixinStub:
    pass


# Stubs are process-wide (sys.modules) and shared across test files via
# setdefault -- match test_spin_logic.py's shape exactly (including
# UserMixin, which only models.py needs) so whichever test file's stub
# "wins" the race is still complete enough for every other file.
sys.modules.setdefault('flask_login', _make_stub(
    'flask_login', current_user=None, login_required=lambda f: f, UserMixin=_UserMixinStub,
))
sys.modules.setdefault('db', _make_stub('db', db_connection=lambda *a, **kw: None))
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


class _FakeCursor:
    def __init__(self, log, sql_log, rows=None):
        self.log = log
        self.sql_log = sql_log
        self.rows = rows or []
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def execute(self, sql, params=None):
        self.log.append((sql.strip().split()[0], params))
        self.sql_log.append((sql, params))
    def fetchall(self):
        return self.rows


class _FakeConn:
    def __init__(self, rows=None):
        self.log = []
        self.sql_log = []
        self.rows = rows or []
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def cursor(self):
        return _FakeCursor(self.log, self.sql_log, self.rows)


class _FakeArgs:
    def __init__(self, data):
        self._data = data
    def get(self, key, default=None):
        return self._data.get(key, default)


class _FakeRequest:
    def __init__(self, args_data):
        self.args = _FakeArgs(args_data)


def test_first_message_is_posted():
    _chat._system_message_last_posted.clear()
    conn = _FakeConn()
    _chat.post_system_message(conn, 'hello', 'event', event_kind='test_kind_a')
    inserts = [op for op, _ in conn.log if op == 'INSERT']
    assert len(inserts) == 1


def test_repeat_within_window_is_throttled():
    _chat._system_message_last_posted.clear()
    conn = _FakeConn()
    _chat.post_system_message(conn, 'first', 'event', event_kind='test_kind_b')
    _chat.post_system_message(conn, 'second', 'event', event_kind='test_kind_b')
    inserts = [op for op, _ in conn.log if op == 'INSERT']
    assert len(inserts) == 1  # second call throttled, no second INSERT


def test_different_kinds_throttle_independently():
    _chat._system_message_last_posted.clear()
    conn = _FakeConn()
    _chat.post_system_message(conn, 'a', 'event', event_kind='test_kind_c1')
    _chat.post_system_message(conn, 'b', 'event', event_kind='test_kind_c2')
    inserts = [op for op, _ in conn.log if op == 'INSERT']
    assert len(inserts) == 2  # different kinds, both go through


def test_posting_also_trims_old_messages():
    _chat._system_message_last_posted.clear()
    conn = _FakeConn()
    _chat.post_system_message(conn, 'hi', 'event', event_kind='test_kind_d')
    ops = [op for op, _ in conn.log]
    assert 'INSERT' in ops and 'DELETE' in ops


def test_max_chat_messages_constant_is_200():
    assert _chat.MAX_CHAT_MESSAGES == 200


def test_post_system_message_trim_uses_max_chat_messages():
    _chat._system_message_last_posted.clear()
    conn = _FakeConn()
    _chat.post_system_message(conn, 'hi', 'event', event_kind='test_kind_e')
    delete_sqls = [sql for sql, _ in conn.sql_log if sql.lstrip().upper().startswith('DELETE')]
    assert len(delete_sqls) == 1
    assert f'LIMIT {_chat.MAX_CHAT_MESSAGES}' in delete_sqls[0]
    assert 'LIMIT 200' in delete_sqls[0]


def test_rapid_fire_throttled_after_first():
    _chat._system_message_last_posted.clear()
    conn = _FakeConn()
    for i in range(10):
        _chat.post_system_message(conn, f'msg{i}', 'event', event_kind='test_kind_f')
    inserts = [op for op, _ in conn.log if op == 'INSERT']
    assert len(inserts) == 1


# ── T81: chat history cursor pagination ──────────────────────────────────

_FIXED_DT = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _row(mid, msg='m'):
    return (mid, f'user{mid}', msg, _FIXED_DT, 'user')


def _with_request_and_db(request_data, conn, fn):
    """Run fn() with chat.request / chat.db_connection patched, then restore."""
    saved_request = _chat.request
    saved_db = _chat.db_connection
    _chat.request = _FakeRequest(request_data)
    _chat.db_connection = lambda: conn
    try:
        return fn()
    finally:
        _chat.request = saved_request
        _chat.db_connection = saved_db


def test_get_chat_default_limit_50():
    conn = _FakeConn()
    _with_request_and_db({}, conn, _chat.get_chat)
    assert len(conn.sql_log) == 1
    sql, params = conn.sql_log[0]
    assert 'LIMIT %s' in sql
    assert 'ORDER BY id DESC' in sql
    # Default limit is 50 (not 30)
    assert params == (50,)


def test_get_chat_with_before_param():
    conn = _FakeConn()
    _with_request_and_db({'before': '100'}, conn, _chat.get_chat)
    assert len(conn.sql_log) == 1
    sql, params = conn.sql_log[0]
    assert 'WHERE id < %s' in sql
    assert 'ORDER BY id DESC' in sql
    assert 'LIMIT %s' in sql
    assert params == (100, 50)


def test_get_chat_with_custom_limit():
    conn = _FakeConn()
    _with_request_and_db({'limit': '10'}, conn, _chat.get_chat)
    assert len(conn.sql_log) == 1
    sql, params = conn.sql_log[0]
    assert 'LIMIT %s' in sql
    assert params == (10,)


def test_get_chat_ordered_desc():
    # Rows in id DESC order, ids 30..21
    rows = [_row(i) for i in range(30, 20, -1)]
    conn = _FakeConn(rows=rows)
    result = _with_request_and_db({}, conn, _chat.get_chat)
    # After reversed(), ids should be ASC: 21..30
    ids = [r['id'] for r in result]
    assert ids == list(range(21, 31))
    sql, _ = conn.sql_log[0]
    assert 'ORDER BY id DESC' in sql


def test_get_chat_with_before_returns_at_most_limit_rows():
    # Fake returns 5 rows; SQL says LIMIT 3 — at most 3 should pass through.
    rows = [_row(i) for i in range(5, 0, -1)]
    conn = _FakeConn(rows=rows)
    _with_request_and_db({'before': '100', 'limit': '3'}, conn, _chat.get_chat)
    sql, params = conn.sql_log[0]
    assert 'WHERE id < %s' in sql
    assert 'LIMIT %s' in sql
    assert params == (100, 3)


def test_get_chat_invalid_before_returns_400():
    conn = _FakeConn()
    # jsonify is stubbed to identity, so the returned tuple is (body, status)
    result = _with_request_and_db({'before': 'not-a-number'}, conn, _chat.get_chat)
    assert result[1] == 400
    assert conn.sql_log == []  # no SQL executed
