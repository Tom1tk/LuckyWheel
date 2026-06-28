"""T106 + T107: cumulative_wins tier gating + auto-spin-as-upgrade tests.

T106: change tier gating from `win_count` (count of winning spins) to
`cumulative_wins` (lifetime value of wins gained). The previous metric was
designed for an auto-spin era where every player spun 100+ times per session.
With wager-driven manual play, the count was too slow.

T107: auto-spin is now a shop upgrade. The stake slider is hidden in the UI
while auto-spin is active (auto-spin always uses 0% stake). The /api/auto-spin/start
endpoint requires the `auto_spin_unlock` item.
"""
import os
import sys
import re
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


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


# Stub game modules to avoid loading them in tests
sys.modules.setdefault('replays', _make_stub('replays', record_replay=lambda *a, **kw: None))
sys.modules.setdefault('seasons', _make_stub('seasons', **{'ensure_current_season': lambda *a, **kw: None,
                                                            'get_season_info': lambda *a, **kw: {},
                                                            'get_latest_winners': lambda *a, **kw: [],
                                                            'get_week_number': lambda *a, **kw: 1,
                                                            'get_active_goal': lambda *a, **kw: (None, None)}))
sys.modules.setdefault('community_goals', _make_stub('community_goals',
    **{'increment_goal': lambda *a, **kw: None,
       'check_goal_completion': lambda *a, **kw: None}))
sys.modules.setdefault('chat_triggers', _make_stub('chat_triggers',
    **{'jackpot_msg': lambda *a, **kw: 'JACKPOT',
       'big_win_msg': lambda *a, **kw: 'BIG WIN',
       'new_player_msg': lambda *a, **kw: 'NEW'}))
sys.modules.setdefault('chat', _make_stub('chat',
    **{'post_system_message': lambda *a, **kw: None,
       'record_replay': lambda *a, **kw: None}))


from models import (
    SHOP_ITEMS, UPGRADE_TIER_THRESHOLDS, item_tier,
)


def test_cumulative_wins_threshold_values():
    """T106: thresholds are 10K (tier 2) and 100K (tier 3)."""
    assert UPGRADE_TIER_THRESHOLDS[2] == 10_000, (
        f"tier 2 should be 10K lifetime wins gained, got {UPGRADE_TIER_THRESHOLDS[2]}"
    )
    assert UPGRADE_TIER_THRESHOLDS[3] == 100_000, (
        f"tier 3 should be 100K lifetime wins gained, got {UPGRADE_TIER_THRESHOLDS[3]}"
    )


def test_cumulative_wins_in_state_select():
    """T106: the _GAME_STATE_SQL includes cumulative_wins."""
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')) as f:
        src = f.read()
    assert 'cumulative_wins' in src, "game.py must reference cumulative_wins"


def test_cumulative_wins_in_manual_spin_update():
    """T106: the manual spin UPDATE includes cumulative_wins = %s."""
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')) as f:
        src = f.read()
    # Find all UPDATE ... SET statements and verify at least 2 reference cumulative_wins
    matches = re.findall(r'cumulative_wins\s*=\s*%s', src)
    assert len(matches) >= 2, (
        f"Expected cumulative_wins = %s in at least 2 UPDATE statements (manual + auto), found {len(matches)}"
    )


def test_cumulative_wins_in_state_response():
    """T106: /api/state response includes cumulative_wins field."""
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')) as f:
        src = f.read()
    assert "'cumulative_wins'" in src, "game.py must surface cumulative_wins in /api/state response"


def test_tier_gate_uses_cumulative_wins():
    """T106: the tier check uses cumulative_wins, not win_count."""
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')) as f:
        src = f.read()
    # Find the tier check block. Old: `if gs['win_count'] < threshold:`
    # New: must reference cumulative_wins in the same check.
    assert "gs.get('cumulative_wins'" in src, (
        "tier gate must check gs.get('cumulative_wins', 0)"
    )
    # Make sure the old win_count check is NOT in the buy endpoint
    buy_block = src.split("'Unlocks at")[0:1] + [src.split("'Unlocks at")[1][:500]]
    # The buy endpoint should not check win_count for tier gating
    assert 'win_count' not in buy_block[1] or 'cumulative_wins' in buy_block[1], (
        "tier gate should use cumulative_wins, not win_count"
    )


def test_t107_auto_spin_unlock_in_shop():
    """T107: auto_spin_unlock exists in SHOP_ITEMS at 5,000 wins, Tier 1."""
    assert 'auto_spin_unlock' in SHOP_ITEMS
    item = SHOP_ITEMS['auto_spin_unlock']
    assert item['cost'] == 5_000, f"cost should be 5,000, got {item['cost']}"
    assert item['requires'] is None, "auto_spin_unlock should be Tier 1 (no requires)"
    assert item_tier('auto_spin_unlock') == 1, "auto_spin_unlock should be Tier 1"


