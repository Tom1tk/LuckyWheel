"""Tests for T110 (option a): spend wager tokens to buy insurance charges.

Mechanic: 1 wager token = 1 insurance charge. The charge is added to the
player's existing ``wager_insurance_charges`` pool, capped at
``WAGER_INSURANCE_MAX_CHARGES``. If the cap would be hit, the unused
tokens are NOT spent (refunded). Atomicity: tokens are debited in the
same UPDATE that increments the charges — no partial state on failure.

Endpoint: ``POST /api/wager/insurance/buy`` with body ``{"token_cost": 1}``.

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
    request=None,  # set per-test on the game module
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
    """Run ``wager_insurance_buy`` with the given game state + request body.

    Returns ``(result, conn)`` so the test can inspect the returned JSON
    and the SQL the handler executed.
    """
    conn = _FakeConn(fetchone_queue=[gs])
    _game.db_connection = lambda: _fake_db_connection(conn)
    _game.request = types.SimpleNamespace(
        method='POST',
        get_json=lambda silent=False: body,
    )
    _game.current_user = types.SimpleNamespace(id=1)
    return _game.wager_insurance_buy(), conn


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
    """T110: 100 tokens, 0 charges, cost=1 → 99 tokens, 1 charge, granted=1."""
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'wager_tokens': 100,
        'wager_insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})

    assert isinstance(result, dict), f"expected dict response, got {result!r}"
    assert result['ok'] is True
    assert result['wager_tokens'] == 99
    assert result['wager_insurance_charges'] == 1
    assert result['granted'] == 1

    sql, params = _last_update_params(conn)
    assert sql is not None, "no UPDATE was executed"
    assert 'wager_tokens = %s' in sql
    assert 'wager_insurance_charges = %s' in sql
    assert params[:3] == (99, 1, params[2]), (
        f"UPDATE params should be (new_tokens=99, new_charges=1, last_recharge, user_id), "
        f"got {params}"
    )


# ════════════════════════════════════════════════════════════════════════════
# 2. Cap respected: max=3, current=2, cost=3 → 1 charge granted, 1 token spent
# ════════════════════════════════════════════════════════════════════════════
def test_buy_respects_cap_and_refunds_unused_tokens():
    """T110: max=3, current=2, cost=3 → 1 charge granted, 1 token spent
    (2 tokens refunded — the unused portion of the request)."""
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'wager_tokens': 10,
        'wager_insurance_charges': 2,
    }
    result, conn = _run_buy(gs, {'token_cost': 3})

    assert isinstance(result, dict), f"expected dict response, got {result!r}"
    assert result['ok'] is True
    assert result['granted'] == 1, (
        f"only 1 charge fits under the cap, granted should be 1, got {result['granted']}"
    )
    assert result['wager_insurance_charges'] == 3, (
        f"charges should reach the cap (3), got {result['wager_insurance_charges']}"
    )
    assert result['wager_tokens'] == 9, (
        f"only 1 token should be spent (10 - 1 = 9), got {result['wager_tokens']}"
    )

    # SQL: tokens debited by the GRANTED amount (1), not the requested cost (3).
    sql, params = _last_update_params(conn)
    assert params[0] == 9, f"tokens debited must be 1 (= 10 - granted), got {params[0]}"
    assert params[1] == 3, f"charges incremented to cap, got {params[1]}"


# ════════════════════════════════════════════════════════════════════════════
# 3. Missing fish_to_wager upgrade → 403
# ════════════════════════════════════════════════════════════════════════════
def test_buy_without_fish_to_wager_returns_403():
    """T110: player without fish_to_wager upgrade → 403, no state change."""
    gs = {
        'owned_items': ['wager_insurance'],  # no fish_to_wager
        'wager_tokens': 100,
        'wager_insurance_charges': 0,
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
    """T110: player without wager_insurance upgrade → 403."""
    gs = {
        'owned_items': ['fish_to_wager'],  # no wager_insurance
        'wager_tokens': 100,
        'wager_insurance_charges': 0,
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
    """T110: 0 tokens, cost=1 → 400."""
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'wager_tokens': 0,
        'wager_insurance_charges': 0,
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
# 6. Tokens not lost on failure (atomicity)
# ════════════════════════════════════════════════════════════════════════════
def test_buy_atomicity_no_token_loss_on_failure():
    """T110: when any precondition fails, the token balance is untouched.

    Three failure paths are covered: missing upgrade, no tokens, and
    invalid token_cost. None of them must execute an UPDATE.
    """
    # (a) missing fish_to_wager
    gs = {
        'owned_items': ['wager_insurance'],
        'wager_tokens': 50,
        'wager_insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})
    assert isinstance(result, tuple) and result[1] == 403
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)

    # (b) zero tokens
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'wager_tokens': 0,
        'wager_insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})
    assert isinstance(result, tuple) and result[1] == 400
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)

    # (c) invalid token_cost: non-int
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'wager_tokens': 50,
        'wager_insurance_charges': 0,
    }
    result, conn = _run_buy(gs, {'token_cost': 'banana'})
    assert isinstance(result, tuple) and result[1] == 400
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)

    # (d) invalid token_cost: zero / negative
    result, conn = _run_buy(gs, {'token_cost': 0})
    assert isinstance(result, tuple) and result[1] == 400
    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log)


# ════════════════════════════════════════════════════════════════════════════
# 7. At-cap no-op: max=3, current=3 → 409, no charge/token change
# ════════════════════════════════════════════════════════════════════════════
def test_buy_at_cap_returns_409_no_spend():
    """T110: charges already at cap → 409, no tokens spent (refund)."""
    gs = {
        'owned_items': ['fish_to_wager', 'wager_insurance'],
        'wager_tokens': 10,
        'wager_insurance_charges': 3,
    }
    result, conn = _run_buy(gs, {'token_cost': 1})

    assert isinstance(result, tuple), (
        f"expected (body, status) tuple for 409, got {result!r}"
    )
    body, status = result
    assert status == 409
    assert 'cap' in body['error'].lower() or 'insurance' in body['error'].lower()

    assert not any(s.lstrip().upper().startswith('UPDATE') for s, _ in conn.log), (
        "no UPDATE should run when already at cap"
    )


# ════════════════════════════════════════════════════════════════════════════
# 8. Structural: endpoint is wired in game.py and app.jsx
# ════════════════════════════════════════════════════════════════════════════
def test_buy_endpoint_registered_in_game_py():
    """T110: the buy route must be registered in game.py."""
    src = open(os.path.join(REPO, 'game.py')).read()
    assert "/api/wager/insurance/buy" in src, (
        "game.py must register POST /api/wager/insurance/buy"
    )
    assert "def wager_insurance_buy" in src, (
        "game.py must define a wager_insurance_buy view function"
    )
    # The decorators sit immediately before the function. Pull the 200-char
    # block preceding the def and assert csrf.exempt is in it.
    def_idx = src.find("def wager_insurance_buy")
    decorators = src[max(0, def_idx - 200):def_idx]
    assert "csrf.exempt" in decorators, (
        "wager_insurance_buy must be CSRF-exempt (@csrf.exempt decorator)"
    )
    assert "login_required" in decorators, (
        "wager_insurance_buy must require login (@login_required decorator)"
    )


def test_buy_handler_wired_in_jsx():
    """T110: a callback + button must exist in app.jsx for the buy flow."""
    src = open(os.path.join(REPO, 'static', 'app.jsx')).read()
    assert "handleBuyInsuranceWithTokens" in src, (
        "app.jsx must define a handleBuyInsuranceWithTokens callback"
    )
    assert "/api/wager/insurance/buy" in src, (
        "the callback must POST to /api/wager/insurance/buy"
    )
    assert "token_cost: 1" in src, (
        "the callback must send token_cost: 1 in the request body"
    )
    assert "wager-buy-insurance-btn" in src, (
        "the wager panel must have a 'wager-buy-insurance-btn' element"
    )
    assert "Buy Insurance" in src, (
        "the buy button must include the text 'Buy Insurance'"
    )
    assert "wagerTokens >= 1" in src, (
        "the buy button must be gated on wagerTokens >= 1"
    )
    assert "fish_to_wager" in src.split("wager-buy-insurance-btn", 1)[0], (
        "the buy button must be gated on fish_to_wager ownership"
    )


def test_buy_response_updates_wager_tokens_in_jsx():
    """T110: the buy callback updates both wagerTokens and
    wagerInsuranceCharges from the response (no /api/state poll)."""
    src = open(os.path.join(REPO, 'static', 'app.jsx')).read()
    # Locate the handleBuyInsuranceWithTokens block and check it sets both
    marker = "handleBuyInsuranceWithTokens"
    start = src.find(marker)
    assert start != -1
    block_end = src.find("\n  }, [showToast]);", start)
    block = src[start:block_end]
    assert "setWagerTokens(data.wager_tokens)" in block, (
        "buy callback must call setWagerTokens(data.wager_tokens)"
    )
    assert "setWagerInsuranceCharges(data.wager_insurance_charges)" in block, (
        "buy callback must call setWagerInsuranceCharges(data.wager_insurance_charges)"
    )


def test_buy_max_charges_exposed_in_state():
    """T110: the cap is exposed via /api/state (no hardcoded 3 in JSX)."""
    src = open(os.path.join(REPO, 'static', 'app.jsx')).read()
    assert "wager_insurance_max_charges" in src, (
        "frontend must read wager_insurance_max_charges from /api/state"
    )
    # The literal "< 3" cap check should not appear in the buy-button expression
    buy_marker = "wager-buy-insurance-btn"
    pos = src.find(buy_marker)
    assert pos != -1
    # Walk back to the start of the &&-chain (the first ownedItems.includes)
    # and forward to the closing paren of the JSX expression.
    chain_start = src.rfind("ownedItems.includes(", 0, pos)
    # Find the matching `&& (` for the outermost expression: walk from chain_start
    # to the closing `)}` that terminates the JSX block
    expr_end = src.find(")}", pos)
    cond = src[chain_start:expr_end]
    assert "< 3" not in cond, (
        "the buy-button visibility check must use the dynamic cap, not a hardcoded 3"
    )
    assert "wagerInsuranceMaxCharges" in cond, (
        "the buy-button visibility check must use wagerInsuranceMaxCharges"
    )


def test_buy_button_gated_on_conditions():
    """T110: button is gated on (a) wager_insurance owned (b) not armed
    (c) fish_to_wager owned (d) tokens >= 1 (e) below cap."""
    src = open(os.path.join(REPO, 'static', 'app.jsx')).read()
    pos = src.find("wager-buy-insurance-btn")
    assert pos != -1
    # The &&-condition lives inside a JSX expression: `{ ... && ( <button ... /> ) }`.
    # The opening `{` is the last `{` before the button position, and the
    # matching `)}` is the first one after the button. The condition
    # itself contains no `{` (only `(` `)` and `&&`), so this pair cleanly
    # bounds the gate expression.
    expr_start = src.rfind("{", 0, pos)
    expr_end = src.find(")}", pos)
    cond = src[expr_start:expr_end + 2]
    assert "'wager_insurance'" in cond, (
        f"buy button must be gated on wager_insurance ownership, condition was:\n{cond}"
    )
    assert "'fish_to_wager'" in cond, (
        f"buy button must be gated on fish_to_wager ownership, condition was:\n{cond}"
    )
    assert "wagerTokens >= 1" in cond, (
        f"buy button must require wagerTokens >= 1, condition was:\n{cond}"
    )
    assert "wagerInsuranceMaxCharges" in cond, (
        f"buy button must be gated on the cap, condition was:\n{cond}"
    )
    assert "!wagerInsuranceArmed" in cond, (
        f"buy button must be hidden when insurance is armed, condition was:\n{cond}"
    )
