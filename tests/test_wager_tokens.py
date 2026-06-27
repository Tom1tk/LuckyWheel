"""Tests for T110: spend wager tokens on high-stake spins (above 5x).

Acceptance criteria covered:
- Server validation: pay_with_tokens at low stake (< 30%) -> 400
- Server validation: pay_with_tokens with 0 tokens -> 400
- Server validation: pay_with_tokens with Double-Down armed -> 400
- Spin with pay_with_tokens: true at high stake with sufficient tokens ->
  tokens decremented, wins debited for any remainder
- Spin with pay_with_tokens: false at any stake -> tokens NOT touched
- Spin response includes wager_tokens + tokens_spent
- UI: the toggle only shows when stake_pct >= 30 and tokens > 0
- The token balance is shown in the wager panel

The tests are mostly source-string assertions (mirroring the project's
existing test style — see test_wager_stake_plumbing.py) because the
endpoints require a live DB and auth, and we already exercise the
core _resolve_spin token-spend math with monkeypatched random rolls.
"""
import os
import random
import sys
import types
import importlib.util

JSX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'static', 'app.jsx',
)
GAME_PY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'game.py',
)
WAGERS_PY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'wagers.py',
)


def _read(path):
    with open(path) as f:
        return f.read()


# ════════════════════════════════════════════════════════════════════════════
# wagers.py — HIGH_STAKE_TOKEN_THRESHOLD constant
# ════════════════════════════════════════════════════════════════════════════
def test_high_stake_token_threshold_constant():
    """T110: wagers.py exports HIGH_STAKE_TOKEN_THRESHOLD = 30."""
    src = _read(WAGERS_PY_PATH)
    assert 'HIGH_STAKE_TOKEN_THRESHOLD = 30' in src, (
        "wagers.py must export HIGH_STAKE_TOKEN_THRESHOLD = 30 (the high-stake "
        "threshold that gates the pay-with-tokens toggle)"
    )


