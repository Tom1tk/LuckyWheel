"""T91/B21: claiming a bounty must not post a system message to chat.

Bounty completions stay in the bounty panel only — never broadcast to chat.
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


# Match the stub pattern from test_chat.py / test_spin_logic.py so all test
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

    def fetchone(self):
        return None


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


def _stub_load_game_state(cur, user_id, for_update=False):
    return {'bounty_claimed_date': None}


def _stub_get_claim_rewards(conn, user_id, bounty_date):
    return {'cosmetic_fragments': 5, 'tokens': 200}


_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)

# Monkey-patch the symbols claim_bounty() touches.
_game.post_system_message = _fake_post_system_message
_game._load_game_state = _stub_load_game_state
_game.get_claim_rewards = _stub_get_claim_rewards


class _FakeRequest:
    method = 'POST'
    is_json = True
    json = {'bounty_id': 'bounty_wager5'}


class _FakeUser:
    id = 1
    username = 'testuser'


_game.request = _FakeRequest()
_game.current_user = _FakeUser()


def test_bounty_claim_does_not_post_system_message():
    """Claiming a completed bounty must not broadcast to chat (B21)."""
    _posted.clear()
    result = _game.claim_bounty()
    # Endpoint still returns the rewards payload on success.
    assert result == {'ok': True, 'rewards': {'cosmetic_fragments': 5, 'tokens': 200}}
    # Critical assertion: no chat broadcast.
    assert _posted == [], f"Expected no post_system_message calls, got: {_posted}"


# ---------------------------------------------------------------------------
# T87: Onboarding step 5 (terminal transition) — /api/bounties advances
# onboarding_step 3 → 5 in a single UPDATE, grants 100 wager_tokens, and
# surfaces `onboarding_advance: true` in the response. Steps 4/5 are no-ops.
# ---------------------------------------------------------------------------

_fake_bounty_status = [
    {'id': 'b1', 'progress': 0, 'target': 5, 'completed': False},
]


def _stub_bounty_status_for_onboarding(conn, user_id, bounty_date):
    return _fake_bounty_status


_game.get_bounty_status = _stub_bounty_status_for_onboarding


class _OnboardCursor:
    """Cursor that returns a configured onboarding_step from the SELECT."""

    def __init__(self, log, onboarding_step):
        self.log = log
        self._onboarding_step = onboarding_step
        self._fetched = False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append(sql)

    def fetchone(self):
        if not self._fetched:
            self._fetched = True
            return {'onboarding_step': self._onboarding_step}
        return None


class _OnboardConn:
    def __init__(self, onboarding_step):
        self.log = []
        self._cursor = _OnboardCursor(self.log, onboarding_step)

    def cursor(self, cursor_factory=None):
        return self._cursor

    def commit(self):
        pass


def _invoke_bounties_endpoint(onboarding_step):
    """Run get_bounties_endpoint() with a fake conn reporting `onboarding_step`.

    Returns (response_dict, conn_log) so callers can assert on both the
    response payload and the SQL that was issued.
    """
    conn = _OnboardConn(onboarding_step)

    @contextmanager
    def cm():
        yield conn

    original = _game.db_connection
    _game.db_connection = cm
    try:
        result = _game.get_bounties_endpoint()
    finally:
        _game.db_connection = original
    return result, conn.log


def test_bounty_endpoint_advances_step_3_to_5():
    """T87: step 3 → step 5 transition grants 100 wager_tokens and reports advance."""
    result, log = _invoke_bounties_endpoint(onboarding_step=3)

    assert result['onboarding_advance'] is True
    assert result['bounties'] == _fake_bounty_status
    updates = [sql for sql in log if sql.lstrip().upper().startswith('UPDATE')]
    assert len(updates) == 1, f"expected one UPDATE, got: {updates}"
    assert 'onboarding_step = 5' in updates[0]
    assert 'wager_tokens = wager_tokens + 100' in updates[0]


def test_bounty_endpoint_no_advance_at_step_4():
    """T87: step 4 is a no-op — no UPDATE, no reward, no advance flag."""
    result, log = _invoke_bounties_endpoint(onboarding_step=4)

    assert result['onboarding_advance'] is False
    updates = [sql for sql in log if sql.lstrip().upper().startswith('UPDATE')]
    assert updates == [], f"expected no UPDATE at step 4, got: {updates}"


def test_bounty_endpoint_no_advance_at_step_5():
    """T87: step 5 (terminal) is a no-op — cap honored."""
    result, log = _invoke_bounties_endpoint(onboarding_step=5)

    assert result['onboarding_advance'] is False
    updates = [sql for sql in log if sql.lstrip().upper().startswith('UPDATE')]
    assert updates == [], f"expected no UPDATE at step 5, got: {updates}"
