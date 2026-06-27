"""T223: Shop cleanup — fish_to_wager removed, duplicate wager section removed.

Bug report (operator, 2026-06-27):
  1. 'fish_to_wager' was a legacy item in the shop that wasn't supposed
     to exist there. The item still lives in models.SHOP_ITEMS (for the
     one-time +5 insurance_tokens grant on first purchase) but the shop
     UI no longer offers it for purchase.
  2. The '⚡ Season 8: Wager System' section appeared in the shop twice
     (once above Special Upgrades and once below). The lower duplicate
     was removed.

These tests pin both fixes so they don't regress.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

ROOT    = os.path.dirname(os.path.dirname(__file__))
APP_JSX = os.path.join(ROOT, 'static', 'app.jsx')


def _read(path):
    with open(path) as f:
        return f.read()


# ── T223: fish_to_wager removed from the shop ─────────────────────────────

def test_fish_to_wager_not_a_shop_entry():
    """T223: fish_to_wager must not appear as a buyable shop entry
    in the JSX SHOP_ITEMS array. The string may still appear in code
    (e.g. the pay-with-tokens toggle gate, insurance-buy checks), but
    never as `{ id: 'fish_to_wager', ... }`."""
    jsx = _read(APP_JSX)
    assert "{ id: 'fish_to_wager'" not in jsx, (
        "fish_to_wager must not be a buyable shop entry in app.jsx "
        "(T223: removed from the shop UI)"
    )
    assert '{ id: "fish_to_wager"' not in jsx, (
        "fish_to_wager must not be a buyable shop entry in app.jsx "
        "(double-quote variant)"
    )


def test_fish_to_wager_still_in_jsx_for_other_logic():
    """T223: the string 'fish_to_wager' must still appear in app.jsx —
    the pay-with-tokens toggle, insurance-buy endpoint check, and the
    models.py comment all reference it. Removing the shop entry is the
    only change; the underlying game logic is untouched."""
    jsx = _read(APP_JSX)
    assert 'fish_to_wager' in jsx, (
        "fish_to_wager should still appear in app.jsx for the "
        "pay-with-tokens toggle and other internal references"
    )


# ── T223: only one 'Season 8: Wager System' section ───────────────────────

def test_only_one_wager_system_section():
    """T223: the 'Season 8: Wager System' section must appear exactly
    once in the shop. The lower duplicate (below 'Special Upgrades')
    was removed."""
    jsx = _read(APP_JSX)
    matches = re.findall(r"label:\s*['\"]⚡\s*Season 8:\s*Wager System['\"]", jsx)
    assert len(matches) == 1, (
        f"expected exactly 1 'Season 8: Wager System' section, found {len(matches)}"
    )


def test_wager_unlock_in_exactly_one_section():
    """T223 sanity: the wager_unlock entry (a section's first item) should
    appear in exactly one shop entry line. Before the fix it appeared
    in both duplicate sections."""
    jsx = _read(APP_JSX)
    matches = re.findall(r"\{ id:\s*'wager_unlock'", jsx)
    assert len(matches) == 1, (
        f"wager_unlock shop entry must appear exactly once, found {len(matches)}"
    )


def test_auto_spin_unlock_in_exactly_one_section():
    """T223 sanity: auto_spin_unlock is the last item of the wager
    section. Before the fix it appeared in both duplicate sections."""
    jsx = _read(APP_JSX)
    matches = re.findall(r"\{ id:\s*'auto_spin_unlock'", jsx)
    assert len(matches) == 1, (
        f"auto_spin_unlock shop entry must appear exactly once, found {len(matches)}"
    )
