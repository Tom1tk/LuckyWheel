"""Tests for T119: insurance buy endpoint (`/api/insurance/buy`).

T119 renamed and reworked the endpoint:
- URL: `/api/wager/insurance/buy` → `/api/insurance/buy`
- Handler: `wager_insurance_buy` → `insurance_buy_with_tokens`
- Columns: `wager_tokens` → `insurance_tokens`,
  `wager_insurance_charges` → `insurance_charges`
- Cap: REMOVED. Players can stockpile as many charges as they've
  bought with tokens. The old `WAGER_INSURANCE_MAX_CHARGES` cap
  and its refund-unused-tokens behaviour are gone.
- Rate: 1 token = 1 charge (unchanged from T110).

Tests follow the existing in-process test pattern from
``test_wager_actions.py``: stub modules, fake DB connection with a
controllable ``fetchone`` queue, then invoke the endpoint function
directly and assert on the returned JSON + recorded SQL.
"""
import os
import sys
import types
import importlib.util
from contextlib import contextmanager


REPO = os.path.dirname(os.path.dirname(__file__))


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
        self._cursor = _FakeCursor(self.log, self._fetchone_queue)

    def cursor(self, cursor_factory=None):
        return self._cursor

    def commit(self):
        pass


@contextmanager
def _fake_db_connection(conn):
    yield conn


sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(REPO, 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)


def _run_buy(gs, body):
    """Run ``insurance_buy_with_tokens`` (T119) with the given game
    state + request body. Returns ``(result, conn)`` so the test can
    inspect the returned JSON and the SQL the handler executed.
    """
    conn = _FakeConn(fetchone_queue=[gs])
    _game.db_connection = lambda: _fake_db_connection(conn)
    _game.request = types.SimpleNamespace(
        method='POST',
        get_json=lambda silent=False: body,
    )
    _game.current_user = types.SimpleNamespace(id=1)
    return _game.insurance_buy_with_tokens(), conn


def _last_update_params(conn):
    """Return the params tuple of the last UPDATE statement."""
    for sql, params in reversed(conn.log):
        if sql.lstrip().upper().startswith('UPDATE'):
            return sql, params
    return None, None


# ════════════════════════════════════════════════════════════════════════════
# 1. Success: 100 tokens, 0 charges → spend 1 token → 99 tokens, 1 charge
# ════════════════════════════════════════════════════════════════════════════
def test_buy_one_charge_success():
    """T119: 100 tokens, 0 charges, cost=1 → 99 tokens, 1 charge."""
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'insurance_tokens': 100,
        'insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})

    assert isinstance(result, dict), f"expected dict response, got {result!r}"
    assert result['ok'] is True
    assert result['insurance_tokens'] == 99
    assert result['insurance_charges'] == 1
    assert result['granted'] == 1

    sql, params = _last_update_params(conn)
    assert sql is not None, "no UPDATE was executed"
    assert 'insurance_tokens = %s' in sql
    assert 'insurance_charges = %s' in sql
    assert params[:2] == (99, 1), (
        f"UPDATE params should be (new_tokens=99, new_charges=1, user_id), "
        f"got {params}"
    )


# ════════════════════════════════════════════════════════════════════════════
# 2. No cap: 100 tokens, 0 charges → spend 100 tokens → 0 tokens, 100 charges
# ════════════════════════════════════════════════════════════════════════════
def test_buy_no_cap():
    """T119: the WAGER_INSURANCE_MAX_CHARGES cap is removed. Buying 10
    charges in a row succeeds (no cap, no refund)."""
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'insurance_tokens': 100,
        'insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 100})

    assert isinstance(result, dict), f"expected dict response, got {result!r}"
    assert result['ok'] is True
    assert result['granted'] == 100, (
        f"all 100 tokens should be granted as charges, got {result['granted']}"
    )
    assert result['insurance_charges'] == 100, (
        f"charges should reach 100 (no cap), got {result['insurance_charges']}"
    )
    assert result['insurance_tokens'] == 0, (
        f"tokens should be drained to 0, got {result['insurance_tokens']}"
    )


# ════════════════════════════════════════════════════════════════════════════
# 3. Missing fish_to_wager upgrade → 403
# ════════════════════════════════════════════════════════════════════════════
def test_buy_without_fish_to_wager_returns_403():
    """T119: player without fish_to_wager upgrade → 403, no state change."""
    gs = {
        'owned_items': ['wager_insurance'],  # no fish_to_wager
        'insurance_tokens': 100,
        'insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})

    assert isinstance(result, tuple), (
        f"expected (body, status) tuple for 403, got {result!r}"
    )
    body, status = result
    assert status == 403
    assert 'fish_to_wager' in body['error'].lower()

    # No UPDATE must have been executed (atomicity)
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log), (
        "no UPDATE should run on a failed validation"
    )


# ════════════════════════════════════════════════════════════════════════════
# 4. Missing wager_insurance upgrade → 403
# ════════════════════════════════════════════════════════════════════════════
def test_buy_without_wager_insurance_returns_403():
    """T119: player without wager_insurance upgrade → 403."""
    gs = {
        'owned_items': ['fish_to_wager'],  # no wager_insurance
        'insurance_tokens': 100,
        'insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})

    assert isinstance(result, tuple), (
        f"expected (body, status) tuple for 403, got {result!r}"
    )
    body, status = result
    assert status == 403
    assert 'insurance' in body['error'].lower()

    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log), (
        "no UPDATE should run on a failed validation"
    )


