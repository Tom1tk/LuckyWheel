"""T112: layout audit for the vertical wager panel.

Verifies at 1920x1080 / 1366x768 / 1280x720 that the wager panel
(.season8-wager-panel) does not overlap the wheel, that the stake steps
stack with 0% at the BOTTOM, and that clicking a step selects it.
"""
import os
import uuid

import psycopg2
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope='module')
def logged_in_context(server_url, db_url):
    with sync_playwright() as p:
        b = p.chromium.launch()
        context = b.new_context()
        page = context.new_page()
        page.goto(server_url + '/')
        page.wait_for_load_state('domcontentloaded')
        username = f't112{uuid.uuid4().hex[:10]}'
        password = 'testpass123'
        result = page.evaluate(
            '''async ({u, p}) => {
                const me = await fetch('/api/me');
                const meData = await me.json();
                const csrf = meData.csrf_token;
                const r = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf
                    },
                    body: JSON.stringify({username: u, password: p})
                });
                const data = await r.json();
                return {ok: r.ok, status: r.status, error: data.error || null};
            }''',
            {'u': username, 'p': password},
        )
        if not result['ok'] and result['error'] and 'taken' not in result['error']:
            b.close()
            pytest.fail(f'register failed: {result["error"]}')
        # T108 follow-up: the wager panel only renders when the player
        # owns wager_unlock. Grant it via SQL so the fixture user sees
        # the panel (these tests check layout, not the unlock flow).
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                '''UPDATE game_state
                   SET owned_items = ARRAY(
                       SELECT DISTINCT unnest(
                           owned_items || ARRAY['wager_unlock']
                       )
                   )
                   WHERE user_id = (SELECT id FROM users WHERE username = %s)''',
                (username,),
            )
        conn.close()
        page.reload()
        page.wait_for_selector('.season8-wager-panel', timeout=5000)
        yield context
        b.close()


@pytest.fixture()
def logged_in_page(logged_in_context):
    page = logged_in_context.new_page()
    page.goto(logged_in_context._impl_obj._pages[0].url if logged_in_context._impl_obj._pages else '/')
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_selector('.season8-wager-panel', timeout=10000)
    yield page
    page.close()


RESOLUTIONS = [
    ('1920x1080', 1920, 1080),
    ('1366x768', 1366, 768),
    ('1280x720', 1280, 720),
]


@pytest.mark.parametrize('name,width,height', RESOLUTIONS)
def test_wager_panel_does_not_overlap_wheel(name, width, height, logged_in_page):
    page = logged_in_page
    page.set_viewport_size({'width': width, 'height': height})
    page.wait_for_timeout(150)
    panel = page.locator('.season8-wager-panel').bounding_box()
    wheel = page.locator('.wheel-wrapper').bounding_box()
    assert panel is not None, f'wager panel not visible at {name}'
    assert wheel is not None, f'wheel not visible at {name}'
    px1, py1 = panel['x'], panel['y']
    px2, py2 = panel['x'] + panel['width'], panel['y'] + panel['height']
    wx1, wy1 = wheel['x'], wheel['y']
    wx2, wy2 = wheel['x'] + wheel['width'], wheel['y'] + wheel['height']
    x_overlap = px1 < wx2 and wx1 < px2
    y_overlap = py1 < wy2 and wy1 < py2
    assert not (x_overlap and y_overlap), (
        f'wager panel ({px1:.0f},{py1:.0f},{px2:.0f},{py2:.0f}) '
        f'overlaps wheel ({wx1:.0f},{wy1:.0f},{wx2:.0f},{wy2:.0f}) at {name}'
    )


@pytest.mark.parametrize('name,width,height', RESOLUTIONS)
def test_wager_panel_sits_close_to_wheel(name, width, height, logged_in_page):
    """At >=1366px, the panel must sit immediately to the left of the wheel
    (gap < 80px). At <1366px the layout falls back to below-the-wheel, so the
    panel can sit below (large vertical gap is expected)."""
    page = logged_in_page
    page.set_viewport_size({'width': width, 'height': height})
    page.wait_for_timeout(150)
    panel = page.locator('.season8-wager-panel').bounding_box()
    wheel = page.locator('.wheel-wrapper').bounding_box()
    if width >= 1366:
        gap_x = wheel['x'] - (panel['x'] + panel['width'])
        assert 0 <= gap_x < 80, (
            f'wager panel should sit immediately to the left of the wheel '
            f'(gap_x={gap_x:.0f}px) at {name}; large gap means the panel '
            f'is not anchored to the wheel'
        )


