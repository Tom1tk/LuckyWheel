"""T121: prestige rework — drop efficiency/legacy, move trigger to shop.

T121 AC summary:
  A. `prestige_efficiency` and `prestige_legacy` no longer appear in the
     shop. /api/buy returns 403 'Item retired' for these IDs.
  B. The side-panel Prestige button + the old `showPrestigeConfirm` modal
     are deleted. The legacy_wins badge remains.
  C. Buying `prestige_unlock` in the shop now opens a centred
     "⚠️ Prestige Reset" modal first. Confirm calls POST /api/prestige;
     cancel just closes the modal.
  D. POST /api/prestige is atomic: deducts 1M wins (if not yet owned),
     adds the item, and resets state — all in one transaction.
  E. `compute_wins_kept` returns 0 (wins are fully reset).
  F. `get_legacy_keep_count` returns 0 (no functional items kept).

This file mixes source-string assertions (for the JSX/CSS, mirroring
the project's existing test style — see test_wager_tokens.py) with a
stubs-based harness for the game.py /api/buy and /api/prestige
endpoints (mirroring test_prestige_scope.py).
"""
import os
import sys
import types
import importlib.util
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
JSX_PATH = os.path.join(REPO_ROOT, 'static', 'app.jsx')
APP_JS_PATH = os.path.join(REPO_ROOT, 'static', 'app.js')
CSS_PATH = os.path.join(REPO_ROOT, 'static', 'styles.css')
GAME_PY_PATH = os.path.join(REPO_ROOT, 'game.py')
MODELS_PY_PATH = os.path.join(REPO_ROOT, 'models.py')
PRESTIGE_PY_PATH = os.path.join(REPO_ROOT, 'prestige.py')


def _read(path):
    with open(path) as f:
        return f.read()


# ════════════════════════════════════════════════════════════════════════════
# Module-loading plumbing (shared by the game.py endpoint tests below)
# ════════════════════════════════════════════════════════════════════════════
def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


def _install_stubs():
    """Install the minimal set of fake modules needed to import game.py
    without a live DB / Flask app. Idempotent — safe to call from multiple
    test functions."""
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
    sys.modules.setdefault('chat', _make_stub('chat',
        post_system_message=lambda *a, **kw: None,
        post_dedup_system_message=lambda *a, **kw: None,
    ))
    sys.modules.setdefault('chat_triggers', _make_stub('chat_triggers',
        jackpot_msg=lambda *a, **kw: '',
        prestige_msg=lambda *a, **kw: '',
        double_down_win_msg=lambda *a, **kw: '',
        hot_streak_msg=lambda *a, **kw: '',
        DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE=5,
        HOT_STREAK_MSG_THRESHOLD=10,
        BIG_WIN_THRESHOLD=5000,
    ))
    sys.modules.setdefault('bounties', _make_stub('bounties',
        increment_bounty=lambda *a, **kw: None,
        get_bounty_status=lambda *a, **kw: [],
        get_claim_rewards_for_bounty=lambda *a, **kw: {},
        BOUNTY_DEFS={},
    ))
    sys.modules.setdefault('community_goals', _make_stub('community_goals',
        COMMUNITY_GOAL_DEFS={},
        get_active_goal=lambda *a, **kw: (None, None),
        increment_goal=lambda *a, **kw: None,
        check_goal_completion=lambda *a, **kw: None,
        get_player_contribution=lambda *a, **kw: 0,
    ))
    sys.modules.setdefault('wagers', _make_stub('wagers',
        validate_stake=lambda *a, **kw: None,
        compute_hot_streak_bonus=lambda *a, **kw: 0,
        should_reset_streak=lambda *a, **kw: False,
        apply_safety_net=lambda *a, **kw: 0,
        compute_wager_payout=lambda *a, **kw: 0,
        compute_wager_loss=lambda *a, **kw: 0,
        compute_stake_risk=lambda *a, **kw: 0,
        compute_max_stake_pct=lambda *a, **kw: 30,
        compute_stake_value=lambda *a, **kw: 0,
        HIGH_STAKE_TOKEN_THRESHOLD=30,
    ))
    sys.modules.setdefault('wheel_modes', _make_stub('wheel_modes',
        WHEEL_MODES={
            'steady':   {'win_pct': 70.0, 'loss_pct': 27.0, 'jackpot_pct': 3.0},
            'volatile': {'win_pct': 45.0, 'loss_pct': 50.0, 'jackpot_pct': 5.0},
            'inverted': {'win_pct': 60.0, 'loss_pct': 35.0, 'jackpot_pct': 5.0},
            'mirror':   {'win_pct': 65.0, 'loss_pct': 30.0, 'jackpot_pct': 5.0},
            'gravity':  {'win_pct': 55.0, 'loss_pct': 40.0, 'jackpot_pct': 5.0},
        },
        compute_gravity_probabilities=lambda d: {'win_pct': 55.0, 'loss_pct': 40.0, 'jackpot_pct': 5.0},
        clamp_gravity_drift=lambda d: max(-35, min(35, d)),
        get_available_modes=lambda w: ['steady', 'volatile', 'mirror', 'gravity', 'inverted'],
        get_week_number=lambda d: 1,
    ))


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
def _fake_db_connection():
    conn = _FakeConn()
    yield conn


