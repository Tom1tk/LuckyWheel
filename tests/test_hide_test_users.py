"""T241: hide test users from the public leaderboard.

Background: the pytest suite runs against the production `wheeldb` (no
separate test DB is wired up; T234 + audit §3 explicitly defer that).
Tests register users from `127.0.0.1` and assign wins, prestige, etc.
Those users pollute the live `/api/leaderboard` for every real player.

Fix: every public query that surfaces multiple users filters
`u.ip_address <> '127.0.0.1'`. The 8 real players (tom7, dylan, …)
connect from `192.168.68.10` and are unaffected.

These assertions re-grep the SQL source; live-server verification is
manual (restart gunicorn, GET /api/leaderboard, confirm no `^t\\d+`
username appears).
"""
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read_game_py():
    with open(os.path.join(REPO, 'game.py')) as f:
        return f.read()


def _read_seasons_py():
    with open(os.path.join(REPO, 'seasons.py')) as f:
        return f.read()


def _leaderboard_select_block():
    src = _read_game_py()
    m = re.search(
        r"@game_bp\.route\('/api/leaderboard'.*?def leaderboard\(\):.*?cur\.execute\(\s*'''(.*?)'''",
        src, re.MULTILINE | re.DOTALL,
    )
    assert m, "could not locate /api/leaderboard SELECT in game.py"
    return m.group(1)


def _season_top3_select_block():
    src = _read_seasons_py()
    m = re.search(
        r"# Snapshot top 3.*?cur\.execute\(\s*'''(.*?)'''",
        src, re.MULTILINE | re.DOTALL,
    )
    assert m, "could not locate season top-3 SELECT in seasons.py"
    return m.group(1)


def test_leaderboard_excludes_localhost_users():
    """The /api/leaderboard SELECT must filter u.ip_address <> '127.0.0.1'."""
    block = _leaderboard_select_block()
    assert "u.ip_address <> '127.0.0.1'" in block, (
        "/api/leaderboard WHERE must include "
        "u.ip_address <> '127.0.0.1' (T241 hides test users from "
        "the public leaderboard — pytest writes to the prod DB)"
    )


def test_leaderboard_preserves_prior_filter():
    """T121's wins/prestige predicate must still be present
    (the test-user filter is additive, not a replacement)."""
    block = _leaderboard_select_block()
    assert 'wins > 0' in block, "T121 wins > 0 filter regressed"
    assert 'prestige_level > 0' in block, "T121 prestige_level > 0 filter regressed"
    assert 'ORDER BY gs.prestige_level DESC' in block, "T121 ORDER BY regressed"


def test_season_top3_excludes_localhost_users():
    """The season-rollover top-3 SELECT must also filter test users,
    so future season_snapshots (the 'winners' tab) never freeze a
    pytest fixture as a permanent record."""
    block = _season_top3_select_block()
    assert "u.ip_address <> '127.0.0.1'" in block, (
        "seasons.py top-3 SELECT must include "
        "u.ip_address <> '127.0.0.1' (T241 prevents test users from "
        "entering season_snapshots)"
    )
