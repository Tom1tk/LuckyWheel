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


def test_t107_auto_spin_button_in_wager_panel():
    """T107: app.jsx renders auto-spin start/stop button when auto_spin_unlock is owned."""
    with open(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'app.jsx',
    )) as f:
        src = f.read()
    assert "ownedItems.includes('auto_spin_unlock')" in src, (
        "auto-spin button must be gated on owning auto_spin_unlock"
    )
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
