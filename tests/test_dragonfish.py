"""Tests for the Season 9 dragonfish (rarest legendary catch)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import models


def test_dragonfish_in_catalog():
    d = models.FISH_CATALOG['dragonfish']
    assert d['value'] == 150, "dragonfish value should be 150"
    assert d['tier'] == 'Legendary', "dragonfish is legendary"
    assert d['weight'] == 0.15, "dragonfish weight should be 0.15"
    assert d['emoji'] == '🐲'


def test_dragonfish_is_most_valuable_fish():
    assert models.FISH_CATALOG['dragonfish']['value'] == max(
        f['value'] for f in models.FISH_CATALOG.values()
    ), "dragonfish must be the single most valuable catch"


def test_dragonfish_is_rarest_fish():
    assert models.FISH_CATALOG['dragonfish']['weight'] == min(
        f['weight'] for f in models.FISH_CATALOG.values()
    ), "dragonfish must be the single rarest catch"


def test_dragonfish_excluded_from_auto_fish():
    assert 'dragonfish' in models._AUTO_FISH_LEGENDARY, (
        "dragonfish must be in _AUTO_FISH_LEGENDARY"
    )
    assert 'dragonfish' in models.AUTO_FISH_EXCLUDED, (
        "dragonfish must never be auto-catchable"
    )
    assert 'dragonfish' not in models._AUTO_IDS, (
        "dragonfish must not appear in the auto-fish weighted list"
    )


def test_dragonfish_still_catchable_by_hand():
    assert 'dragonfish' in models._ALL_IDS, (
        "dragonfish must remain in the manual-catch catalog"
    )