def test_t107_auto_spin_start_gated_on_unlock():
    """T107: /api/auto-spin/start returns 403 if auto_spin_unlock not owned."""
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')) as f:
        src = f.read()
    # Find the auto_spin_start function body
    start_match = re.search(
        r'def auto_spin_start\(\):.*?return jsonify\(\{[\'\"]ok[\'\"]\:.+?\}\)\s*\n',
        src, re.DOTALL,
    )
    assert start_match, "could not locate auto_spin_start function"
    body = start_match.group(0)
    assert 'auto_spin_unlock' in body, (
        "auto_spin_start must check for 'auto_spin_unlock' in owned_items"
    )
    assert '403' in body, "auto_spin_start must return 403 when not unlocked"


def test_t107_stake_slider_hidden_during_auto_spin():
    """T107: app.jsx hides the stake slider when autoSpinActive is true."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )) as f:
        src = f.read()
    # The conditional must use autoSpinActive
    assert '!autoSpinActive &&' in src or 'autoSpinActive ?' in src, (
        "app.jsx must conditionally render the stake slider based on autoSpinActive"
    )


def test_t107_auto_spin_checkbox_in_wager_panel():
    """T107: app.jsx renders an auto-spin checkbox toggle (`.autospin-row`
    style from S5/S6/S7) when auto_spin_unlock is owned. Checkbox toggles
    the server-side auto-spin via /api/auto-spin/start and /api/auto-spin/stop."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )) as f:
        src = f.read()
    assert "ownedItems.includes('auto_spin_unlock')" in src, (
        "auto-spin toggle must be gated on owning auto_spin_unlock"
    )
    # Checkbox markup (not a button — that's the old design the operator
    # wanted reverted to)
    assert 'className="autospin-row"' in src, (
        "must use .autospin-row class (checkbox style, not button)"
    )
    assert '<input' in src and 'type="checkbox"' in src, (
        "must render a checkbox input"
    )
    assert 'className="autospin-label"' in src, (
        "must use .autospin-label class for the label"
    )
    # Handlers still exist
    assert 'handleStartAutoSpin' in src, "must have handleStartAutoSpin handler"
    assert 'handleStopAutoSpin' in src, "must have handleStopAutoSpin handler"
    assert '/api/auto-spin/start' in src, "must POST to /api/auto-spin/start"
    assert '/api/auto-spin/stop' in src, "must POST to /api/auto-spin/stop"


def test_t107_tick_polls_during_auto_spin():
    """T107: app.jsx polls /api/tick while autoSpinActive is true."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )) as f:
        src = f.read()
    # Find a useEffect that depends on autoSpinActive and runs tick on an interval
    assert re.search(
        r'useEffect\(\(\)\s*=>\s*\{[^}]*autoSpinActive[^}]*setInterval',
        src, re.DOTALL,
    ), "must have useEffect that sets up an interval tied to autoSpinActive"


# ── T106 follow-up: live updates ───────────────────────────────────────────

def test_t106_cumulative_wins_echoed_in_spin_response():
    """The /api/spin response must include `cumulative_wins` so the shop
    tier-locked text updates live (without waiting for the next /api/state poll)."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'game.py',
    )) as f:
        src = f.read()
    # In the /api/spin endpoint (or its _events_to_response helper), the
    # response must include the new cumulative_wins value.
    spin_block = re.search(
        r"@game_bp\.route\('/api/spin'.*?return jsonify\(resp\)",
        src, re.DOTALL,
    )
    assert spin_block, "could not locate /api/spin endpoint"
    body = spin_block.group(0)
    assert "resp['cumulative_wins']" in body, (
        "/api/spin must echo resp['cumulative_wins'] = new_cumulative_wins"
    )


def test_t106_cumulative_wins_echoed_in_tick_response():
    """The /api/tick response must include `cumulative_wins` in both
    per-spin results (live auto-spin) and in `final_state` (catch-up summary)."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'game.py',
    )) as f:
        src = f.read()
    # Greedy match so we go to the LAST return jsonify (the final response),
    # not the early-return when budget == 0.
    tick_block = re.search(
        r"@game_bp\.route\('/api/tick'.*return jsonify\(\{",
        src, re.DOTALL,
    )
    assert tick_block, "could not locate /api/tick endpoint"
    body = tick_block.group(0)
    # Per-spin response (inside the loop)
    assert re.search(
        r"resp\['cumulative_wins'\]\s*=\s*new_cumulative_wins",
        body,
    ), "/api/tick per-spin response must include resp['cumulative_wins']"
    # Catch-up final_state (after the loop)
    assert "'cumulative_wins'" in body, (
        "/api/tick final_state must include 'cumulative_wins' for catch-up updates"
    )


def test_t106_frontend_uses_cumulative_wins_from_spin():
    """app.jsx must update cumulativeWins state from the spin response (not wait
    for /api/state). This is what makes the shop tier-locked text update live."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )) as f:
        src = f.read()
    # The apply-spin-result block (or whichever handler processes spin data)
    # must reference data.cumulative_wins AND setCumulativeWins
    assert "data.cumulative_wins" in src, (
        "app.jsx must read data.cumulative_wins from the spin response"
    )
    assert "setCumulativeWins" in src, (
        "app.jsx must call setCumulativeWins to update the state"
    )
    # Should NOT have a "refetch on next /api/state" comment (the old broken plan)
    assert "refetch on next /api/state" not in src, (
        "the old 'refetch on next /api/state' comment must be removed — the server "
        "now echoes cumulative_wins directly"
    )


