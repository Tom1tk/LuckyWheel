"""Tests for Season 9 theme/shop/catalog additions."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import models


def test_page_season9_in_shop():
    assert 'page_season9' in models.SHOP_ITEMS, "page_season9 must be buyable"
    assert models.SHOP_ITEMS['page_season9']['cost'] == 1_000


def test_arcade_wheel_themes():
    assert 'theme_arcade' in models.SHOP_ITEMS
    assert 'theme_pixel' in models.SHOP_ITEMS
    assert 'theme_holo' in models.SHOP_ITEMS
    # Chain: pixel requires arcade; holo requires pixel.
    assert models.SHOP_ITEMS['theme_pixel']['requires'] == 'theme_arcade'
    assert models.SHOP_ITEMS['theme_holo']['requires'] == 'theme_pixel'


def test_arcade_fish_skins():
    for skin, cost in [('fish_joystick', 3_000_000),
                       ('fish_pixel', 4_500_000),
                       ('fish_ghost', 6_000_000)]:
        assert skin in models.FISH_SKINS, f"{skin} must be a fish skin"
        assert models.FISH_SKINS[skin]['cost'] == cost


def test_new_items_are_cosmetic_currency():
    for item in ['page_season9', 'theme_arcade', 'theme_pixel', 'theme_holo',
                 'fish_joystick', 'fish_pixel', 'fish_ghost']:
        assert models.ITEM_CURRENCY[item] == 'losses', (
            f"{item} must be a cosmetic (losses) item"
        )


def test_singularity_per_player_cap_retuned():
    assert models.SINGULARITY_PER_PLAYER_CAP == 2_000_000, (
        "Season 9 singularity per-player cap should be 2M (was 25M)"
    )


def test_migrations_present():
    root = os.path.dirname(os.path.dirname(__file__))
    for name in ['073_season9_theme.sql',
                 '074_singularity_retune.sql',
                 '075_community_goals_retune.sql']:
        assert os.path.exists(os.path.join(root, 'migrations', name)), (
            f"missing migration {name}"
        )