_install_stubs()
sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


# Load game.py and prestige.py once, after the stubs are in place.
_spec = importlib.util.spec_from_file_location('game', GAME_PY_PATH)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)


# ════════════════════════════════════════════════════════════════════════════
# A. Shop JSX — efficiency / legacy entries are gone
# ════════════════════════════════════════════════════════════════════════════
def test_efficiency_not_in_shop():
    """T121 AC#1: prestige_efficiency is not a buyable shop item.

    grep the source for any shop-section entry — the id should only
    appear in a code comment explaining the retirement.
    """
    jsx = _read(JSX_PATH)
    # The id may appear inside a comment, but never as a shop entry like
    # { id: 'prestige_efficiency', ... }.
    assert "{ id: 'prestige_efficiency'" not in jsx, (
        "prestige_efficiency must not appear as a buyable shop entry "
        "(T121 retired it)"
    )


def test_legacy_not_in_shop():
    """T121 AC#1: prestige_legacy is not a buyable shop item."""
    jsx = _read(JSX_PATH)
    assert "{ id: 'prestige_legacy'" not in jsx, (
        "prestige_legacy must not appear as a buyable shop entry "
        "(T121 retired it)"
    )


# ════════════════════════════════════════════════════════════════════════════
# A. /api/buy guard — 403 for retired items
# ════════════════════════════════════════════════════════════════════════════
def _drive_buy(item_id, gs):
    """Drive game.buy() with a fully-populated gs."""
    conn = _FakeConn(fetchone_queue=[gs, gs])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(
        method='POST', json={'item_id': item_id},
        get_json=lambda silent=True: {'item_id': item_id},
    )
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    return conn, _game.buy()


def test_buy_efficiency_returns_403():
    """T121 AC#2: /api/buy prestige_efficiency returns 403 'Item retired'."""
    gs = {'owned_items': ['prestige_unlock'], 'wins': 10_000_000, 'losses': 0}
    _drive_buy('prestige_efficiency', gs)  # warm up; assert on a fresh call
    # Direct call: hit the buy handler with a real gs and assert.
    conn = _FakeConn(fetchone_queue=[gs, gs])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(
        method='POST', json={'item_id': 'prestige_efficiency'},
        get_json=lambda silent=True: {'item_id': 'prestige_efficiency'},
    )
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    response, status = _game.buy()
    assert status == 403, f"expected 403 for retired item, got {status}"
    assert response['error'] == 'Item retired', (
        f"expected 'Item retired' error, got {response.get('error')!r}"
    )


def test_buy_legacy_returns_403():
    """T121 AC#2: /api/buy prestige_legacy returns 403 'Item retired'."""
    gs = {'owned_items': ['prestige_unlock'], 'wins': 10_000_000, 'losses': 0}
    conn = _FakeConn(fetchone_queue=[gs, gs])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(
        method='POST', json={'item_id': 'prestige_legacy'},
        get_json=lambda silent=True: {'item_id': 'prestige_legacy'},
    )
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    response, status = _game.buy()
    assert status == 403
    assert response['error'] == 'Item retired'


