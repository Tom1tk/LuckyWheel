"""T224: Auto-fish state must be reset on prestige, not left stuck on.

Bug report (operator, 2026-06-27): a player had auto-fishing on when
they prestiged. After prestige:
  - the autofisher_* upgrade is removed from owned_items (T121 clears
    every functional upgrade on prestige)
  - but auto_fish_enabled was still TRUE in the DB
  - the JSX only renders the auto-fish toggle when hasAutoFisher is
    true, so the player had no way to turn it off
  - the JSX hides the manual cast button when autoFish is true, so
    they also couldn't fish manually

Fix:
  1. auto_fish_enabled + auto_fish_last_tick are in PRESTIGE_RESET_COLUMNS
  2. _prestige_default returns False / None for the two new columns
  3. /api/state response includes auto_fish_enabled so the client can
     stay in sync
  4. /api/prestige POST response includes the new (cleared) value
  5. /api/auto-fish-enabled defensively forces the flag off if the
     player doesn't own an autofisher upgrade
  6. The JSX FishingPanel forces local autoFish=false when the upgrade
     is missing (defence in depth, even if the server-side fixes fail)
  7. Migration 066 backfills any existing stuck players

These tests pin all of the above so the bug doesn't regress.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

ROOT    = os.path.dirname(os.path.dirname(__file__))
APP_JSX = os.path.join(ROOT, 'static', 'app.jsx')
GAME_PY = os.path.join(ROOT, 'game.py')
PRESTIGE_PY = os.path.join(ROOT, 'prestige.py')
MIG_066 = os.path.join(ROOT, 'migrations', '066_clear_stuck_auto_fish.sql')


def _read(path):
    with open(path) as f:
        return f.read()


# ── PRESTIGE_RESET_COLUMNS includes the new columns ───────────────────────

def test_prestige_reset_columns_includes_auto_fish_enabled():
    """T224: auto_fish_enabled must be in PRESTIGE_RESET_COLUMNS so it
    gets reset on every prestige."""
    from prestige import PRESTIGE_RESET_COLUMNS
    assert 'auto_fish_enabled' in PRESTIGE_RESET_COLUMNS, (
        "auto_fish_enabled must be in PRESTIGE_RESET_COLUMNS (T224)"
    )


def test_prestige_reset_columns_includes_auto_fish_last_tick():
    """T224: auto_fish_last_tick must be in PRESTIGE_RESET_COLUMNS so
    the stale timestamp doesn't drive an immediate catch-up fish on the
    player's first spin post-prestige."""
    from prestige import PRESTIGE_RESET_COLUMNS
    assert 'auto_fish_last_tick' in PRESTIGE_RESET_COLUMNS, (
        "auto_fish_last_tick must be in PRESTIGE_RESET_COLUMNS (T224)"
    )


# ── _prestige_default returns the right values ────────────────────────────

def test_prestige_default_auto_fish_enabled_false():
    """T224: _prestige_default('auto_fish_enabled') must return False
    so the column is cleared on prestige."""
    src = _read(GAME_PY)
    # The function groups columns that reset to False in a tuple
    # followed by a `return False`. The auto_fish_enabled literal must
    # appear in that tuple, with the matching `return False` within
    # the same group. Search with [\\s\\S] to span newlines.
    assert re.search(
        r"if\s+col\s+in\s+\([\s\S]*?'auto_fish_enabled'[\s\S]*?\)\s*:\s*\n\s*return\s+False",
        src,
    ), (
        "_prestige_default must return False for auto_fish_enabled "
        "(T224: clear on prestige)"
    )


def test_prestige_default_auto_fish_last_tick_none():
    """T224: _prestige_default('auto_fish_last_tick') must return None
    so the timestamp is cleared on prestige."""
    src = _read(GAME_PY)
    # The function groups columns that reset to None in a tuple
    # followed by a `return None`. Same multi-line pattern.
    assert re.search(
        r"if\s+col\s+in\s+\([\s\S]*?'auto_fish_last_tick'[\s\S]*?\)\s*:\s*\n\s*return\s+None",
        src,
    ), (
        "_prestige_default must return None for auto_fish_last_tick "
        "(T224: clear on prestige)"
    )


