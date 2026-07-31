"""T211: casino title + dice panel label/desc must use the S8 (Casino) theme palette.

Pure source-string assertions against `static/styles.css`. No Playwright,
no Flask server, no DB. Mirrors the simple file-content test style used
in tests/test_mobile_css.py.

T211 adds a `body.page-season8` block with three new rules to the S8 page
theme section (around line 3820):
  - `.casino-title` — S8 green primary, with a green→red neon glow
  - `.dice-panel-label` — S8 green primary light
  - `.dice-panel-desc`  — S8 green primary mid (muted)

The S8 page theme defines `--p: #1FBE5C` (green) and `--s: #E23030` (red).
Using green for the title and dice label keeps those elements consistent
with the existing S8 pointer / score-label / center-hub accents, and the
green→red text-shadow matches the existing S8 wheel-hub glow pattern.

Regression coverage ensures the S1 `.casino-title` (#FFD700 gold) and the
S5 `.dice-panel-label` (#80EEFF cyan) overrides are NOT clobbered.
"""
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
STYLES_CSS = REPO_ROOT / 'static' / 'styles.css'


@pytest.fixture(scope='module')
def styles_css() -> str:
    return STYLES_CSS.read_text(encoding='utf-8')


def _rule_body(css: str, selector: str) -> str:
    """Return the body of the first CSS rule whose selector matches.

    Handles multi-line whitespace between the selector and `{` and matches
    balanced braces inside the body (declarations only — no nested rules
    in this file, so `[^}]*` is safe).
    """
    m = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', css)
    return m.group(1) if m else ''


def test_casino_title_color_on_page_season8(styles_css):
    """T211: the S8 casino title must use the S8 green primary accent
    (#45E27A, matching .pointer / .score-label / .center-hub border),
    not the default purple `--p` (#7766FF) which the operator reported
    as the wrong colour.
    """
    body = _rule_body(styles_css, 'body.page-season8 .casino-title')
    assert body, (
        'body.page-season8 .casino-title rule is missing from static/styles.css '
        '— T211 casino title override was not added.'
    )
    assert re.search(r'color:\s*#45E27A\b', body), (
        f'expected body.page-season8 .casino-title to set color: #45E27A '
        f'(S8 primary light green), got body: {body!r}'
    )
    # S8 neon glow — green core, green mid, red deep (matches .center-hub
    # box-shadow pattern of mixing the green primary with the red secondary).
    assert '#45E27A' in body and '#1FBE5C' in body and '#E23030' in body, (
        'expected body.page-season8 .casino-title text-shadow to use the '
        'S8 green→red neon glow (#45E27A / #1FBE5C / #E23030).'
    )


def test_dice_panel_label_color_on_page_season8(styles_css):
    """T211: the S8 dice panel label ('🎲 Dice Roll') must be in the S8
    primary light green (#45E27A), not the default lavender (#c4a0e0).
    """
    body = _rule_body(styles_css, 'body.page-season8 .dice-panel-label')
    assert body, (
        'body.page-season8 .dice-panel-label rule is missing — '
        'T211 dice panel label override was not added.'
    )
    assert re.search(r'color:\s*#45E27A\b', body), (
        f'expected body.page-season8 .dice-panel-label to set '
        f'color: #45E27A, got body: {body!r}'
    )


def test_dice_panel_desc_color_on_page_season8(styles_css):
    """T211: the S8 dice panel description must use a muted S8 green
    (#138C42, primary mid) for less visual weight than the label.
    """
    body = _rule_body(styles_css, 'body.page-season8 .dice-panel-desc')
    assert body, (
        'body.page-season8 .dice-panel-desc rule is missing — '
        'T211 dice panel desc override was not added.'
    )
    assert re.search(r'color:\s*#138C42\b', body), (
        f'expected body.page-season8 .dice-panel-desc to set '
        f'color: #138C42 (muted S8 green), got body: {body!r}'
    )


def test_season1_casino_title_unchanged(styles_css):
    """T211 regression: the S1 casino title must remain gold (#FFD700).
    Ensures the new S8 block did not displace or override the S1 rule.
    """
    body = _rule_body(styles_css, 'body.page-season1 .casino-title')
    assert body, (
        'body.page-season1 .casino-title rule is missing — '
        'T211 may have accidentally removed the S1 casino-title override.'
    )
    assert re.search(r'color:\s*#FFD700\b', body), (
        f'expected body.page-season1 .casino-title to remain color: #FFD700 '
        f'(S1 gold), got body: {body!r}'
    )


def test_season5_dice_panel_unchanged(styles_css):
    """T211 regression: the S5 dice panel label must remain cyan (#80EEFF).
    Ensures the new S8 block did not displace or override the S5 rule.
    """
    body = _rule_body(styles_css, 'body.page-season5 .dice-panel-label')
    assert body, (
        'body.page-season5 .dice-panel-label rule is missing — '
        'T211 may have accidentally removed the S5 dice-panel override.'
    )
    assert re.search(r'color:\s*#80EEFF\b', body), (
        f'expected body.page-season5 .dice-panel-label to remain '
        f'color: #80EEFF (S5 cyan), got body: {body!r}'
    )


def test_s8_overrides_within_season8_block(styles_css):
    """T211: the new S8 rules must be co-located with the existing
    S8 page-theme section (between the start of the S8 block and the
    Hiatus Screen section), not stranded somewhere unrelated in the file.
    Also verifies the relative order: casino-title → dice-panel-label →
    dice-panel-desc.
    """
    season8_start = styles_css.find('body.page-season8 {')
    hiatus_start = styles_css.find('/* ── Hiatus Screen')
    assert season8_start != -1, 'body.page-season8 { page-theme block not found'
    assert hiatus_start != -1, 'Hiatus Screen section not found in styles.css'
    assert season8_start < hiatus_start, (
        'expected the S8 page-theme block to come BEFORE the Hiatus Screen section'
    )

    new_selectors = [
        'body.page-season8 .casino-title',
        'body.page-season8 .dice-panel-label',
        'body.page-season8 .dice-panel-desc',
    ]
    positions = []
    for selector in new_selectors:
        pos = styles_css.find(selector)
        assert pos != -1, f'{selector} not found in static/styles.css'
        assert season8_start < pos < hiatus_start, (
            f'{selector} at file offset {pos} is not within the S8 page-theme '
            f'section (offsets {season8_start}..{hiatus_start}). The new T211 '
            f'rules must be co-located with the existing S8 page-theme overrides.'
        )
        positions.append(pos)

    assert positions == sorted(positions), (
        f'expected the new T211 rules in the order '
        f'casino-title → dice-panel-label → dice-panel-desc, got offsets: '
        f'{dict(zip(new_selectors, positions))}'
    )


def test_default_p_variable_unchanged(styles_css):
    """T211 hard constraint: the :root `--p` variable (global default
    primary colour) must NOT have been changed. Per-season overrides are
    the right mechanism for S8 theming.
    """
    root_body = _rule_body(styles_css, ':root')
    assert root_body, ':root block is missing from static/styles.css'
    assert re.search(r'--p:\s*#7766FF\b', root_body), (
        f'expected :root --p to remain #7766FF (global default), '
        f'got :root body: {root_body!r}'
    )