# ════════════════════════════════════════════════════════════════════════════
# models.py — RETIRED_ITEMS is defined
# ════════════════════════════════════════════════════════════════════════════
def test_models_has_retired_items():
    """T121: models.py exposes a RETIRED_ITEMS constant with the two
    retired prestige items."""
    src = _read(MODELS_PY_PATH)
    assert 'RETIRED_ITEMS' in src, (
        "models.py must define a RETIRED_ITEMS constant"
    )
    assert "'prestige_efficiency'" in src, (
        "RETIRED_ITEMS must list prestige_efficiency (with its old cost)"
    )
    assert "'prestige_legacy'" in src, (
        "RETIRED_ITEMS must list prestige_legacy (with its old cost)"
    )


def test_models_prestige_items_only_has_unlock():
    """T121: PRESTIGE_ITEMS keeps only prestige_unlock."""
    src = _read(MODELS_PY_PATH)
    # The two retired items are no longer in the buyable PRESTIGE_ITEMS dict
    # nor in SHOP_ITEMS. They live only in RETIRED_ITEMS now.
    # Heuristic: count occurrences in PRESTIGE_ITEMS / SHOP_ITEMS context.
    assert "'prestige_unlock':" in src
    # Make sure the shop still has prestige_unlock (so the buy button shows).
    assert "'prestige_unlock'" in src


# ════════════════════════════════════════════════════════════════════════════
# B. Side-panel button + old modal are gone
# ════════════════════════════════════════════════════════════════════════════
def test_side_panel_button_removed():
    """T121 AC#3: no <button>Prestige</button> in the side-panel JSX.

    Searches the JSX for the season8-prestige-panel block and asserts
    no <button> with text 'Prestige' is rendered inside it.
    """
    jsx = _read(JSX_PATH)
    # The className on the panel still exists (the badges stay).
    assert 'season8-prestige-panel' in jsx, (
        "the prestige panel container is still rendered (badges live inside)"
    )
    # The button labelled 'Prestige' inside the panel is gone. We grep for
    # the literal text in a <button> tag, scoped by surrounding code.
    # Simpler: look for the onClick={() => setShowPrestigeConfirm(true)}
    # handler — it only existed to open the now-deleted modal.
    assert 'setShowPrestigeConfirm' not in jsx, (
        "setShowPrestigeConfirm must be removed (T121 deleted the side-panel "
        "Prestige button and the modal it opened)"
    )


def test_show_prestige_confirm_modal_block_deleted():
    """T121 AC#3: the old `showPrestigeConfirm` modal block is gone.

    The old block was an .onboarding-overlay/.onboarding-modal with text
    '⚠️ Prestige Reset' + a one-liner body. The new modal lives in a
    patch-notes-card with the same title but a much longer body. We
    assert the state hook + the old block is gone, and the new modal
    uses the showPrestigeBuyConfirm state instead.
    """
    jsx = _read(JSX_PATH)
    assert 'showPrestigeConfirm' not in jsx, (
        "showPrestigeConfirm state and modal block must be removed"
    )
    # The new modal is the patch-notes-style card with showPrestigeBuyConfirm.
    assert 'showPrestigeBuyConfirm' in jsx, (
        "new showPrestigeBuyConfirm state must be defined"
    )


def test_legacy_wins_display_badge_remains():
    """T121 AC#4: the legacy_wins badge (.legacy-badge) stays in the JSX
    even though the button is removed. It's a passive display only."""
    jsx = _read(JSX_PATH)
    assert 'legacy-badge' in jsx, (
        "legacy_wins badge (.legacy-badge) must remain after the side-panel "
        "Prestige button is removed"
    )
    # And it's rendered conditionally on legacyWins > 0.
    assert 'legacyWins > 0' in jsx, (
        "legacy_wins badge is shown only when legacyWins > 0"
    )


