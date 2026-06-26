"""T200: mobile CSS scaffolding — drawer + below-wheel wager styles.

Pure source-string assertions against `static/styles.css`. No Playwright,
no Flask server, no DB. Mirrors the simple file-content test style used
elsewhere in the suite.

The T200 spec adds a new `@media (max-width: 768px)` block at the END of
`static/styles.css` (after the existing one at line ~2413) with classes
for the new mobile drawer (.mobile-drawer, .mobile-drawer-tabs,
.mobile-drawer-tab, .mobile-drawer-section) and the below-wheel wager
panel overrides (.mobile-below-wheel .season8-wager-panel and friends).
"""
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
STYLES_CSS = REPO_ROOT / 'static' / 'styles.css'


@pytest.fixture(scope='module')
def styles_css() -> str:
    return STYLES_CSS.read_text(encoding='utf-8')


def test_mobile_drawer_class_exists(styles_css):
    """T200: the new mobile drawer class is defined, and the new T200
    `@media (max-width: 768px)` block sits at the end of styles.css
    alongside the existing one at line ~2413.

    The T200 spec says: "@media (max-width: 768px)" must appear at least
    twice (once for the existing block, once for the new T200 block).
    """
    assert '.mobile-drawer' in styles_css, (
        '.mobile-drawer class is missing from static/styles.css — '
        'T200 drawer scaffolding was not added.'
    )
    media_count = styles_css.count('@media (max-width: 768px)')
    assert media_count >= 2, (
        f'expected >= 2 occurrences of "@media (max-width: 768px)" '
        f'(existing block at line ~2413 + new T200 block at end), '
        f'got {media_count}.'
    )


def test_mobile_wager_below_wheel_class_exists(styles_css):
    """T200: the below-wheel wager panel scoped override is defined.

    `.mobile-below-wheel .season8-wager-panel` is the parent-scoped
    selector that overrides the desktop absolute positioning so the
    wager panel renders as a full-width block between the wheel and
    the Spin prompt on <=768px viewports.
    """
    assert '.mobile-below-wheel .season8-wager-panel' in styles_css, (
        '.mobile-below-wheel .season8-wager-panel selector is missing '
        'from static/styles.css — T200 below-wheel wager override was '
        'not added.'
    )


def test_mobile_drawer_tab_class_exists(styles_css):
    """T200: the drawer tab button + its active-state modifier exist.

    The drawer surfaces S8 panels as tabs at the top; the active tab is
    styled via `.mobile-drawer-tab.active` (border-color: currentColor
    so JSX can theme each tab by its emoji color).
    """
    assert '.mobile-drawer-tab' in styles_css, (
        '.mobile-drawer-tab class is missing from static/styles.css — '
        'T200 drawer tab button was not added.'
    )
    assert '.mobile-drawer-tab.active' in styles_css, (
        '.mobile-drawer-tab.active modifier is missing from '
        'static/styles.css — T200 active tab state was not added.'
    )
