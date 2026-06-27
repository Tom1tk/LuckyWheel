"""T215: Guard Charge passive regen + shop description fix.

Background (from docs/SEASON_8_TICKETS.md, T215):

    The shop entry claimed "Recharges 1 per 50 spins via Regen Shield." but
    no such regen existed. The Regen Shield (`regen_shield`) is a separate
    item that blocks losses. T215 implements the per-spin passive regen
    (1 charge every 50 spins, capped at 3) and updates the misleading
    shop description.

Operator's choice: Option A (per-spin, 50 spins) — pure passive mechanic,
no migration needed, no new column, no time-based regen.

This test file mixes source-string assertions (for the JSX shop entry)
with a pure-Python unit test of the regen condition itself. The regen
condition is evaluated inline in the /api/spin handler against the
post-increment spin_count; we test the equivalent expression here.

The pre-existing bug "buying guard_charge does not grant a charge" is
NOT fixed by T215 (the operator's clarification scoped T215 to the regen
side only). The buy-grant is tracked as a separate follow-up; the
test_first_charge_purchase_grants_1 test is therefore marked xfail until
that work lands.
"""
import os
import re
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSX_PATH  = os.path.join(REPO_ROOT, 'static', 'app.jsx')
APP_JS_PATH = os.path.join(REPO_ROOT, 'static', 'app.js')
GAME_PY_PATH = os.path.join(REPO_ROOT, 'game.py')
MODELS_PY_PATH = os.path.join(REPO_ROOT, 'models.py')


def _read(path):
    with open(path) as f:
        return f.read()


# ════════════════════════════════════════════════════════════════════════════
# A. Shop description: must not falsely claim Regen Shield drives regen
# ════════════════════════════════════════════════════════════════════════════
def _guard_charge_shop_desc():
    """Pull the `desc` field of the guard_charge shop entry from app.jsx."""
    src = _read(JSX_PATH)
    m = re.search(r"id:\s*'guard_charge'.*?desc:\s*'([^']+)'", src)
    if not m:
        pytest.fail("guard_charge shop entry not found in static/app.jsx")
    return m.group(1)


def test_shop_desc_no_longer_mentions_regen_shield():
    """T215 AC#1: shop description is accurate (does not falsely link
    Guard Charge regen to the Regen Shield item)."""
    desc = _guard_charge_shop_desc()
    assert 'Regen Shield' not in desc, (
        f"guard_charge desc still mentions Regen Shield: {desc!r}"
    )


def test_shop_desc_mentions_50_spin_regen():
    """T215 AC#1 (companion): the new description must reflect the
    implemented passive regen cadence — 1 charge every 50 spins."""
    desc = _guard_charge_shop_desc()
    assert '50 spins' in desc, (
        f"guard_charge desc should mention '50 spins' (the regen cadence): "
        f"{desc!r}"
    )
    # Sanity: cap is mentioned.
    assert '3' in desc, f"guard_charge desc should mention the 3-charge cap: {desc!r}"


def test_compiled_app_js_matches_jsx():
    """The compiled app.js must mirror the JSX change (so the browser sees
    the corrected description)."""
    jsx_desc = _guard_charge_shop_desc()
    js_src = _read(APP_JS_PATH)
    # Babel escapes the apostrophes as \x27 in the compiled output.
    needle = jsx_desc.replace("'", "\\x27")
    assert needle in js_src, (
        f"static/app.js missing the updated guard_charge desc: {jsx_desc!r}"
    )


# ════════════════════════════════════════════════════════════════════════════
# B. Regen condition unit tests (pure-Python, no DB)
# ════════════════════════════════════════════════════════════════════════════
def _apply_regen(spin_count, owns_guard_charge, guard_charges, max_charges=3, recharge_every=50):
    """Mirror of the regen condition in game.py's /api/spin handler.

    Pure function so the unit tests don't need a DB. The handler runs:
        if (owns_guard_charge
                and new_spin_count > 0
                and new_spin_count % GUARD_CHARGE_RECHARGE_SPINS == 0
                and prev_guard_charges < GUARD_CHARGE_MAX):
            new_guard_charges = min(GUARD_CHARGE_MAX, prev_guard_charges + 1)
    """
    if (owns_guard_charge
            and spin_count > 0
            and spin_count % recharge_every == 0
            and guard_charges < max_charges):
        return min(max_charges, guard_charges + 1)
    return guard_charges


def test_regen_fires_on_spin_50_100_150_200_1000():
    """T215 AC#2: regen fires on spin #50, #100, #150, etc."""
    for spin_count in (50, 100, 150, 200, 1000, 5000):
        assert _apply_regen(spin_count, True, 0) == 1, (
            f"regen failed at spin_count={spin_count}"
        )


def test_regen_does_not_fire_off_multiple():
    """Regen must NOT fire on spin #1, #49, #51, #99, #101, etc."""
    for spin_count in (1, 2, 25, 49, 51, 99, 101, 149, 1001):
        assert _apply_regen(spin_count, True, 0) == 0, (
            f"regen wrongly fired at spin_count={spin_count}"
        )