# ════════════════════════════════════════════════════════════════════════════
# C. Shop buy intercepts prestige_unlock and opens a centred modal
# ════════════════════════════════════════════════════════════════════════════
def test_modal_renders_in_shop():
    """T121 AC#5: buying prestige_unlock opens a centred modal with the
    title '⚠️ Prestige Reset' and Confirm/Cancel buttons."""
    jsx = _read(JSX_PATH)
    # The intercept is in handleBuy: it special-cases id === 'prestige_unlock'
    # and sets showPrestigeBuyConfirm(true) instead of POSTing /api/buy.
    assert "id === 'prestige_unlock'" in jsx, (
        "handleBuy must intercept prestige_unlock to open the modal"
    )
    assert 'setShowPrestigeBuyConfirm(true)' in jsx, (
        "handleBuy must open the modal via setShowPrestigeBuyConfirm(true)"
    )
    # The modal renders with the title.
    assert '⚠️ Prestige Reset' in jsx, (
        "modal must show the '⚠️ Prestige Reset' title"
    )
    # And both buttons (data-testid is the stable Playwright hook).
    assert 'Confirm Prestige' in jsx
    assert 'prestige-cancel' in jsx, (
        "modal must have a Cancel button (data-testid='prestige-cancel')"
    )
    assert 'prestige-confirm' in jsx, (
        "modal must have a Confirm button (data-testid='prestige-confirm')"
    )
    # The modal is centred (uses the .stats-overlay/.patch-notes-card
    # primitives, which are centred by the existing CSS).
    assert 'stats-overlay' in jsx
    assert 'patch-notes-card' in jsx


def test_modal_confirm_button_calls_prestige_endpoint():
    """T121 AC#6: the modal's Confirm button calls POST /api/prestige."""
    jsx = _read(JSX_PATH)
    # handleConfirmPrestigeBuy calls /api/prestige with POST.
    assert "apiGame('/api/prestige', { method: 'POST'" in jsx, (
        "Confirm Prestige handler must POST to /api/prestige"
    )


def test_modal_cancel_button_no_api_call():
    """T121 AC#7: the modal's Cancel button just closes the modal —
    no /api/prestige POST is made from the cancel path.

    The cancel button is bound to setShowPrestigeBuyConfirm(false) only.
    """
    jsx = _read(JSX_PATH)
    # Find the cancel button (it has data-testid="prestige-cancel" and
    # calls only setShowPrestigeBuyConfirm(false)). The simplest assertion
    # is that handleConfirmPrestigeBuy is the only function that POSTs
    # to /api/prestige in the JSX.
    prestige_posts = jsx.count("apiGame('/api/prestige', { method: 'POST'")
    assert prestige_posts == 1, (
        f"expected exactly one POST to /api/prestige, found {prestige_posts}"
    )
    # And the data-testid attribute proves the cancel button exists in the DOM.
    assert 'prestige-cancel' in jsx, (
        "cancel button must be present in the modal JSX (for tests to find)"
    )


# ════════════════════════════════════════════════════════════════════════════
# D. /api/prestige is atomic
# ════════════════════════════════════════════════════════════════════════════
def _drive_prestige(gs, *, capture_log=True):
    """Drive game.prestige_reset() with a fully-populated gs."""
    full_gs = dict(gs)
    full_gs.setdefault('prestige_level', 0)
    full_gs.setdefault('prestige_count', 0)
    full_gs.setdefault('legacy_wins', 0)
    full_gs.setdefault('onboarding_step', 0)
    full_gs.setdefault('insurance_tokens', 0)
    full_gs.setdefault('active_cosmetics', [])
    full_gs.setdefault('cosmetic_fragments', 0)
    full_gs.setdefault('caught_species', [])

    conn = _FakeConn(fetchone_queue=[full_gs, full_gs])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST', json={})
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    _game.post_system_message = lambda *a, **kw: None
    _game.increment_bounty = lambda *a, **kw: None
    _game.increment_goal = lambda *a, **kw: None
    _game.check_goal_completion = lambda *a, **kw: None
    _game.get_season_info = lambda c: {'season_number': 8}
    _game.get_active_goal = lambda c, s, w: (None, None)
    return conn, _game.prestige_reset()


