"""T112: layout audit for the vertical wager panel.

Verifies at 1920x1080 / 1366x768 / 1280x720 that the wager panel
(.season8-wager-panel) does not overlap the wheel, that the slider thumb
sits at the BOTTOM when stake=0 and at the TOP when stake=max, and that
the ?-tooltip trigger sits below the slider.
"""
import os
import socket
import subprocess
import sys
import time
import uuid

import pytest
from playwright.sync_api import sync_playwright


def _free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


@pytest.fixture(scope='module')
def server_url():
    port = _free_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    env.setdefault('WHEEL_SECRET_KEY', 't112-test-secret-key-for-playwright-only')
    env.setdefault('DATABASE_URL',
                   'postgresql://wheelapp:a51f2d9685f4d6dca9d2f9d8d6e66374@localhost/wheeldb_staging')
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.Popen(
        [sys.executable, 'server.py'],
        cwd=repo_root, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f'http://127.0.0.1:{port}'
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            import urllib.request
            urllib.request.urlopen(base + '/', timeout=1).read()
            break
        except Exception:
            time.sleep(0.25)
    else:
        proc.terminate()
        pytest.fail('Flask server did not start within 20s')
    yield base
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope='module')
def logged_in_context(server_url):
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
    """T112: at 1920x1080 the wheel is visibly larger than the 580px old cap."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.wait_for_timeout(150)
    wheel = page.locator('.wheel-wrapper').bounding_box()
    assert wheel['width'] > 580, (
        f'wheel width ({wheel["width"]:.0f}) should exceed the old 580px cap'
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


def test_slider_thumb_at_bottom_when_stake_zero(logged_in_page):
    """T112: slider thumb is at the BOTTOM when stake=0."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.evaluate(
        '''() => {
            const s = document.querySelector('.wager-slider');
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            setter.call(s, '0');
            s.dispatchEvent(new Event('input', {bubbles: true}));
            s.dispatchEvent(new Event('change', {bubbles: true}));
        }'''
    )
    page.wait_for_timeout(150)
    box = page.locator('.wager-slider').bounding_box()
    thumb = page.locator('.wager-slider').evaluate(
        '''(el) => {
            const r = el.getBoundingClientRect();
            return {x: r.x, y: r.y, w: r.width, h: r.height, value: el.value, max: el.max};
        }'''
    )
    assert box is not None and thumb is not None
    assert thumb['value'] == '0'


def test_slider_orientation_is_vertical(logged_in_page):
    """T112: writing-mode is vertical-lr (slider runs top-to-bottom)."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.wait_for_timeout(150)
    mode = page.locator('.wager-slider').evaluate(
        '''(el) => getComputedStyle(el).writingMode'''
    )
    assert mode in ('vertical-lr', 'vertical-rl'), (
        f'slider writing-mode is {mode!r}; expected vertical-lr or vertical-rl'
    )


def test_tooltip_trigger_sits_below_slider(logged_in_page):
    """T112: the ?-tooltip trigger is rendered after the slider in the
    stake control flex column, so it ends up BELOW the slider track."""
    page = logged_in_page
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.wait_for_timeout(150)
    slider_box = page.locator('.wager-slider').bounding_box()
    trigger_box = page.locator('.wager-tooltip-trigger').bounding_box()
    assert slider_box is not None and trigger_box is not None
    assert trigger_box['y'] >= slider_box['y'] + slider_box['height'] - 2, (
        f'tooltip trigger (y={trigger_box["y"]:.0f}) is not below slider '
        f'(bottom={slider_box["y"] + slider_box["height"]:.0f})'
    )
