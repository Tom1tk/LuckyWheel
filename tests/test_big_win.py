"""T83: Per-player escalating big-win threshold tests.

The big-win chat message must fire only when wins_delta strictly exceeds the
player's previous biggest_win_announced. Ties and below-threshold wins do not
re-announce.
"""
import os
import sys
import types
import importlib.util
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


# Match the stub pattern from test_bounties.py / test_chat.py so all test
# files coexist no matter which loads first.
sys.modules.setdefault('flask', _make_stub(
    'flask',
    Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
    jsonify=lambda x: x,
    request=None,
))


class _UserMixinStub:
    pass


sys.modules.setdefault('flask_login', _make_stub(
    'flask_login',
    current_user=None,
    login_required=lambda f: f,
    UserMixin=_UserMixinStub,
))
_psycopg2_extras_stub = _make_stub(
    'psycopg2.extras', RealDictCursor=type('RealDictCursor', (), {}))
_psycopg2_stub = _make_stub('psycopg2', extras=_psycopg2_extras_stub)
sys.modules.setdefault('psycopg2', _psycopg2_stub)
sys.modules.setdefault('psycopg2.extras', _psycopg2_extras_stub)
sys.modules.setdefault('extensions', _make_stub(
    'extensions',
    limiter=types.SimpleNamespace(limit=_noop),
    csrf=types.SimpleNamespace(exempt=lambda f: f),
))
sys.modules.setdefault('seasons', _make_stub('seasons',
    ensure_current_season=lambda c: None,
    get_season_info=lambda c: {},
    advance_season=lambda c: None,
))
sys.modules.setdefault('security', _make_stub('security', require_json=lambda: None))


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

    def cursor(self, cursor_factory=None):
        return _FakeCursor(self.log)

    def commit(self):
        pass


@contextmanager
def _fake_db_connection():
    conn = _FakeConn()
    yield conn


sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


_posted = []


def _fake_post_system_message(conn, message, message_type='system', event_kind=None):
    _posted.append({'message': message, 'event_kind': event_kind})


def _fake_post_dedup_system_message(
    conn, message, user_id, event_kind, *, message_type='system',
):
    _posted.append({'message': message, 'event_kind': event_kind, 'user_id': user_id})


_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)

# Monkey-patch the side-effecting calls the helper makes.
_game.post_system_message = _fake_post_system_message
_game.post_dedup_system_message = _fake_post_dedup_system_message


def _gs(biggest=0, **overrides):
    g = {'biggest_win_announced': biggest}
    g.update(overrides)
    return g


def _events(wins_delta, result='win', mode='steady'):
    return {'result': result, 'wins_delta': wins_delta, 'active_wheel_mode': mode}


# ---------------------------------------------------------------------------
# T83 acceptance criteria
# ---------------------------------------------------------------------------

def test_big_win_fires_on_first_5k():
    """Win of 5001 with biggest=0 fires the message; helper returns 5001."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=5001), 'alice', 1)
    assert len(_posted) == 1
    assert _posted[0]['event_kind'] == 'big_win'
    assert '5001' in _posted[0]['message']
    assert 'alice' in _posted[0]['message']
    assert new_biggest == 5001


def test_big_win_escalates():
    """Win of 5500 with biggest=5001 fires; helper returns 5500."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=5001), _events(wins_delta=5500), 'alice', 1)
    assert len(_posted) == 1
    assert _posted[0]['event_kind'] == 'big_win'
    assert '5500' in _posted[0]['message']
    assert new_biggest == 5500


def test_big_win_does_not_fire_below_previous():
    """Win of 5100 with biggest=5500 does NOT fire; biggest stays 5500."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=5500), _events(wins_delta=5100), 'alice', 1)
    assert _posted == [], f"Expected no message, got: {_posted}"
    assert new_biggest == 5500  # unchanged


def test_big_win_does_not_fire_below_threshold():
    """Win of 1000 with biggest=0 does NOT fire (below 5000)."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=1000), 'alice', 1)
    assert _posted == []
    assert new_biggest == 0


def test_big_win_fires_three_times():
    """Sequential wins of 5001, 5500, 6000 each escalate and fire."""
    _posted.clear()
    conn = _FakeConn()
    biggest = 0
    for wins in (5001, 5500, 6000):
        biggest = _game._maybe_announce_big_win(
            conn, _gs(biggest=biggest), _events(wins_delta=wins), 'alice', 1)
    assert len(_posted) == 3
    assert biggest == 6000
    assert '5001' in _posted[0]['message']
    assert '5500' in _posted[1]['message']
    assert '6000' in _posted[2]['message']


# ---------------------------------------------------------------------------
# Additional edge cases (consistency with T82 + T83 spec wording)
# ---------------------------------------------------------------------------

def test_big_win_does_not_fire_on_lose():
    """A loss never produces a big-win message regardless of delta."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=10000, result='lose'), 'alice', 1)
    assert _posted == []
    assert new_biggest == 0


def test_big_win_does_not_fire_on_tie():
    """A win that exactly equals the previous biggest does not re-announce."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=5001), _events(wins_delta=5001), 'alice', 1)
    assert _posted == [], f"Tie should not re-announce, got: {_posted}"
    assert new_biggest == 5001


def test_big_win_fires_on_exact_threshold():
    """A win of exactly 5000 with biggest=0 fires (>= threshold)."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=5000), 'alice', 1)
    assert len(_posted) == 1
    assert new_biggest == 5000


def test_big_win_message_uses_active_wheel_mode():
    """The chat message embeds the active_wheel_mode from the event."""
    _posted.clear()
    conn = _FakeConn()
    _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=7000, mode='mirror'), 'bob', 1)
    assert len(_posted) == 1
    assert 'mirror' in _posted[0]['message']