def test_regen_does_not_fire_without_item():
    """T215 AC#4: regen is passive but still requires the player to have
    bought the guard_charge item at least once. Without ownership, no regen.
    """
    assert _apply_regen(50, owns_guard_charge=False, guard_charges=0) == 0
    assert _apply_regen(100, owns_guard_charge=False, guard_charges=0) == 0


def test_regen_caps_at_3():
    """T215 AC#3: guard_charges never exceeds 3, even when regen fires
    while the player is already at the cap."""
    # Already at cap: no change.
    assert _apply_regen(50, True, 3) == 3
    # Below cap: increments to 3.
    assert _apply_regen(50, True, 2) == 3
    # Way below cap: increments by 1 only (not by 50).
    assert _apply_regen(50, True, 0) == 1


def test_regen_requires_positive_spin_count():
    """Defence: spin_count > 0 is checked explicitly so a fresh player
    (spin_count == 0) doesn't get a phantom regen."""
    assert _apply_regen(0, True, 0) == 0


# ════════════════════════════════════════════════════════════════════════════
# C. models.py constants
# ════════════════════════════════════════════════════════════════════════════
def test_models_has_guard_charge_recharge_constant():
    """T215: the recharge cadence must be a single source of truth in
    models.py (not a magic number scattered in game.py)."""
    sys.path.insert(0, REPO_ROOT)
    import models
    assert hasattr(models, 'GUARD_CHARGE_RECHARGE_SPINS'), (
        "models.GUARD_CHARGE_RECHARGE_SPINS missing — T215 fix incomplete"
    )
    assert models.GUARD_CHARGE_RECHARGE_SPINS == 50, (
        f"expected GUARD_CHARGE_RECHARGE_SPINS=50, "
        f"got {models.GUARD_CHARGE_RECHARGE_SPINS}"
    )


def test_models_has_guard_charge_max_constant():
    import models
    assert hasattr(models, 'GUARD_CHARGE_MAX')
    assert models.GUARD_CHARGE_MAX == 3


# ════════════════════════════════════════════════════════════════════════════
# D. Regen Shield regression — its mechanics must remain untouched
# ════════════════════════════════════════════════════════════════════════════
def test_regen_shield_unaffected():
    """T215 AC#6: the Regen Shield item (`regen_shield`) is a separate
    mechanic. T215 must not touch its constants or behaviour."""
    import models
    # The Regen Shield constant still exists with its original value.
    assert hasattr(models, 'REGEN_SHIELD_RECHARGE_WINS')
    assert models.REGEN_SHIELD_RECHARGE_WINS == 5
    # The new T215 constant is distinct from the Regen Shield one.
    assert models.GUARD_CHARGE_RECHARGE_SPINS != models.REGEN_SHIELD_RECHARGE_WINS
    # The Regen Shield item entry in SHOP_ITEMS is untouched.
    assert 'regen_shield' in models.SHOP_ITEMS
    assert 'guard_charge' in models.SHOP_ITEMS


def test_trigger_guard_charge_endpoint_decrement_unchanged():
    """T215 must not modify the /api/guard endpoint — its decrement-on-use
    is correct. The handler at game.py should still call
    `UPDATE game_state SET guard_charges = guard_charges - 1`."""
    src = _read(GAME_PY_PATH)
    assert "SET guard_charges = guard_charges - 1" in src, (
        "/api/guard decrement was modified — T215 must not change it"
    )


# ════════════════════════════════════════════════════════════════════════════
# E. Spin handler integration: regen is wired in
# ════════════════════════════════════════════════════════════════════════════
def test_spin_handler_includes_guard_charge_regen_block():
    """The /api/spin handler in game.py must reference the new constant
    and update guard_charges in its UPDATE statement."""
    src = _read(GAME_PY_PATH)
    assert 'GUARD_CHARGE_RECHARGE_SPINS' in src, (
        "game.py does not import/use GUARD_CHARGE_RECHARGE_SPINS"
    )
    # The handler's UPDATE writes guard_charges with a placeholder, and
    # the regen code path is bracketed by an explicit `new_guard_charges`.
    assert 'new_guard_charges' in src, (
        "game.py missing the new_guard_charges regen computation"
    )
    # The handler's UPDATE statement must write guard_charges.
    assert 'guard_charges = %s' in src, (
        "game.py's spin UPDATE statement does not write guard_charges"
    )


def test_spin_handler_does_not_break_other_unchanged_items():
    """T215 must not touch the Regen Shield path or the /api/guard endpoint."""
    src = _read(GAME_PY_PATH)
    # The trigger_guard_charge endpoint still decrements by 1.
    assert "SET guard_charges = guard_charges - 1" in src
    # Regen Shield re-initialization on buy is untouched.
    assert "new_regen_recharge = 0 if item_id == 'regen_shield'" in src
