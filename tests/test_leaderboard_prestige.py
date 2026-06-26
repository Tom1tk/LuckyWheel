"""T121: leaderboard uses prestige_level instead of win/bonus power columns.

T121 retired the Win Power (winmult_inf_level) and Bonus Power
(bonusmult_inf_level) infinite-upgrade columns. The leaderboard
endpoint should now expose each user's prestige_level (which is
the new permanent progression metric for Season 8).
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read_game_py():
    with open(os.path.join(REPO, 'game.py')) as f:
        return f.read()


def _leaderboard_select_block():
    """Return the text of the SELECT statement in /api/leaderboard
    (the lines between the `cur.execute(` and the trailing `'''`)."""
    src = _read_game_py()
    m = re.search(
        r"@game_bp\.route\('/api/leaderboard'.*?def leaderboard\(\):.*?cur\.execute\(\s*'''(.*?)'''",
        src, re.MULTILINE | re.DOTALL,
    )
    assert m, "could not locate /api/leaderboard SELECT in game.py"
    return m.group(1)


def test_leaderboard_selects_prestige_level():
    """The /api/leaderboard SELECT must include prestige_level (not
    winmult_inf_level / bonusmult_inf_level)."""
    block = _leaderboard_select_block()
    assert 'gs.prestige_level' in block or 'prestige_level' in block, (
        "/api/leaderboard SELECT must include prestige_level (T121 replaced WP/BP)"
    )
    assert 'winmult_inf_level' not in block, (
        "/api/leaderboard SELECT must not reference the retired winmult_inf_level"
    )
    assert 'bonusmult_inf_level' not in block, (
        "/api/leaderboard SELECT must not reference the retired bonusmult_inf_level"
    )


def test_leaderboard_response_has_prestige_level_key():
    """The leaderboard response dict must include prestige_level."""
    src = _read_game_py()
    # Look for the response dict construction in the leaderboard function.
    m = re.search(
        r"@game_bp\.route\('/api/leaderboard'.*?def leaderboard\(\):(.*?)(?=^@game_bp\.route|\Z)",
        src, re.MULTILINE | re.DOTALL,
    )
    assert m
    body = m.group(1)
    assert "'prestige_level'" in body or '"prestige_level"' in body, (
        "response dict must include 'prestige_level' key"
    )
    assert "'winmult_inf_level'" not in body and '"winmult_inf_level"' not in body, (
        "response dict must not include retired winmult_inf_level"
    )
    assert "'bonusmult_inf_level'" not in body and '"bonusmult_inf_level"' not in body, (
        "response dict must not include retired bonusmult_inf_level"
    )


def test_jsx_leaderboard_uses_prestige_column():
    """The JSX leaderboard row must render the Prestige column, not
    the old WP/BP cells."""
    jsx_path = os.path.join(REPO, 'static', 'app.jsx')
    with open(jsx_path) as f:
        jsx = f.read()
    # Find the leaderboard section (the players tab).
    # The lb-row JSX lives between "rows.map((r, i)" and the close.
    m = re.search(r"rows\.map\(\(r, i\) => \(\s*<div[^>]*className=\{?`lb-row",
                   jsx, re.DOTALL)
    assert m, "could not locate lb-row in app.jsx"
    start = m.start()
    # Grab the next ~600 chars after the lb-row opener.
    snippet = jsx[start:start + 800]
    assert 'lb-prestige' in snippet, (
        "lb-row must render lb-prestige (T121 replaced WP/BP)"
    )
    assert 'lb-wp' not in snippet and 'lb-bp' not in snippet, (
        "lb-row must not render the retired lb-wp/lb-bp cells"
    )
    # Header row also updated.
    assert 'lb-prestige-h' in jsx, "header row must include lb-prestige-h"
    assert 'lb-wp-h' not in jsx and 'lb-bp-h' not in jsx, (
        "header row must not include the retired lb-wp-h/lb-bp-h"
    )


def test_css_has_prestige_column_styling():
    """The CSS must style .lb-prestige (replaces .lb-wp / .lb-bp)."""
    css_path = os.path.join(REPO, 'static', 'styles.css')
    with open(css_path) as f:
        css = f.read()
    assert '.lb-prestige' in css, "styles.css must include .lb-prestige"
    assert '.lb-wp' not in css and '.lb-bp' not in css, (
        "styles.css must not include the retired .lb-wp / .lb-bp"
    )


def test_leaderboard_includes_prestiged_zero_win_users():
    """The WHERE clause must include users with 0 wins but
    prestige_level > 0 (otherwise T121-prestiged players
    would be invisible on the leaderboard).

    Similarly, the ORDER BY must rank by prestige_level first
    (then wins) so a Lv3 / 0-win user is ranked above a Lv0 / 1-win
    user."""
    block = _leaderboard_select_block()
    assert 'prestige_level > 0' in block, (
        "WHERE must include 'prestige_level > 0' so prestiged users "
        "with 0 wins appear on the leaderboard"
    )
    assert 'ORDER BY gs.prestige_level DESC' in block, (
        "ORDER BY must rank by prestige_level DESC (primary)"
    )
    assert 'wins > 0' in block, (
        "WHERE must still include wins > 0 (non-prestiged players)"
    )