# ════════════════════════════════════════════════════════════════════════════
# game.py — _resolve_spin token-spend math
# ════════════════════════════════════════════════════════════════════════════
def _load_wagers():
    spec = importlib.util.spec_from_file_location(
        'wagers', WAGERS_PY_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_game():
    _noop = lambda *a, **kw: (lambda f: f)
    _stub_flask = types.SimpleNamespace(
        Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
        jsonify=lambda x: x,
        request=None,
    )
    sys.modules.setdefault('flask', _stub_flask)
    sys.modules.setdefault('flask_login', types.SimpleNamespace(
        current_user=None,
        login_required=lambda f: f,
        UserMixin=type('UserMixin', (), {}),
    ))
    psycopg2_extras = types.SimpleNamespace(RealDictCursor=type('RealDictCursor', (), {}))
    sys.modules.setdefault('psycopg2', types.SimpleNamespace(extras=psycopg2_extras))
    sys.modules.setdefault('psycopg2.extras', psycopg2_extras)
    sys.modules.setdefault('extensions', types.SimpleNamespace(
        limiter=types.SimpleNamespace(limit=_noop),
        csrf=types.SimpleNamespace(exempt=_noop),
    ))
    sys.modules.setdefault('seasons', types.SimpleNamespace(
        ensure_current_season=lambda c: None,
        get_season_info=lambda c: {},
        advance_season=lambda c: None,
    ))
    sys.modules.setdefault('security', types.SimpleNamespace(require_json=lambda: None))
    sys.modules.setdefault('db', types.SimpleNamespace(db_connection=lambda: None))
    sys.modules.setdefault('wheel_modes', types.SimpleNamespace(
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
    sys.modules.setdefault('chat', types.SimpleNamespace(
        post_system_message=lambda *a, **kw: None,
        post_dedup_system_message=lambda *a, **kw: None,
    ))
    sys.modules.setdefault('chat_triggers', types.SimpleNamespace(
        jackpot_msg=lambda *a, **kw: '',
        double_down_win_msg=lambda *a, **kw: '',
        hot_streak_msg=lambda *a, **kw: '',
        DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE=5,
        HOT_STREAK_MSG_THRESHOLD=10,
        BIG_WIN_THRESHOLD=5000,
    ))
    sys.modules.setdefault('bounties', types.SimpleNamespace(
        increment_bounty=lambda *a, **kw: None,
        get_bounty_status=lambda *a, **kw: [],
        get_claim_rewards=lambda *a, **kw: {},
        get_claim_rewards_for_bounty=lambda *a, **kw: {},
        BOUNTY_DEFS={},
    ))
    sys.modules.setdefault('community_goals', types.SimpleNamespace(
        COMMUNITY_GOAL_DEFS={},
        get_active_goal=lambda *a, **kw: (None, None),
        increment_goal=lambda *a, **kw: None,
        check_goal_completion=lambda *a, **kw: None,
        get_player_contribution=lambda *a, **kw: 0,
    ))
    spec = importlib.util.spec_from_file_location('game', GAME_PY_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


game = _load_game()
_resolve_spin = game._resolve_spin


def _base_state(**overrides):
    state = dict(
        owned=['wager_unlock'],
        streak=0,
        best_streak=0,
        regen_recharge_wins=0,
        wins=1000,
        losses=0,
        jackpot_echo_next=False,
        spin_count=1,
        active_cosmetics=[],
        proc_streak=0,
    )
    state.update(overrides)
    return state


def _base_ctx(**overrides):
    ctx = dict(
        effective_win_mult=2.0,
        bonus_mult=1,
        jackpot_chance=0.0,
        echo_chance=0.0,
        charm_chance=0.0,
        resilience_chance=0.5,
        proc_streak_level=0,
        pot_active=False,
        pot_win_pct=0.505,
    )
    ctx.update(overrides)
    return ctx


def test_pay_with_tokens_full_coverage(monkeypatch):
    """T110: token balance exceeds stake cost (full coverage of the stake).

    Player has 1000 wins, 500 tokens, 30% stake (300 wins). Token spend
    is capped by the stake cost: min(500, 300) = 300. No wins debited
    because the tokens cover the entire stake.
    """
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # win
    state = _base_state(wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=30, active_wheel_mode='steady'),
        insurance_tokens=500, pay_with_tokens=True,
    )
    assert events['tokens_spent'] == 300, (
        f"full-coverage spend = min(500 tokens, 300 stake) = 300, "
        f"got {events['tokens_spent']}"
    )
    assert events['insurance_tokens'] == 200, (
        f"200 tokens should remain, got {events['insurance_tokens']}"
    )
    # wins = 1000 - 0 + 300 (refund) + 300 (payout) = 1600
    assert new_state['wins'] == 1600, (
        f"full-coverage win: 1000 + 300 + 300 = 1600, got {new_state['wins']}"
    )


def test_pay_with_tokens_partial_coverage(monkeypatch):
    """T110: pay_with_tokens partially covers the stake. Player has 1000
    wins, 50 tokens, 30% stake (300 wins). Token spend = 50 (capped by
    balance), wins debited = 250 (the remainder).
    """
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # win
    state = _base_state(wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=30, active_wheel_mode='steady'),
        insurance_tokens=50, pay_with_tokens=True,
    )
    assert events['tokens_spent'] == 50, (
        f"partial spend should be min(50 tokens, 300 stake) = 50, "
        f"got {events['tokens_spent']}"
    )
    assert events['insurance_tokens'] == 0, (
        f"token balance should be drained to 0, got {events['insurance_tokens']}"
    )
    # wins = 1000 - (300 - 50) + 300 (refund) + 300 (payout) = 1350
    assert new_state['wins'] == 1350, (
        f"partial-coverage win: 1000 - 250 + 300 + 300 = 1350, got {new_state['wins']}"
    )


def test_pay_with_tokens_drains_balance(monkeypatch):
    """T110: token balance exactly equals stake cost; all tokens spent."""
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # win
    state = _base_state(wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=30, active_wheel_mode='steady'),
        insurance_tokens=300, pay_with_tokens=True,
    )
    assert events['tokens_spent'] == 300
    assert events['insurance_tokens'] == 0
    # wins = 1000 + 0 + 300 (refund) + 300 (payout) = 1600
    assert new_state['wins'] == 1600


def test_pay_with_tokens_false_does_not_touch_balance(monkeypatch):
    """T110: pay_with_tokens: false leaves the token balance untouched."""
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # win
    state = _base_state(wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=30, active_wheel_mode='steady'),
        insurance_tokens=500, pay_with_tokens=False,
    )
    assert events['tokens_spent'] == 0, (
        f"no spend when pay_with_tokens: false, got {events['tokens_spent']}"
    )
    assert events['insurance_tokens'] == 500, (
        f"token balance unchanged, got {events['insurance_tokens']}"
    )


def test_pay_with_tokens_below_threshold_no_spend(monkeypatch):
    """T110: token-spend is gated on actual_stake >= HIGH_STAKE_TOKEN_THRESHOLD.
    Even with pay_with_tokens: true, a 10% stake does not consume tokens.
    (The /api/spin handler rejects this with 400, but _resolve_spin is
    defensive too — the function should never spend tokens at low stake.)
    """
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # win
    state = _base_state(wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=10, active_wheel_mode='steady'),
        insurance_tokens=1000, pay_with_tokens=True,
    )
    assert events['tokens_spent'] == 0, (
        f"low stake must not spend tokens, got {events['tokens_spent']}"
    )
    assert events['insurance_tokens'] == 1000, (
        f"token balance unchanged at low stake, got {events['insurance_tokens']}"
    )