@pytest.mark.parametrize('name,width,height', RESOLUTIONS)
def test_wager_panel_vertically_centered_with_wheel(name, width, height, logged_in_page):
    """At >=1366px, the panel and wheel should have matching vertical centers
    (offset < 5px). At <1366px the layout falls back to a vertical stack."""
    page = logged_in_page
    page.set_viewport_size({'width': width, 'height': height})
    page.wait_for_timeout(150)
    panel = page.locator('.season8-wager-panel').bounding_box()
    wheel = page.locator('.wheel-wrapper').bounding_box()
    if width >= 1366:
        panel_cy = panel['y'] + panel['height'] / 2
        wheel_cy = wheel['y'] + wheel['height'] / 2
        offset = abs(panel_cy - wheel_cy)
        assert offset < 5, (
            f'wager panel center ({panel_cy:.0f}) should match wheel '
            f'center ({wheel_cy:.0f}) at {name}; offset={offset:.0f}px'
        )


@pytest.mark.parametrize('name,width,height', RESOLUTIONS)
def test_wager_panel_inside_viewport(name, width, height, logged_in_page):
    page = logged_in_page
    page.set_viewport_size({'width': width, 'height': height})
    page.wait_for_timeout(150)
    panel = page.locator('.season8-wager-panel').bounding_box()
    assert panel is not None
    assert panel['y'] >= 0, f'panel clipped at top at {name}'
    assert panel['y'] + panel['height'] <= height + 1, (
        f'panel clipped at bottom at {name}: '
        f'panel bottom = {panel["y"] + panel["height"]:.0f}, viewport = {height}'
    )


def test_wheel_grows_at_desktop(logged_in_page):
    """T112 v2: at 1920x1080 the wheel is at least 500px so it dominates the page."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.wait_for_timeout(150)
    wheel = page.locator('.wheel-wrapper').bounding_box()
    assert wheel['width'] >= 500, (
        f'wheel width ({wheel["width"]:.0f}) should be at least 500px to dominate the page'
    )


def test_screenshot_clean_layout(logged_in_page):
    """T112: capture a clean screenshot of the vertical wager panel layout."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.wait_for_timeout(200)
    page.evaluate(
        '''() => {
            const card = document.querySelector('.patch-notes-card');
            if (card) {
                const closeBtn = card.querySelector('button, .close, [aria-label]');
                if (closeBtn) closeBtn.click();
                else card.remove();
            }
        }'''
    )
    page.wait_for_timeout(100)
    screenshot_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'static', 'screenshots',
    )
    os.makedirs(screenshot_dir, exist_ok=True)
    page.screenshot(path=os.path.join(screenshot_dir, 't112_1920x1080.png'), full_page=False)


def test_stake_steps_stack_zero_at_bottom(logged_in_page):
    """Stake steps run bottom (0%) to top (max) on the side panel."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.wait_for_timeout(150)
    steps = page.locator('.stake-step')
    first = steps.first.bounding_box()
    last = steps.last.bounding_box()
    assert steps.first.inner_text() == '0%'
    assert first['y'] > last['y'], '0% step must sit below the max step'


def test_stake_step_click_selects(logged_in_page):
    """Clicking a step marks it active, fills the steps below it and shows the odds."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.locator('.stake-step', has_text='10%').first.click()
    page.wait_for_timeout(300)
    assert page.locator('.stake-step.active').inner_text() == '10%'
    assert page.locator('.stake-step.filled').count() == 3
    assert page.locator('.stake-step[aria-checked="true"]').count() == 1
    assert 'Lose' in page.locator('.wager-stake-value').inner_text()
    page.locator('.stake-step', has_text='0%').first.click()
    page.wait_for_timeout(300)
    assert page.locator('.wager-stake-value').inner_text() == 'No risk'


def test_stake_info_button_toggles_explainer(logged_in_page):
    """The ? button opens the explainer on click (works on touch, unlike a hover tooltip)."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    btn = page.locator('.stake-info-btn')
    assert page.locator('.stake-explainer').count() == 0
    btn.click()
    assert page.locator('.stake-explainer').is_visible()
    assert btn.get_attribute('aria-expanded') == 'true'
    btn.click()
    assert page.locator('.stake-explainer').count() == 0
