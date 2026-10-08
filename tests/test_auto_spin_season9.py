"""Season 9: auto-spin restoration tests.

T217: auto-spin is universal again (granted to every player) and the
S8 restrictions are relaxed for offline play:

  1. `auto_spin_unlock` is granted at registration (auth.py) and in the
     season reset (seasons.py), and backfilled for existing players by
     migration 076.
  2. `MAX_SPINS_PER_TICK` is back to ~1 week (201_600) so catch-up can
     cover a full offline window.
  3. The client resume-prevention behaviour from S8 is gone; page loads
     resume an active session so /api/tick catches up.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import models


def test_max_spins_per_tick_restored_to_a_week():
    assert models.MAX_SPINS_PER_TICK == 201_600, (
        "Season 9 restores the offline catch-up cap to ~1 week "
        "(7d * 86400s / 3s = 201_600). Was 100 in S8, 100800 in S7."
    )


def test_heartbeat_threshold_still_capped_by_24h_in_game():
    """The /api/tick stale auto-stop must be 24h (86_400s), wide enough
    for a full offline night yet short enough to abandon stale sessions."""
    root = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(root, 'game.py')) as f:
        src = f.read()
    assert re.search(r'>\s*86_?400\b', src), (
        "/api/tick stale-check must use a 86_400 (24h) threshold"
    )
    # The week-scale MAX_SPINS_PER_TICK must also be imported/used so the
    # tick loop actually honours it (not just defined in models.py).
    assert 'MAX_SPINS_PER_TICK' in src, (
        "game.py must reference MAX_SPINS_PER_TICK in the tick loop"
    )


def test_registration_grants_auto_spin_unlock():
    """New players in S9 start with auto_spin_unlock in owned_items."""
    root = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(root, 'auth.py')) as f:
        src = f.read()
    assert re.search(
        r"ARRAY\['page_season9',\s*'auto_spin_unlock'\]",
        src,
    ), "auth.py registration must grant ARRAY['page_season9', 'auto_spin_unlock']"


def test_season_reset_regrants_auto_spin_unlock():
    """The season rollover wipes owned_items — auto_spin_unlock must be
    re-granted there too so it survives future sub-season resets."""
    root = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(root, 'seasons.py')) as f:
        src = f.read()
    assert re.search(r"new_owned\s*=\s*\[new_theme,\s*['\"]auto_spin_unlock['\"]\]", src), (
        "seasons.py must define new_owned = [new_theme, 'auto_spin_unlock']"
    )
    assert "'auto_spin_unlock'" in src, (
        "seasons.py reset owned_items must include 'auto_spin_unlock'"
    )


def test_migration_076_grants_auto_spin_unlock():
    root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(root, 'migrations', '076_auto_spin_universal.sql')
    assert os.path.exists(path), f"missing migration: {path}"
    with open(path) as f:
        sql = f.read()
    assert re.search(
        r'auto_spin_unlock', sql,
    ), "migration 076 must reference auto_spin_unlock"
    assert re.search(
        r"array_append\(owned_items,\s*'auto_spin_unlock'\)", sql,
    ), "migration 076 must append auto_spin_unlock to owned_items"
    assert 'ANY(owned_items)' in sql, (
        "migration 076 must be idempotent (guard on ANY(owned_items))"
    )


def test_auto_spin_unlock_still_a_shop_item():
    """The shop item stays (players see it as owned) and the backend gate
    remains as a safety check — the S9 change is that every account holds
    the upgrade, not that the gate is removed."""
    assert 'auto_spin_unlock' in models.SHOP_ITEMS, (
        "auto_spin_unlock must stay in SHOP_ITEMS"
    )
    assert models.SHOP_ITEMS['auto_spin_unlock']['cost'] == 5_000


def test_app_jsx_keeps_stake_hiding_and_resume():
    """S9 legibility safeguards are retained: the stake slider is hidden
    while auto-spin is active, and the page resumes an active session on
    load (no S8 resume-prevention stop)."""
    root = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(root, 'static', 'app.jsx')) as f:
        src = f.read()
    assert '!autoSpinActive &&' in src, (
        "app.jsx must keep hiding the stake slider while auto-spin is active"
    )
    assert 'apiGame(\'/api/auto-spin/stop\' ' in src or "apiGame('/api/auto-spin/stop'" in src, (
        "app.jsx must still support the manual stop handler"
    )
    assert "Auto-spin was running on the server" not in src, (
        "S8 resume-prevention toast must be gone (S9 resumes sessions)"
    )