def test_pay_with_tokens_dd_armed_no_spend(monkeypatch):
    """T110: Double-Down armed means tokens don't apply (DD uses
    wager_last_win_amount as the stake, not the percentage)."""
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # win
    state = _base_state(wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=30, active_wheel_mode='steady'),
        insurance_tokens=500, pay_with_tokens=True,
        double_down_active=True, wager_last_win_amount=100,
    )
    assert events['tokens_spent'] == 0, (
        f"DD armed must not spend tokens, got {events['tokens_spent']}"
    )
    assert events['insurance_tokens'] == 500, (
        f"token balance unchanged when DD armed, got {events['insurance_tokens']}"
    )


def test_pay_with_tokens_zero_balance(monkeypatch):
    """T110: zero token balance means zero spend (partial=0)."""
    monkeypatch.setattr(random, 'random', lambda: 0.5)  # win
    state = _base_state(wins=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=30, active_wheel_mode='steady'),
        insurance_tokens=0, pay_with_tokens=True,
    )
    assert events['tokens_spent'] == 0, (
        f"zero balance means zero spend, got {events['tokens_spent']}"
    )
    # wins = 1000 - 300 + 300 + 300 = 1300 (no token coverage)
    assert new_state['wins'] == 1300, (
        f"no-coverage win: 1000 - 300 + 300 + 300 = 1300, got {new_state['wins']}"
    )


def test_pay_with_tokens_inverted_mode(monkeypatch):
    """T110: token-spend also works in inverted mode (covers loss stake)."""
    monkeypatch.setattr(random, 'random', lambda: 0.95)  # 'lose' (good in inverted)
    state = _base_state(wins=1000, losses=1000)
    new_state, events = _resolve_spin(
        **state, **_base_ctx(stake_pct=30, active_wheel_mode='inverted'),
        insurance_tokens=200, pay_with_tokens=True,
    )
    # stake_losses = 30% of 1000 = 300. Token spend = min(200, 300) = 200.
    assert events['tokens_spent'] == 200, (
        f"inverted partial spend = 200, got {events['tokens_spent']}"
    )
    assert events['insurance_tokens'] == 0, (
        f"inverted: token balance drained, got {events['insurance_tokens']}"
    )


# ════════════════════════════════════════════════════════════════════════════
# game.py — /api/spin handler validation + response shape
# ════════════════════════════════════════════════════════════════════════════
def test_spin_handler_validates_pay_with_tokens_low_stake():
    """T110: /api/spin rejects pay_with_tokens: true with stake < 30."""
    src = _read(GAME_PY_PATH)
    assert "req_stake < HIGH_STAKE_TOKEN_THRESHOLD" in src, (
        "spin handler must reject pay_with_tokens when stake is below threshold"
    )
    assert "Pay-with-tokens requires stake" in src, (
        "spin handler must include a clear error message for low-stake rejection"
    )


def test_spin_handler_validates_pay_with_tokens_no_dd():
    """T110: /api/spin rejects pay_with_tokens when Double-Down is armed."""
    src = _read(GAME_PY_PATH)
    assert 'pay_with_tokens' in src and 'double_down_active' in src, (
        "spin handler must validate the DD-vs-tokens incompatibility"
    )
    assert 'Double-Down' in src, (
        "spin handler must include a clear error message for DD+token incompatibility"
    )


def test_spin_handler_validates_pay_with_tokens_no_balance():
    """T110/T119: /api/spin rejects pay_with_tokens when token balance is 0.
    T119 renamed the column/parameter wager_tokens → insurance_tokens."""
    src = _read(GAME_PY_PATH)
    assert 'No insurance tokens to spend' in src, (
        "spin handler must reject pay_with_tokens when balance is 0 (T119 renamed error)"
    )
    assert "gs.get('insurance_tokens', 0)) <= 0" in src, (
        "spin handler must check the current insurance_tokens balance (T119 renamed)"
    )


def test_spin_handler_passes_pay_with_tokens_to_resolve():
    """T110/T119: /api/spin forwards pay_with_tokens + insurance_tokens to
    _resolve_spin. T119 renamed the parameter."""
    src = _read(GAME_PY_PATH)
    assert 'pay_with_tokens=pay_with_tokens' in src, (
        "spin handler must forward the pay_with_tokens flag to _resolve_spin"
    )
    assert "insurance_tokens=int(gs.get('insurance_tokens', 0))" in src, (
        "spin handler must forward the current insurance_tokens balance to _resolve_spin "
        "(T119 renamed from wager_tokens)"
    )