# ── /api/state response includes auto_fish_enabled ────────────────────────

def test_state_response_includes_auto_fish_enabled():
    """T224: /api/state must include auto_fish_enabled so the client
    can keep its local state in sync with the server."""
    src = _read(GAME_PY)
    # The /api/state SELECT must include auto_fish_enabled
    assert "'auto_fish_enabled'" in src or '"auto_fish_enabled"' in src, (
        "game.py must reference auto_fish_enabled (T224: surface in /api/state)"
    )
    # The response dict must include it
    assert re.search(
        r"['\"]auto_fish_enabled['\"]\s*:\s*bool\(gs\.get",
        src,
    ), (
        "the /api/state response must include "
        "'auto_fish_enabled': bool(gs.get('auto_fish_enabled', False))"
    )


# ── /api/prestige POST response includes the cleared value ────────────────

def test_prestige_post_response_includes_auto_fish_enabled():
    """T224: the prestige POST response must include the new
    auto_fish_enabled value (always False after prestige) so the client
    can clear its local state immediately, without waiting for the
    next /api/state poll."""
    src = _read(GAME_PY)
    # The prestige POST response includes the state object; within
    # that object, auto_fish_enabled should be set from the freshly
    # loaded game state (fresh.get('auto_fish_enabled')).
    assert re.search(
        r"auto_fish_enabled['\"]\s*:\s*bool\(fresh\.get\(['\"]auto_fish_enabled['\"]",
        src,
    ), (
        "the prestige POST response must include the post-prestige "
        "auto_fish_enabled value from the freshly loaded game state"
    )


# ── set_auto_fish_enabled is defensive ─────────────────────────────────────

def test_set_auto_fish_enabled_forces_off_when_no_upgrade():
    """T224: /api/auto-fish-enabled must force the flag off if the
    player doesn't own an autofisher upgrade. This is the server-side
    unstick mechanism (the client also handles it, but defence in depth).

    T240: the autofisher gate now lives in ``fish.py`` (the route
    handler in ``game.py`` is a thin wrapper that delegates to
    ``fish.set_auto_fish_enabled``).  This test now pins both pieces:
    the route must delegate, and the delegated function must do the
    autofisher gate.
    """
    src = _read(GAME_PY)
    # The handler must still exist in game.py and delegate to fish.
    assert re.search(
        r"def set_auto_fish_enabled",
        src,
    ), "set_auto_fish_enabled handler must exist in game.py"
    handler_block = re.search(
        r"def set_auto_fish_enabled.*?(?=^def [a-zA-Z_]|\Z)",
        src,
        re.DOTALL | re.MULTILINE,
    )
    assert handler_block, "could not locate set_auto_fish_enabled function in game.py"
    body = handler_block.group(0)
    # The route must call into fish.set_auto_fish_enabled (the actual
    # autofisher gate lives there now).
    assert 'set_auto_fish_enabled' in body, (
        "set_auto_fish_enabled route must call into fish.set_auto_fish_enabled"
    )
    # And the gate must live in fish.py — the autofisher level check
    # + 'autofisher_lvl >= 1' gate.
    fish_src = _read(os.path.join(ROOT, 'fish.py'))
    fish_func = re.search(
        r"def set_auto_fish_enabled.*?(?=^def [a-zA-Z_]|\Z)",
        fish_src,
        re.DOTALL | re.MULTILINE,
    )
    assert fish_func, "fish.set_auto_fish_enabled must exist (T240)"
    fish_body = fish_func.group(0)
    assert 'autofisher_lvl' in fish_body and '>= 1' in fish_body, (
        "fish.set_auto_fish_enabled must gate the enabled flag on "
        "autofisher_lvl >= 1 (T224 server-side unstick)"
    )


# ── Migration 066 backfills stuck players ─────────────────────────────────

def test_migration_066_exists():
    """T224: migration 066 must exist to backfill existing stuck players."""
    assert os.path.exists(MIG_066), (
        "migrations/066_clear_stuck_auto_fish.sql must exist (T224)"
    )


