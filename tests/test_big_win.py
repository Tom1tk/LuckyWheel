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


# ── Stub install/teardown (T242) ────────────────────────────────────────────
# Stubs are installed only during this module's tests (via setup_module) and
# restored in teardown_module, so other test files collected in the same
# pytest process see the real modules / whichever stubs the previous test
# file left behind.
_SENTINEL = object()
_STUB_PREV = {}  # name -> previous sys.modules entry (or _SENTINEL)
_GAME_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')
_game = None     # set in setup_module


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


def _stub_specs():
    """Return (name, factory) pairs for every module this test stubs."""
    _psycopg2_extras_stub = _make_stub(
        'psycopg2.extras', RealDictCursor=type('RealDictCursor', (), {}))
    return [
        ('flask', lambda: _make_stub(
            'flask',
            Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
            jsonify=lambda x: x,
            request=None,
        )),
        ('flask_login', lambda: _make_stub(
            'flask_login',
            current_user=None,
            login_required=lambda f: f,
            UserMixin=_UserMixinStub,
        )),
        ('psycopg2', lambda: _make_stub('psycopg2', extras=_psycopg2_extras_stub)),
        ('psycopg2.extras', lambda: _psycopg2_extras_stub),
        ('extensions', lambda: _make_stub(
            'extensions',
            limiter=types.SimpleNamespace(limit=_noop),
            csrf=types.SimpleNamespace(exempt=lambda f: f),
        )),
        ('seasons', lambda: _make_stub('seasons',
            ensure_current_season=lambda c: None,
            get_season_info=lambda c: {},
            get_latest_winners=lambda c, n: [],
            advance_season=lambda c: None,
        )),
        ('security', lambda: _make_stub('security', require_json=lambda: None)),
    ]


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


_posted = []


def _fake_post_system_message(conn, message, message_type='system', event_kind=None):
    _posted.append({'message': message, 'event_kind': event_kind})


def _fake_post_dedup_system_message(
    conn, message, user_id, event_kind, *, message_type='system',
):
    _posted.append({'message': message, 'event_kind': event_kind, 'user_id': user_id})


def setup_module(module):
    """Install stubs and load game.py once before any test in this module."""
    global _game
    for name, factory in _stub_specs():
        _STUB_PREV[name] = sys.modules.get(name, _SENTINEL)
        sys.modules[name] = factory()
    # The `db` stub needs the locally-defined _fake_db_connection, which
    # the stubs above don't see. Override it now that the contextmanager
    # exists.
    _STUB_PREV['db'] = sys.modules.get('db', _SENTINEL)
    sys.modules['db'] = _make_stub('db', db_connection=_fake_db_connection)

    # Force-reload game.py under the now-stubbed environment.
    sys.modules.pop('game', None)
    spec = importlib.util.spec_from_file_location('game', _GAME_PATH)
    _game = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_game)

    # Monkey-patch the side-effecting calls the helper makes.
    _game.post_system_message = _fake_post_system_message
    _game.post_dedup_system_message = _fake_post_dedup_system_message


def teardown_module(module):
    """Restore sys.modules and drop the stub-loaded game so the next test
    file sees real modules (or whichever stubs it installs)."""
    global _game
    sys.modules.pop('game', None)
    _game = None
    for name, prev in _STUB_PREV.items():
        if prev is _SENTINEL:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prev
    _STUB_PREV.clear()


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
    from format_wins import format_wins
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=5001), 'alice', 1)
    assert len(_posted) == 1
    assert _posted[0]['event_kind'] == 'big_win'
    assert format_wins(5001) in _posted[0]['message']
    assert 'alice' in _posted[0]['message']
    assert new_biggest == 5001


def test_big_win_escalates():
    """Win of 5500 with biggest=5001 fires; helper returns 5500."""
    from format_wins import format_wins
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=5001), _events(wins_delta=5500), 'alice', 1)
    assert len(_posted) == 1
    assert _posted[0]['event_kind'] == 'big_win'
    assert format_wins(5500) in _posted[0]['message']
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
    from format_wins import format_wins
    _posted.clear()
    conn = _FakeConn()
    biggest = 0
    for wins in (5001, 5500, 6000):
        biggest = _game._maybe_announce_big_win(
            conn, _gs(biggest=biggest), _events(wins_delta=wins), 'alice', 1)
    assert len(_posted) == 3
    assert biggest == 6000
    assert format_wins(5001) in _posted[0]['message']
    assert format_wins(5500) in _posted[1]['message']
    assert format_wins(6000) in _posted[2]['message']


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


# ---------------------------------------------------------------------------
# T230: skip_message kwarg. The /api/spin path posts a merged
# double-down/big-win message when a double-down lands a big win. The
# merged message conveys the big-win info, so _maybe_announce_big_win
# is called with skip_message=True to avoid a second chat post. The
# biggest_win_announced value must still be updated so non-DD big-wins
# keep escalating.
# ---------------------------------------------------------------------------

def test_skip_message_suppresses_post_but_still_updates_biggest():
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=12000), 'alice', 1,
        skip_message=True,
    )
    assert _posted == [], (
        f"T230: skip_message=True must suppress the big_win chat post. "
        f"Got: {_posted}"
    )
    # biggest_win_annotated is still updated so the per-player threshold
    # keeps escalating for non-DD wins.
    assert new_biggest == 12000, (
        f"T230: skip_message must still return the new biggest for the "
        f"persisted UPDATE. Got: {new_biggest}"
    )


def test_skip_message_false_still_posts():
    """Sanity check: skip_message=False (the default) posts as before."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=12000), 'alice', 1,
        skip_message=False,
    )
    assert len(_posted) == 1
    assert new_biggest == 12000


def test_skip_message_does_not_affect_below_threshold():
    """A win below BIG_WIN_THRESHOLD posts nothing either way."""
    _posted.clear()
    conn = _FakeConn()
    new_biggest = _game._maybe_announce_big_win(
        conn, _gs(biggest=0), _events(wins_delta=1000), 'alice', 1,
        skip_message=True,
    )
    assert _posted == []
    assert new_biggest == 0