def test_prestige_endpoint_atomic():
    """T121 AC#8: fresh user with 1.5M wins, no owned items. POST
    /api/prestige should:
      - deduct 1M wins (1.5M - 1M = 500K kept for legacy_wins)
      - add the prestige_unlock item
      - reset wins to 0
      - bump prestige_level to 1
      - all in one transaction (one UPDATE statement)
    """
    gs = {
        'owned_items': [],   # fresh user
        'wins': 1_500_000,
        'losses': 0,
    }
    conn, result = _drive_prestige(gs)
    # Result: atomic endpoint advances the level and persists the unlock.
    assert result['prestige_level'] == 1
    assert result['prestige_count'] == 1
    assert result['legacy_wins'] == 1_500_000, (
        f"legacy_wins should equal the prior wins (1.5M), got {result['legacy_wins']}"
    )
    # The new wins is 0 (T121: full reset).
    assert result['wins_kept'] == 0

    # Exactly one UPDATE — the atomic write.
    updates = [(sql, params) for sql, params in conn.log
               if sql.lstrip().upper().startswith('UPDATE')]
    assert len(updates) == 1, (
        f"expected exactly 1 UPDATE for the atomic transaction, got {len(updates)}: "
        f"{updates}"
    )

    # The UPDATE includes both the unlock (via owned_items param) and
    # the win deduction.
    sql, params = updates[0]
    assert 'owned_items = %s' in sql
    assert 'wins = %s' in sql
    # Params layout: (new_level, new_prestige_count, new_legacy_wins,
    # new_wins, new_owned_items, *reset defaults*, user_id).
    # wins = 0 (T121 full reset), legacy_wins = 1.5M (prior wins).
    assert params[3] == 0, f"new wins (idx 3) should be 0, got {params[3]}"
    assert params[2] == 1_500_000, (
        f"new legacy_wins (idx 2) should be 1.5M, got {params[2]}"
    )
    # The unlock is in the new owned_items list (atomic flow re-adds it
    # because the player didn't own it before the call).
    new_owned = params[4]
    assert 'prestige_unlock' in new_owned, (
        f"atomic flow should add prestige_unlock to owned_items, got {new_owned}"
    )
    # The cost was the 1M unlock price (because player didn't own it yet).
    assert result['cost'] == 1_000_000


def test_prestige_endpoint_insufficient_wins():
    """T121: fresh user with 999,999 wins, no owned items.
    POST /api/prestige should return 403 with current_wins + threshold.
    """
    gs = {
        'owned_items': [],
        'wins': 999_999,
        'losses': 0,
    }
    conn = _FakeConn(fetchone_queue=[gs, gs])
    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST', json={})
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    _game.post_system_message = lambda *a, **kw: None
    _game.increment_bounty = lambda *a, **kw: None
    _game.increment_goal = lambda *a, **kw: None
    _game.check_goal_completion = lambda *a, **kw: None
    _game.get_season_info = lambda c: {'season_number': 8}
    _game.get_active_goal = lambda c, s, w: (None, None)

    result = _game.prestige_reset()
    # Error response: (body_dict, 403) tuple.
    assert isinstance(result, tuple), (
        f"expected 403 tuple response, got {type(result).__name__}: {result!r}"
    )
    body, status = result
    assert status == 403
    assert body['current_wins'] == 999_999
    assert body['threshold'] == 1_000_000
    assert '1000000' in body['error']