def test_t216_auto_spin_start_uses_only_auto_spin_since():
    """T216 follow-up: the per-activation `auto_spin_budget` column was
    dropped. /api/auto-spin/start now uses `auto_spin_since` as the sole
    'is active' signal (a stale timestamp is treated as active — the
    heartbeat auto-stop in /api/tick will clear it after 60s of no
    ticks). The 'already active' check must NOT reference
    `auto_spin_budget` (the column no longer exists)."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'game.py',
    )) as f:
        src = f.read()
    # Locate the /api/auto-spin/start endpoint body
    start_block = re.search(
        r"@game_bp\.route\('/api/auto-spin/start'.*?return jsonify\(\{'ok': True",
        src, re.DOTALL,
    )
    assert start_block, "could not locate /api/auto-spin/start endpoint body"
    body = start_block.group(0)
    # The 'already active' check uses only auto_spin_since now.
    assert 'auto_spin_budget' not in body, (
        "/api/auto-spin/start still references auto_spin_budget but the "
        "column was dropped in migration 057 (T216)"
    )
    # The check still inspects auto_spin_since (sanity). The actual code
    # uses `gs.get('auto_spin_since')` (with the get() call), so look
    # for the close-paren + 'is not None' pattern.
    assert re.search(
        r"gs(?:\[[''\"]auto_spin_since['\"]\]|\.get\(['\"]auto_spin_since['\"]\))\s+is\s+not\s+None",
        body,
    ), (
        "/api/auto-spin/start must check auto_spin_since before reporting "
        "'already active' (T216)"
    )


def test_t107_autospin_css_mirrors_legacy_style():
    """T107 follow-up: the `.autospin-row` + `.autospin-label` CSS must
    exist (so the checkbox renders in the legacy S5/S6/S7 gold-glow style
    the operator wanted restored)."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'styles.css',
    )) as f:
        css = f.read()
    assert '.autospin-row' in css, "must define .autospin-row CSS"
    assert '.autospin-label' in css, "must define .autospin-label CSS"
    assert 'autospin-row input[type="checkbox"]' in css, (
        "must style the checkbox within .autospin-row"
    )
    assert 'autospin-row input[type="checkbox"]:checked' in css, (
        "must style the checked state of the checkbox"
    )
    # The legacy gold-glow look
    assert '#FFD700' in css, "must use the legacy gold accent color"


def test_t107_polling_useeffect_after_autospinactive_state():
    """T107 follow-up: the polling useEffect must be defined AFTER the
    `autoSpinActive` useState declaration, so the deps array
    `[autoSpinActive, tick]` reads a stable binding. If it's above
    the useState, babel hoists `var autoSpinActive` and the effect
    never re-fires when setAutoSpinActive(true) flips the value —
    the wheel never spins after ticking the checkbox."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )) as f:
        lines = f.readlines()
    # Find the line numbers. The polling useEffect is the one whose body
    # contains `setInterval(tick, 3000)` and whose deps are
    # `[autoSpinActive, tick]`.
    autospin_state_line = None
    polling_effect_line = None
    tick_callback_line = None
    polling_intervals = 0
    for i, line in enumerate(lines, start=1):
        if 'const [autoSpinActive, setAutoSpinActive]' in line:
            autospin_state_line = i
        if 'const tick = useCallback' in line:
            tick_callback_line = i
        if 'setInterval(tick, 3000)' in line:
            polling_intervals += 1
            polling_effect_line = i

    assert autospin_state_line, "could not locate autoSpinActive useState"
    assert tick_callback_line, "could not locate tick useCallback"
    assert polling_effect_line, "could not locate polling useEffect (setInterval(tick, 3000))"
    assert polling_intervals == 1, (
        f"expected exactly 1 polling useEffect (3s tick), found {polling_intervals}"
    )
    assert polling_effect_line > autospin_state_line, (
        f"polling useEffect (line {polling_effect_line}) must be defined AFTER "
        f"autoSpinActive state (line {autospin_state_line}) so the deps array "
        f"reads a stable binding"
    )
    # Also assert the tick callback is defined before the polling useEffect
    # (the polling effect closes over `tick` from the parent scope)
    assert tick_callback_line < polling_effect_line, (
        f"tick useCallback (line {tick_callback_line}) must be defined before "
        f"polling useEffect (line {polling_effect_line})"
    )
