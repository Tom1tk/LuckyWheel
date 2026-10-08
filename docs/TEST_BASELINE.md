# Test baseline (Revival Phase 0.3)

Recorded 2026-10-08 against a fresh `wheeldb_test` (schema.sql + all migrations).
Rule for every revival ticket: **no new failures vs this list.**

- master `f77fb55`: 844 passed, 4 failed, 12 errors, 1 skipped
- staging + leak fix: 845 passed (+ `test_db_pin.py`), same 16 failures/errors

All 16 are Playwright mobile UI tests (S8 drawer layout / mobile e2e fixture setup);
pre-existing, not caused by revival work. RV-06/RV-08 should fix or retire them.

```
ERROR tests/test_mobile_e2e.py::test_bounties_panel_visible_on_mobile_after_t202
ERROR tests/test_mobile_e2e.py::test_community_goal_visible_on_mobile_after_t202
ERROR tests/test_mobile_e2e.py::test_free_tokens_section_visible_on_mobile_after_t202
ERROR tests/test_mobile_e2e.py::test_leaderboard_visible_on_mobile - Assertio...
ERROR tests/test_mobile_e2e.py::test_loadout_panel_visible_on_mobile_after_t202
ERROR tests/test_mobile_e2e.py::test_main_wheel_visible_on_mobile[mobile_viewport0]
ERROR tests/test_mobile_e2e.py::test_main_wheel_visible_on_mobile[mobile_viewport1]
ERROR tests/test_mobile_e2e.py::test_main_wheel_visible_on_mobile[mobile_viewport2]
ERROR tests/test_mobile_e2e.py::test_mobile_toolbar_renders_5_buttons - Asser...
ERROR tests/test_mobile_e2e.py::test_prestige_panel_visible_on_mobile_after_t202
ERROR tests/test_mobile_e2e.py::test_shop_panel_visible_on_mobile - Assertion...
ERROR tests/test_mobile_mode_centering.py::test_mode_buttons_centered_on_mobile
FAILED tests/test_mobile_drawer_style.py::test_s8_drawer_does_not_cover_toolbar
FAILED tests/test_mobile_drawer_style.py::test_s8_drawer_no_close_button - As...
FAILED tests/test_mobile_drawer_style.py::test_s8_drawer_no_header - Assertio...
FAILED tests/test_mobile_drawer_style.py::test_s8_drawer_z_index_matches_shop
```