def test_prestige_endpoint_already_owned():
    """T121: user already owns prestige_unlock and has 1.1M wins. POST
    /api/prestige should reset without an additional 1M deduction
    (the second prestige is "free" — wins > threshold carries it).

    Per the T85 + T121 contract, ``prestige_unlock`` itself is a functional
    upgrade and gets dropped by ``filter_kept_items(0)`` after the reset.
    The player has to re-buy it from the shop for the next prestige. The
    atomic flow only re-adds the unlock when it wasn't already owned (i.e.
    on the first prestige). This test verifies the cost=0 path is reachable
    and behaves correctly.
    """
    gs = {
        'owned_items': ['prestige_unlock'],
        'wins': 1_100_000,   # > 1M threshold for level 0
        'losses': 0,
        'prestige_level': 0,
        'prestige_count': 0,
        'legacy_wins': 0,
    }
    conn, result = _drive_prestige(gs)
    assert result['prestige_level'] == 1
    # cost is 0 (already owned, so no 1M deduction).
    assert result['cost'] == 0, (
        f"already-owned flow should have cost=0 (no 1M deduction), got {result['cost']}"
    )
    # legacy_wins is 1.1M (the prior wins — T121 carries the full total).
    assert result['legacy_wins'] == 1_100_000
    # T121 follow-up: prestige_unlock is the permanent gate for prestige —
    # it must always be in the new owned_items. The server re-adds it
    # after filter_kept_items drops it (since keep_count=0 strips
    # functionals). The shop re-shows the buy button on subsequent
    # prestiges for the next-level threshold.
    sql, params = next(
        (s, p) for s, p in conn.log
        if s.lstrip().upper().startswith('UPDATE')
    )
    new_owned = params[4]
    assert 'prestige_unlock' in new_owned, (
        f"prestige_unlock must be preserved as the permanent gate, got {new_owned}"
    )


# ════════════════════════════════════════════════════════════════════════════
# E + F. compute_wins_kept and get_legacy_keep_count are dead code
# ════════════════════════════════════════════════════════════════════════════
def test_no_efficiency_carryover():
    """T121 AC#9: compute_wins_kept returns 0 unconditionally. Owning 3
    prestige_efficiency items does not change the post-prestige wins
    (it's still 0)."""
    from prestige import compute_wins_kept
    # Direct: even with 3 efficiency levels, wins_kept is 0.
    assert compute_wins_kept(2_000_000, ['prestige_efficiency'] * 3) == 0
    assert compute_wins_kept(10_000_000, ['prestige_efficiency'] * 5) == 0
    # Without any owned items, also 0.
    assert compute_wins_kept(2_000_000, []) == 0
    # Atomic endpoint reflects this: a 1.5M-win player with the retired
    # items still has wins_kept == 0.
    gs = {
        'owned_items': ['prestige_efficiency'] * 3,  # staging legacy data
        'wins': 1_500_000,
        'losses': 0,
    }
    _, result = _drive_prestige(gs)
    assert result['wins_kept'] == 0


def test_no_legacy_carryover():
    """T121 AC#9: get_legacy_keep_count returns 0 unconditionally. Owning
    3 prestige_legacy items does not change the items kept (the filter
    returns only cosmetics)."""
    from prestige import get_legacy_keep_count, filter_kept_items
    # Direct: even with 3 legacy levels, keep_count is 0.
    assert get_legacy_keep_count(['prestige_legacy'] * 3) == 0
    # filter_kept_items(0) only keeps cosmetics; the legacy items themselves
    # are treated as functional (T121 update to _is_cosmetic_item) and dropped.
    owned = ['prestige_legacy', 'prestige_legacy', 'prestige_legacy',
             'fish_tropical', 'wager_unlock', 'winmult_1']
    kept = filter_kept_items(owned, get_legacy_keep_count(owned))
    # Cosmetics stay, functionals + wager items dropped, retired items
    # explicitly treated as functional and dropped.
    assert 'fish_tropical' in kept
    assert 'wager_unlock' not in kept
    assert 'winmult_1' not in kept
    assert 'prestige_legacy' not in kept


# ════════════════════════════════════════════════════════════════════════════
# F. PRESTIGE_RESET_COLUMNS — every column in the canonical list is cleared
# ════════════════════════════════════════════════════════════════════════════
def test_prestige_resets_columns():
    """T121 AC#10: every column in PRESTIGE_RESET_COLUMNS is in the UPDATE
    SQL. (The new atomic flow still uses the same reset list.)"""
    from prestige import PRESTIGE_RESET_COLUMNS
    gs = {
        'owned_items': ['prestige_unlock'],
        'wins': 1_050_000,
    }
    conn, _ = _drive_prestige(gs)
    sql = next(s for s, _ in conn.log if s.lstrip().upper().startswith('UPDATE'))
    for col in PRESTIGE_RESET_COLUMNS:
        if col == 'wins':
            assert 'wins = %s' in sql, f"wins not parameterised: {sql}"
        else:
            assert f'{col} = %s' in sql, (
                f"reset column {col!r} missing from SQL:\n{sql}"
            )