def test_spin_handler_decrements_insurance_tokens_in_sql():
    """T110/T119: /api/spin UPDATE includes insurance_tokens so the new
    balance persists. T119 renamed the column."""
    src = _read(GAME_PY_PATH)
    assert 'insurance_tokens = %s' in src, (
        "spin handler SQL UPDATE must set insurance_tokens (T119 renamed)"
    )
    assert "int(events.get('insurance_tokens', 0))" in src, (
        "spin handler must source the new insurance_tokens from the events dict"
    )


def test_spin_response_includes_token_fields():
    """T110/T119: /api/spin response includes insurance_tokens + tokens_spent.
    T119 renamed the response key."""
    src = _read(GAME_PY_PATH)
    assert "resp['insurance_tokens']" in src, (
        "spin response must include the new insurance_tokens balance (T119 renamed)"
    )
    assert "resp['tokens_spent']" in src, (
        "spin response must include the tokens_spent amount"
    )


# ════════════════════════════════════════════════════════════════════════════
# app.jsx — wager panel toggle + balance display
# ════════════════════════════════════════════════════════════════════════════
def test_frontend_pay_with_tokens_toggle_gated_on_stake():
    """T110: the toggle is rendered only when stakePct >= 30, tokens > 0,
    and fish_to_wager is owned."""
    jsx = _read(JSX_PATH)
    assert 'wager-pay-tokens-toggle' in jsx, (
        "wager panel must have a 'wager-pay-tokens-toggle' element"
    )
    assert 'stakePct >= 30' in jsx, (
        "toggle must be gated on stakePct >= 30 (the high-stake threshold)"
    )
    assert 'fish_to_wager' in jsx, (
        "toggle must be gated on owning fish_to_wager"
    )
    assert '!doubleDownPending' in jsx, (
        "toggle must be hidden when Double-Down is armed"
    )


def test_frontend_wager_tokens_balance_in_panel():
    """T110: the token balance is shown in the wager panel itself."""
    jsx = _read(JSX_PATH)
    assert 'wager-tokens-balance' in jsx, (
        "wager panel must have a 'wager-tokens-balance' display"
    )


def test_frontend_pay_with_tokens_state_and_ref():
    """T110: payWithTokens state + payWithTokensRef mirror the value
    into the spin handler (same wager-stale pattern as stakeRef)."""
    jsx = _read(JSX_PATH)
    assert 'const [payWithTokens, setPayWithTokens]' in jsx, (
        "wager panel must hold payWithTokens in React state"
    )
    assert 'const payWithTokensRef' in jsx, (
        "wager panel must mirror payWithTokens into a ref for the spin handler"
    )
    assert 'payWithTokensRef.current = payWithTokens' in jsx, (
        "a useEffect must mirror payWithTokens into payWithTokensRef.current"
    )


def test_frontend_spin_sends_pay_with_tokens():
    """T110: the manual spin handler sends pay_with_tokens in the request body."""
    jsx = _read(JSX_PATH)
    assert 'pay_with_tokens: payWithTokensRef.current' in jsx, (
        "handleManualSpin must send 'pay_with_tokens: payWithTokensRef.current' "
        "in the request body"
    )


def test_frontend_spin_response_updates_wager_tokens():
    """T110/T119: the spin response handler updates insuranceTokens from
    data.insurance_tokens. T119 renamed the variable and response key."""
    jsx = _read(JSX_PATH)
    assert "data.insurance_tokens" in jsx and 'setInsuranceTokens(data.insurance_tokens)' in jsx, (
        "spin response handler must call setInsuranceTokens(data.insurance_tokens) "
        "so the UI updates without a /api/state poll (T119 renamed from setWagerTokens)"
    )


def test_frontend_toggle_resets_when_stake_drops_below_threshold():
    """T110: when the stake slider drops below 30, the toggle is auto-cleared
    so a stale value isn't sent to the server (which would 400)."""
    jsx = _read(JSX_PATH)
    assert "newStakePct < 30" in jsx and "setPayWithTokens(false)" in jsx, (
        "handleStakeChange must clear the toggle when stake drops below 30"
    )


# ════════════════════════════════════════════════════════════════════════════
# styles.css — toggle + balance styling
# ════════════════════════════════════════════════════════════════════════════
def test_stylesheet_has_pay_with_tokens_classes():
    """T110: styles.css has the new toggle + balance classes."""
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'styles.css',
    )
    css = _read(css_path)
    assert '.wager-pay-tokens-toggle' in css, (
        "styles.css must have .wager-pay-tokens-toggle rules"
    )
    assert '.wager-tokens-balance' in css, (
        "styles.css must have .wager-tokens-balance rules"
    )
