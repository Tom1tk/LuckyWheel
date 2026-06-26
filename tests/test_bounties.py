"""T91/B21: claiming a bounty must not post a system message to chat.

Bounty completions stay in the bounty panel only — never broadcast to chat.

Also: T117 — per-bounty claim overhaul (claim flow, payload key,
position-based rewards, no cosmetic fragments, claim independence).
"""
import os
import sys
import types
import importlib.util
import datetime as dt
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


def _stub_get_claim_rewards_for_bounty(conn, user_id, bounty_date, bounty_id):
    return {'tokens': 2, 'cosmetic_fragments': 0}


# T117: per-bounty claim flow reads a row from `bounty_progress` (via SELECT
# FOR UPDATE) to confirm `completed = TRUE` and `claimed = FALSE` before
# flipping `claimed = TRUE` and crediting tokens. The legacy _FakeCursor
# returns None from fetchone, which trips the new "Bounty not completed"
# branch, so this test uses a richer cursor.
class _ClaimCursor:
    """Cursor that returns a 'completed but unclaimed' bounty_progress row."""

    def __init__(self, log):
        self.log = log
        self._fetched = False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql.strip().split()[0], params))

    def fetchone(self):
        if not self._fetched:
            self._fetched = True
            return {'completed': True, 'claimed': False}
        return None


class _ClaimConn:
    def __init__(self):
        self.log = []

    def cursor(self, cursor_factory=None):
        return _ClaimCursor(self.log)

    def commit(self):
        pass


@contextmanager
def _fake_db_connection_for_claim():
    yield _ClaimConn()


_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)

# Monkey-patch the symbols claim_bounty() touches (T117).
_game.post_system_message = _fake_post_system_message
_game.get_claim_rewards_for_bounty = _stub_get_claim_rewards_for_bounty


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
    """Claiming a completed bounty must not broadcast to chat (B21/T117)."""
    _posted.clear()
    original_db = _game.db_connection
    _game.db_connection = _fake_db_connection_for_claim
    try:
        result = _game.claim_bounty()
    finally:
        _game.db_connection = original_db
    # Endpoint still returns the per-bounty rewards payload on success.
    assert result == {'ok': True, 'rewards': {'tokens': 2, 'cosmetic_fragments': 0}}
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
    """T87/T119: step 3 → step 5 transition advances the step but no
    longer grants 100 tokens. T119 removed the onboarding token grant —
    the only token sources are now: 3/day free claim, 1/2/3 per bounty,
    +5 on first fish_to_wager purchase."""
    result, log = _invoke_bounties_endpoint(onboarding_step=3)

    assert result['onboarding_advance'] is True
    assert result['bounties'] == _fake_bounty_status
    updates = [sql for sql in log if sql.lstrip().upper().startswith('UPDATE')]
    assert len(updates) == 1, f"expected one UPDATE, got: {updates}"
    assert 'onboarding_step = 5' in updates[0]
    # T119: the 100-token grant is gone. The UPDATE only flips the step.
    assert 'wager_tokens' not in updates[0], (
        f"T119: the 100-token grant is removed, but UPDATE still references "
        f"wager_tokens: {updates[0]}"
    )


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


# ════════════════════════════════════════════════════════════════════════════
# T117: Bounty claim overhaul — per-bounty rewards, payload key fix,
# no cosmetic fragments, per-bounty independence.
# ════════════════════════════════════════════════════════════════════════════


