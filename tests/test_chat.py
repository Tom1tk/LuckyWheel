"""Unit tests for chat.py's post_system_message throttle (no DB/Flask needed)."""
import sys
import os
import types

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
    def __init__(self, log):
        self.log = log
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def execute(self, sql, params=None):
        self.log.append((sql.strip().split()[0], params))


class _FakeConn:
    def __init__(self):
        self.log = []
    def cursor(self):
        return _FakeCursor(self.log)


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