# ════════════════════════════════════════════════════════════════════════════
# 5. No tokens → 400
# ════════════════════════════════════════════════════════════════════════════
def test_buy_with_no_tokens_returns_400():
    """T119: 0 tokens, cost=1 → 400."""
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'insurance_tokens': 0,
        'insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})

    assert isinstance(result, tuple), (
        f"expected (body, status) tuple for 400, got {result!r}"
    )
    body, status = result
    assert status == 400
    assert 'token' in body['error'].lower()

    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log), (
        "no UPDATE should run when the balance check fails"
    )


# ════════════════════════════════════════════════════════════════════════════
# 6. Atomicity: tokens are not lost on any failure
# ════════════════════════════════════════════════════════════════════════════
def test_buy_atomicity_no_token_loss_on_failure():
    """T119: when any precondition fails, the token balance is untouched.
    No UPDATE may execute for any failure path.
    """
    # (a) missing fish_to_wager
    gs = {
        'owned_items': ['wager_insurance'],
        'insurance_tokens': 50,
        'insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})
    assert isinstance(result, tuple) and result[1] == 403
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)

    # (b) zero tokens
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'insurance_tokens': 0,
        'insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})
    assert isinstance(result, tuple) and result[1] == 400
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)

    # (c) invalid token_cost: non-int
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'insurance_tokens': 50,
        'insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 'banana'})
    assert isinstance(result, tuple) and result[1] == 400
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)

    # (d) invalid token_cost: zero / negative
    result, conn = _run_buy(gs, {'token_cost': 0})
    assert isinstance(result, tuple) and result[1] == 400
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)


# ════════════════════════════════════════════════════════════════════════════
# 7. Endpoint registration: /api/insurance/buy (renamed from /api/wager/insurance/buy)
# ════════════════════════════════════════════════════════════════════════════
def test_buy_endpoint_registered_in_game_py():
    """T119: the buy route must be registered at /api/insurance/buy."""
    src = open(os.path.join(REPO, 'game.py')).read()
    assert "/api/insurance/buy" in src, (
        "game.py must register POST /api/insurance/buy (T119 renamed from /api/wager/insurance/buy)"
    )
    assert "def insurance_buy_with_tokens" in src, (
        "game.py must define an insurance_buy_with_tokens view function (T119 renamed)"
    )
    # The decorators sit immediately before the function.
    def_idx = src.find("def insurance_buy_with_tokens")
    decorators = src[max(0, def_idx - 200):def_idx]
    assert "csrf.exempt" in decorators, (
        "insurance_buy_with_tokens must be CSRF-exempt (@csrf.exempt decorator)"
    )
    assert "login_required" in decorators, (
        "insurance_buy_with_tokens must require login (@login_required decorator)"
    )


def test_buy_handler_wired_in_jsx():
    """T119: a callback + button must exist in app.jsx for the buy flow.
    The new buy URL is /api/insurance/buy; the button label uses
    insuranceTokens (was wagerTokens)."""
    src = open(os.path.join(REPO, 'static', 'app.jsx')).read()
    # Endpoint URL is the new /api/insurance/buy.
    assert "/api/insurance/buy" in src, (
        "the buy callback must POST to /api/insurance/buy (T119 renamed)"
    )
    # The column is now insurance_tokens; the JSX variable is
    # insuranceTokens (T119 renamed from wagerTokens).
    assert "setInsuranceTokens(data.insurance_tokens)" in src, (
        "buy callback must call setInsuranceTokens(data.insurance_tokens) "
        "(T119 renamed from setWagerTokens(data.wager_tokens))"
    )
    assert "setInsuranceCharges(data.insurance_charges)" in src, (
        "buy callback must call setInsuranceCharges(data.insurance_charges) "
        "(T119 renamed from setWagerInsuranceCharges(data.wager_insurance_charges))"
    )
    assert "wager-buy-insurance-btn" in src, (
        "the wager panel must still have a 'wager-buy-insurance-btn' element"
    )
    # T119: button label is "Buy 1 charge (1 token)" (T110's
    # "Buy Insurance" label was a bit ambiguous — T119 clarifies it
    # converts 1 token to 1 charge).
    assert "Buy 1 charge" in src, (
        "the buy button must include the new 'Buy 1 charge' text (T119)"
    )
    # The condition no longer references a cap (the cap is removed).
    # The button is gated on insuranceTokens >= 1, ownership, and not armed.
    assert "insuranceTokens >= 1" in src, (
        "the buy button must be gated on insuranceTokens >= 1 "
        "(T119 renamed from wagerTokens >= 1)"
    )
    assert "fish_to_wager" in src.split("wager-buy-insurance-btn", 1)[0], (
        "the buy button must still be gated on fish_to_wager ownership"
    )
    # T119: the "Buy Insurance" button is hidden when insurance is armed.
    # The condition includes `!insuranceArmed` (was `!wagerInsuranceArmed`).
    # Walk from the button to find the surrounding JSX gate expression.
    pos = src.find("wager-buy-insurance-btn")
    assert pos != -1
    expr_start = src.rfind("{", 0, pos)
    expr_end = src.find(")}", pos)
    cond = src[expr_start:expr_end + 2]
    assert "!insuranceArmed" in cond, (
        f"buy button must be hidden when insurance is armed, condition was:\n{cond}"
    )
    # T119: the cap is removed. The old "wagerInsuranceMaxCharges" reference
    # is gone, and no "wager_insurance_max_charges" key is read.
    assert "wagerInsuranceMaxCharges" not in cond, (
        f"buy button must not reference the removed cap constant, condition was:\n{cond}"
    )
    # The /api/state no longer exposes wager_insurance_max_charges; the
    # JSX must not read it.
    full_jsx = src
    assert "wager_insurance_max_charges" not in full_jsx, (
        "JSX must not read the removed wager_insurance_max_charges key from /api/state"
    )