def _load_bounties_module():
    """Import bounties.py with no DB required (the new helpers are pure)."""
    spec = importlib.util.spec_from_file_location(
        'bounties_under_test',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bounties.py'),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_payload_uses_bounty_id_key():
    """T117 AC#5: /api/bounties response payload uses `bounty_id` (not `id`).

    The legacy payload used `id` which the JS read as `b.bounty_id` (undefined)
    and posted `{}` to /api/bounties/claim, triggering the 400. Confirms the
    new key name is present on every entry, with a 1-indexed `position`.
    """
    bounties = _load_bounties_module()
    user_id = 42
    bounty_date = dt.date(2026, 6, 26)

    class _ProgCursor:
        def __init__(self):
            self.log = []
            self._calls = 0

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, sql, params=None):
            self.log.append((sql, params))
            self._calls += 1

        def fetchone(self):
            # Mirror the shape the real SELECT returns when there's no row.
            return None

    class _ProgConn:
        def __init__(self):
            self.cursor_obj = _ProgCursor()

        def cursor(self, cursor_factory=None):
            return self.cursor_obj

        def commit(self):
            pass

    conn = _ProgConn()
    result = bounties.get_bounty_status(conn, user_id, bounty_date)

    assert len(result) == 3, f"expected 3 daily bounties, got {len(result)}"
    for entry in result:
        assert 'bounty_id' in entry, (
            f"payload entry missing 'bounty_id' (the legacy key was 'id'): {entry}"
        )
        assert 'id' not in entry, (
            f"payload entry still uses legacy 'id' key: {entry}"
        )
        assert 'position' in entry, "payload entry missing 'position' (1-indexed)"
        assert 'claimed' in entry, "payload entry missing 'claimed' flag"

    positions = [e['position'] for e in result]
    assert positions == [1, 2, 3], f"positions should be 1-indexed [1,2,3], got {positions}"


def test_per_bounty_token_amounts():
    """T117 AC#2: position 1 → 1 token, #2 → 2, #3 → 3. Max 6/day.

    Pure-Python test: the function is deterministic for a given (user, date).
    """
    bounties = _load_bounties_module()
    user_id = 99
    bounty_date = dt.date(2026, 6, 26)

    class _NoOpConn:
        def cursor(self, cursor_factory=None):
            raise AssertionError("get_claim_rewards_for_bounty must not touch the DB")

    selected = bounties.get_daily_bounties(user_id, bounty_date)
    assert len(selected) == 3

    # The function maps each bounty to its 1-indexed position in `selected`.
    by_id = {b['id']: i + 1 for i, b in enumerate(selected)}

    for bounty_id, expected in by_id.items():
        rewards = bounties.get_claim_rewards_for_bounty(
            _NoOpConn(), user_id, bounty_date, bounty_id,
        )
        assert rewards == {
            'tokens': expected,
            'cosmetic_fragments': 0,
        }, (
            f"bounty {bounty_id} (position {expected}) should grant "
            f"{expected} token(s), got {rewards}"
        )

    # The "max per day" invariant: claim all three → 6 tokens total.
    total = sum(
        bounties.get_claim_rewards_for_bounty(
            _NoOpConn(), user_id, bounty_date, b['id'],
        )['tokens']
        for b in selected
    )
    assert total == 6, f"max per-day total should be 6 tokens, got {total}"


def test_claim_independence():
    """T117 AC#3: claiming one bounty must not lock the others.

    Each daily bounty has its own `claimed` flag (column on bounty_progress).
    A claim that fails for one row — e.g. it's already claimed — must not
    affect sibling rows.
    """
    bounties = _load_bounties_module()
    user_id = 7
    bounty_date = dt.date(2026, 6, 26)

    class _NoOpConn:
        def cursor(self, cursor_factory=None):
            raise AssertionError("get_claim_rewards_for_bounty must not touch the DB")

    selected = bounties.get_daily_bounties(user_id, bounty_date)

    # Each call returns a fresh reward dict for its own bounty_id. A second
    # call with the same bounty_id still returns the same reward (idempotent
    # compute) — the gate that prevents double-claims is the per-row
    # `claimed` flag checked by the claim handler, not this helper.
    r1 = bounties.get_claim_rewards_for_bounty(
        _NoOpConn(), user_id, bounty_date, selected[0]['id'],
    )
    r1_again = bounties.get_claim_rewards_for_bounty(
        _NoOpConn(), user_id, bounty_date, selected[0]['id'],
    )
    r2 = bounties.get_claim_rewards_for_bounty(
        _NoOpConn(), user_id, bounty_date, selected[1]['id'],
    )
    r3 = bounties.get_claim_rewards_for_bounty(
        _NoOpConn(), user_id, bounty_date, selected[2]['id'],
    )
    assert r1 == r1_again, "helper should be a pure function of (user, date, bounty_id)"
    assert r1['tokens'] == 1
    assert r2['tokens'] == 2
    assert r3['tokens'] == 3

    # The three ids must be distinct — otherwise the user's "1+2+3" claim
    # rotation collapses to a single reward.
    ids = {selected[0]['id'], selected[1]['id'], selected[2]['id']}
    assert len(ids) == 3, f"daily set must have 3 distinct ids, got {ids}"