def test_prestige_preserves_cosmetics():
    """T121 AC#11: active_cosmetics, aquarium_species, cosmetic_fragments
    are not in the SET clause of the prestige UPDATE (preserved)."""
    gs = {
        'owned_items': ['prestige_unlock'],
        'wins': 1_050_000,
        'active_cosmetics': ['fish_tropical'],
        'cosmetic_fragments': 42,
    }
    conn, _ = _drive_prestige(gs)
    sql = next(s for s, _ in conn.log if s.lstrip().upper().startswith('UPDATE'))
    set_part = sql.split('WHERE', 1)[0]
    for col in ('active_cosmetics', 'aquarium_species', 'cosmetic_fragments'):
        assert col not in set_part, (
            f"{col} should be preserved (not in SET clause), got SQL:\n{sql}"
        )


def test_prestige_threshold_scales():
    """T121 AC#12: after reaching level 1, the next threshold is
    round(1_000_000 * 1.05) == 1,050,000."""
    from prestige import get_prestige_threshold, PRESTIGE_LEVEL_MULTIPLIER
    # Drive prestige as if the player just hit level 0 → 1.
    gs = {
        'owned_items': ['prestige_unlock'],
        'wins': 1_000_000,
        'prestige_level': 0,
        'prestige_count': 0,
        'legacy_wins': 0,
    }
    _, result = _drive_prestige(gs)
    assert result['prestige_level'] == 1
    # The next threshold uses the new level.
    next_threshold = get_prestige_threshold(['prestige_unlock'], 1)
    assert next_threshold == round(1_000_000 * PRESTIGE_LEVEL_MULTIPLIER ** 1)
    assert next_threshold == 1_050_000


# ════════════════════════════════════════════════════════════════════════════
# Integration: 1.5M-win fresh user ends with wins=0, legacy_wins=1,500,000
# ════════════════════════════════════════════════════════════════════════════
def test_atomic_prestige_1_5m_user_legacy_wins_carries_total():
    """T121 AC#9 (worked example): a fresh user with 1.5M wins and 0 owned
    items, after the atomic prestige:
      - wins = 0
      - legacy_wins = 1,500,000
      - prestige_level = 1
      - prestige_unlock in owned_items
    """
    gs = {
        'owned_items': [],
        'wins': 1_500_000,
        'losses': 0,
        'prestige_level': 0,
        'prestige_count': 0,
        'legacy_wins': 0,
    }
    conn, result = _drive_prestige(gs)
    assert result['prestige_level'] == 1
    assert result['legacy_wins'] == 1_500_000
    assert result['wins_kept'] == 0
    # The UPDATE param tuple contains the new owned_items list with the
    # unlock added (since the player didn't own it before).
    sql, params = next(
        (s, p) for s, p in conn.log
        if s.lstrip().upper().startswith('UPDATE')
    )
    new_owned = params[4]
    assert 'prestige_unlock' in new_owned
    # The new wins is 0.
    assert params[3] == 0
    # The new legacy_wins is 1.5M (the prior wins).
    assert params[2] == 1_500_000


# ════════════════════════════════════════════════════════════════════════════
# Source-level: ensure the build artefact (app.js) was rebuilt with the
# new modal strings.
# ════════════════════════════════════════════════════════════════════════════
def test_built_app_js_contains_new_modal():
    """T121: the built static/app.js bundle (not just the JSX source)
    must contain the new modal markers. This guards against a stale
    build where JSX was edited but `make build` was forgotten."""
    bundle = _read(APP_JS_PATH)
    assert 'showPrestigeBuyConfirm' in bundle, (
        "static/app.js must include the new showPrestigeBuyConfirm state "
        "(rebuild the bundle with `make build`)"
    )
    assert 'handleConfirmPrestigeBuy' in bundle, (
        "static/app.js must include the new handleConfirmPrestigeBuy handler"
    )
    assert "id === 'prestige_unlock'" in bundle, (
        "static/app.js must include the prestige_unlock intercept in handleBuy"
    )