def test_migration_066_clears_stuck_state():
    """T224: migration 066 must update game_state to clear auto_fish for
    any user who doesn't own an autofisher_* upgrade. Idempotent (re-run
    is a no-op)."""
    src = _read(MIG_066)
    assert 'UPDATE game_state' in src, "migration must UPDATE game_state"
    assert 'auto_fish_enabled' in src, "migration must touch auto_fish_enabled"
    assert 'auto_fish_last_tick' in src, "migration must touch auto_fish_last_tick"
    # The WHERE clause must filter to autofisher-less users so we
    # don't accidentally turn off auto-fish for players who DO own
    # the upgrade. owned_items is text[] (not jsonb), so the
    # containment operator is `= ANY(owned_items)`, not `?`.
    assert 'autofisher_1' in src or 'autofisher_2' in src or 'autofisher_3' in src or 'autofisher_4' in src, (
        "migration must filter on autofisher_* ownership"
    )
    assert '= ANY (owned_items)' in src or 'ANY(owned_items)' in src, (
        "migration must use the text[] = ANY() operator (not the "
        "jsonb ? operator, which doesn't exist for text[])"
    )
    assert 'FALSE' in src, "migration must set auto_fish_enabled = FALSE"
    assert 'NULL' in src, "migration must set auto_fish_last_tick = NULL"


# ── JSX: defensive force-off when upgrade is missing ─────────────────────

def test_jsx_force_autofish_off_when_no_upgrade():
    """T224: the JSX FishingPanel must force autoFish=false in local
    state when the autofisher_1 upgrade is missing. This is the
    defence-in-depth path that keeps the manual-fish UI visible even
    if the server-side fixes fail."""
    src = _read(APP_JSX)
    # The useEffect that watches [autoFish, hasAutoFisher] and forces
    # autoFish off when hasAutoFisher is false.
    assert re.search(
        r"if\s*\(\s*autoFish\s*&&\s*!hasAutoFisher\s*\)\s*\{?\s*setAutoFish\s*\(\s*false\s*\)",
        src,
    ), (
        "JSX must force autoFish=false when hasAutoFisher is false "
        "(T224: defence in depth)"
    )


def test_jsx_initialize_autofish_from_server():
    """T224: the JSX FishingPanel must initialise autoFish from the
    server's auto_fish_enabled flag (passed via props) so the local
    state matches the server on page load."""
    src = _read(APP_JSX)
    # The useState initialiser for autoFish must reference
    # !!autoFishEnabled (or autoFishEnabled) — not just `false`.
    assert re.search(
        r"useState\s*\(\s*!!?autoFishEnabled\s*\)",
        src,
    ), (
        "JSX must initialise autoFish from the server-supplied "
        "autoFishEnabled prop (T224: server sync)"
    )


def test_jsx_state_poll_syncs_autofish_enabled():
    """T224: the /api/state sync useEffect must mirror auto_fish_enabled
    into the local state hook so periodic state polls keep the UI in
    sync (e.g. when the user opens a second tab and the server flag
    changes server-side)."""
    src = _read(APP_JSX)
    assert re.search(
        r"gameState\.auto_fish_enabled\s*!=\s*null\s*\)\s*setAutoFishEnabled",
        src,
    ), (
        "the /api/state sync useEffect must call setAutoFishEnabled "
        "when gameState.auto_fish_enabled is non-null (T224)"
    )


def test_jsx_prestige_response_syncs_autofish_enabled():
    """T224: the prestige POST response handler must call
    setAutoFishEnabled(s.auto_fish_enabled) so the UI clears the
    auto-fish state immediately after a successful prestige, without
    waiting for a /api/state poll."""
    src = _read(APP_JSX)
    assert re.search(
        r"s\.auto_fish_enabled\s*!=\s*null\s*\)\s*setAutoFishEnabled",
        src,
    ), (
        "the prestige response handler must sync auto_fish_enabled "
        "into local state (T224)"
    )