def test_no_cosmetic_fragments_awarded():
    """T117 AC#3 (removed): no cosmetic-fragment bonus at 3/3 (or anywhere)."""
    bounties = _load_bounties_module()
    user_id = 1
    bounty_date = dt.date(2026, 6, 26)

    class _NoOpConn:
        def cursor(self, cursor_factory=None):
            raise AssertionError("get_claim_rewards_for_bounty must not touch the DB")

    selected = bounties.get_daily_bounties(user_id, bounty_date)
    for b in selected:
        rewards = bounties.get_claim_rewards_for_bounty(
            _NoOpConn(), user_id, bounty_date, b['id'],
        )
        assert rewards['cosmetic_fragments'] == 0, (
            f"T117 removed cosmetic fragments from bounty claims, got "
            f"{rewards['cosmetic_fragments']} for {b['id']}"
        )

    # Source-level guard: the helper must not reference `1` fragments or the
    # legacy 3-bounty curve.
    bounties_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'bounties.py',
    )
    src = open(bounties_path).read()
    assert 'get_claim_rewards_for_bounty' in src
    # The legacy (1, 2, 3) → (100/250/500, 0/0/1) table must be gone.
    assert '(500, 1)' not in src, "legacy 3-bounty 500-token/1-fragment curve must be removed"
    assert '(250, 0)' not in src, "legacy 3-bounty 250-token curve must be removed"
    assert 'def get_claim_rewards(' not in src, (
        "legacy get_claim_rewards (completion-count curve) must be removed in T117"
    )


def test_claim_button_sends_bounty_id():
    """T117 AC#1: POST with bounty_id → 200; without it → 400.

    Exercises the claim endpoint's input validation, which was the
    root cause of the operator-reported "bounty_id required" error:
    the JSX was posting `{}` because the API had been returning `id`
    instead of `bounty_id`.
    """
    # Missing body entirely.
    class _NoBodyRequest:
        method = 'POST'
        is_json = True
        json = None

    saved_request = _game.request
    saved_user = _game.current_user
    _game.request = _NoBodyRequest()
    _game.current_user = _FakeUser()
    try:
        result = _game.claim_bounty()
    finally:
        _game.request = saved_request
        _game.current_user = saved_user
    assert result[1] == 400, f"missing body should 400, got {result}"
    assert 'bounty_id required' in str(result[0].get('error', '')), (
        f"expected 'bounty_id required' error, got {result[0]}"
    )

    # Body present, but no bounty_id key.
    class _EmptyBodyRequest:
        method = 'POST'
        is_json = True
        json = {}

    _game.request = _EmptyBodyRequest()
    _game.current_user = _FakeUser()
    try:
        result = _game.claim_bounty()
    finally:
        _game.request = saved_request
        _game.current_user = saved_user
    assert result[1] == 400, f"empty body should 400, got {result}"
    assert 'bounty_id required' in str(result[0].get('error', ''))

    # Body with bounty_id → success path through the per-bounty flow.
    class _OKRequest:
        method = 'POST'
        is_json = True
        json = {'bounty_id': 'bounty_jackpot'}

    _game.request = _OKRequest()
    _game.current_user = _FakeUser()
    original_db = _game.db_connection
    _game.db_connection = _fake_db_connection_for_claim
    try:
        result = _game.claim_bounty()
    finally:
        _game.request = saved_request
        _game.current_user = saved_user
        _game.db_connection = original_db
    # Success branch returns just the dict (the stubbed `jsonify = lambda x: x`
    # collapses the (Response, status) tuple to the dict). The 400 branches
    # keep the explicit `, 400` so the result is a tuple there.
    if isinstance(result, tuple):
        body, status = result
    else:
        body, status = result, 200
    assert status == 200, f"valid claim should 200, got status={status} body={body}"
    assert body.get('ok') is True
    assert body['rewards']['cosmetic_fragments'] == 0
    assert body['rewards']['tokens'] == 2  # stubbed to position 2 above
