"""Tests for T108: cancel-arm endpoints for double-down and insurance.

T108 makes the armed indicators clickable to cancel. Two new POST endpoints:
  - /api/wager/double-down/cancel
  - /api/wager/insurance/cancel

Behaviour:
  - 200 + disarm if currently armed
  - 409 if not armed
  - DD cancel does NOT require the wager_double_down item
  - Insurance cancel does NOT require the wager_insurance item
  - Insurance cancel does NOT refund the consumed charge (T74: charge is
    wasted on a win too; the player takes the loss — that's the gamble)
"""
import os
import sys
import types
import importlib.util
import datetime as dt
from contextlib import contextmanager
from datetime import timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


sys.modules.setdefault('flask', _make_stub(
    'flask',
    Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
    jsonify=lambda x: x,
    request=None,
))
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
    get_latest_winners=lambda c, n: [],
    advance_season=lambda c: None,
))
sys.modules.setdefault('security', _make_stub('security', require_json=lambda: None))


class _FakeCursor:
    def __init__(self, log, fetchone_queue=None):
        self.log = log
        self._fetchone_queue = fetchone_queue or []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql, params))

    def fetchone(self):
        if not self._fetchone_queue:
            return None
        return self._fetchone_queue.pop(0)

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, fetchone_queue=None):
        self.log = []
        self._fetchone_queue = fetchone_queue or []
        self._cursors = [_FakeCursor(self.log, self._fetchone_queue)]

    def cursor(self, cursor_factory=None):
        return self._cursors[0]

    def commit(self):
        pass


@contextmanager
def _fake_db_connection():
    conn = _FakeConn()
    yield conn


sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)


# ════════════════════════════════════════════════════════════════════════════
# T108: double-down cancel
# ════════════════════════════════════════════════════════════════════════════
def test_dd_cancel_when_not_armed_returns_409():
    """T108: POST /api/wager/double-down/cancel when not armed → 409."""
    gs = {
        'owned_items': ['wager_double_down'],
        'double_down_pending': False,
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_double_down_cancel()
    assert isinstance(result, tuple)
    body, status = result
    assert status == 409
    assert body == {'error': 'Double down not armed'}


def test_dd_cancel_when_armed_returns_200_and_disarms():
    """T108: POST /api/wager/double-down/cancel when armed → 200, UPDATE
    sets double_down_pending = FALSE."""
    gs = {
        'owned_items': ['wager_double_down'],
        'double_down_pending': True,
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_double_down_cancel()
    assert isinstance(result, dict)
    assert result == {'ok': True}
    update = next((s for s, _ in conn.log if s.lstrip().upper().startswith('UPDATE')), None)
    assert update is not None
    assert 'double_down_pending = FALSE' in update
    sql_params = next(p for s, p in conn.log if s.lstrip().upper().startswith('UPDATE'))
    assert sql_params == (1,)


def test_dd_cancel_does_not_require_item_ownership():
    """T108: cancel is always allowed — no item ownership check."""
    # Player has NO wager_double_down item but somehow double_down_pending is True
    # (e.g. via direct DB or a future migration). Cancel must still succeed.
    gs = {
        'owned_items': [],
        'double_down_pending': True,
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_double_down_cancel()
    assert isinstance(result, dict)
    assert result == {'ok': True}


# ════════════════════════════════════════════════════════════════════════════
# T108: insurance cancel
# ════════════════════════════════════════════════════════════════════════════
def test_insurance_cancel_when_not_armed_returns_409():
    """T108: POST /api/insurance/cancel when not armed → 409."""
    gs = {
        'owned_items': ['wager_insurance'],
        'insurance_armed': False,
        'insurance_charges': 2,
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_insurance_cancel()
    assert isinstance(result, tuple)
    body, status = result
    assert status == 409
    assert body == {'error': 'Insurance not armed'}


def test_insurance_cancel_when_armed_returns_200_and_disarms_without_refund():
    """T108: POST /api/insurance/cancel when armed → 200, UPDATE
    sets insurance_armed = FALSE, charge NOT refunded (by design)."""
    gs = {
        'owned_items': ['wager_insurance'],
        'insurance_armed': True,
        'insurance_charges': 1,  # already consumed on arm
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_insurance_cancel()
    assert isinstance(result, dict)
    assert result == {'ok': True}
    update = next((s for s, _ in conn.log if s.lstrip().upper().startswith('UPDATE')), None)
    assert update is not None
    # The UPDATE must only set armed = FALSE — must NOT touch charges.
    assert 'insurance_armed = FALSE' in update
    assert 'insurance_charges' not in update, (
        "T108: insurance cancel must NOT refund the consumed charge (T119: the "
        "1 token is wasted on a win too; the player takes the loss — that's the gamble)"
    )


def test_insurance_cancel_does_not_require_item_ownership():
    """T108: cancel is always allowed — no item ownership check."""
    gs = {
        'owned_items': [],
        'insurance_armed': True,
        'insurance_charges': 0,
    }
    conn = _FakeConn(fetchone_queue=[gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST')
    _game.current_user = types.SimpleNamespace(id=1)

    result = _game.wager_insurance_cancel()
    assert isinstance(result, dict)
    assert result == {'ok': True}


# ════════════════════════════════════════════════════════════════════════════
# T108: structural — endpoints are wired in game.py
# ════════════════════════════════════════════════════════════════════════════
def test_cancel_endpoints_registered_in_game_py():
    """T108: both cancel routes must exist in game.py. T119: the
    insurance cancel URL was renamed from /api/wager/insurance/cancel
    to /api/insurance/cancel."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')).read()
    assert "/api/wager/double-down/cancel" in src
    assert "/api/insurance/cancel" in src
    assert "def wager_double_down_cancel" in src
    assert "def wager_insurance_cancel" in src


def test_cancel_handlers_wired_in_jsx():
    """T108: both cancel handlers and clickable armed buttons in app.jsx."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'app.jsx')).read()
    assert "handleCancelDoubleDown" in src
    assert "handleCancelInsurance" in src
    assert "handleCancelDoubleDown" in src
    assert "wager-cancel-btn" in src
    assert "(click to cancel)" in src


def test_cancel_btn_style_in_css():
    """T108: .wager-cancel-btn exists in styles.css with cursor:pointer."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'styles.css')).read()
    assert ".wager-cancel-btn" in src
    assert "cursor: pointer" in src
