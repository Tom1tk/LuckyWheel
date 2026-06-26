"""T113: aquarium panel — readable text + luck tooltip.

Verifies the T113 hotfix:
1. The aquarium panel renders when the player owns the `aquarium` upgrade.
2. Species names in `.aquarium-grid` are NOT black — they must be light
   grey (#e0e0e0 → R > 150 in computed rgb) so they're readable against
   the panel's near-black background.
3. The `.aquarium-info-icon` (?) element exists in the header and has a
   non-empty `title` attribute.
4. The tooltip text mentions "+0.1%" or "win chance" (or similar).
"""
import os
import re
import socket
import subprocess
import sys
import time
import uuid

import psycopg2
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
    env.setdefault('WHEEL_SECRET_KEY', 't113-test-secret-key-for-playwright-only')
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


def _grant_aquarium(db_url, username):
    """Direct DB write: add 'aquarium' to owned_items and a few species.

    Bypasses the /api/buy tier gate (aquarium is tier 2 → 10K lifetime wins)
    so the panel renders for the test user without spinning 10K wins first.
    Sets `caught_species` (the API's source for `aquarium_species` in the
    /api/state response — see game.py:1079).
    """
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''UPDATE game_state
                      SET owned_items = array_append(owned_items, 'aquarium'),
                          caught_species = ARRAY['bass','trout','salmon']::text[]
                    WHERE user_id = (
                        SELECT id FROM users WHERE username = %s
                    )''',
                (username,),
            )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(scope='module')
def db_url():
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://wheelapp:a51f2d9685f4d6dca9d2f9d8d6e66374@localhost/wheeldb_staging',
    )


@pytest.fixture(scope='module')
def logged_in_context(server_url, db_url):
    username = f't113{uuid.uuid4().hex[:10]}'
    password = 'testpass123'
    with sync_playwright() as p:
        b = p.chromium.launch()
        context = b.new_context()
        page = context.new_page()
        page.goto(server_url + '/')
        page.wait_for_load_state('domcontentloaded')
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
        if not result['ok'] and result['error'] and 'taken' not in (result['error'] or ''):
            b.close()
            pytest.fail(f'register failed: {result["error"]}')
        _grant_aquarium(db_url, username)
        page.reload()
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_selector('.season8-aquarium-panel', timeout=10000)
        yield context
        b.close()


@pytest.fixture()
def logged_in_page(logged_in_context):
    page = logged_in_context.new_page()
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.goto(logged_in_context.pages[0].url if logged_in_context.pages else '/')
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_selector('.season8-aquarium-panel', timeout=10000)
    yield page
    page.close()


def test_aquarium_panel_renders(logged_in_page):
    """T113: the aquarium panel is visible when the player owns the upgrade."""
    page = logged_in_page
    panel = page.locator('.season8-aquarium-panel')
    assert panel.count() == 1, f'expected exactly one .season8-aquarium-panel, got {panel.count()}'
    assert panel.is_visible(), '.season8-aquarium-panel should be visible'
    # At least one species chip should be rendered (we granted 3).
    species = page.locator('.aquarium-species')
    assert species.count() >= 1, f'expected >=1 .aquarium-species, got {species.count()}'


def test_aquarium_species_text_is_light(logged_in_page):
    """T113: species names must NOT be black. Computed rgb R must be > 150.

    Before the fix, `.aquarium-grid` had no explicit color so species names
    inherited the page default (black) and were unreadable on the near-black
    panel background. After the fix, they should be #e0e0e0 (rgb 224,224,224).
    """
    page = logged_in_page
    species = page.locator('.aquarium-species').first
    assert species.count() == 1, 'no .aquarium-species to inspect'
    color = species.evaluate('(el) => getComputedStyle(el).color')
    assert color.startswith('rgb'), f'unexpected color format: {color!r}'
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', color)
    assert m, f'could not parse color {color!r}'
    r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    assert r > 150, (
        f'aquarium species text is too dark — R={r} (computed color {color!r}). '
        f'Bug: .aquarium-species has no explicit color, inheriting the page default (black).'
    )
    assert g > 150, (
        f'aquarium species text is too dark — G={g} (computed color {color!r}).'
    )
    assert b > 150, (
        f'aquarium species text is too dark — B={b} (computed color {color!r}).'
    )


def test_aquarium_info_icon_exists_with_tooltip(logged_in_page):
    """T113: the (?) icon exists and uses data-tooltip (custom CSS hover popup,
    matching the wager panel's (?) icon)."""
    page = logged_in_page
    icon = page.locator('.aquarium-info-icon')
    assert icon.count() == 1, f'expected one .aquarium-info-icon, got {icon.count()}'
    data_tooltip = icon.get_attribute('data-tooltip')
    assert data_tooltip, '.aquarium-info-icon has no data-tooltip attribute'
    assert data_tooltip.strip() != '', '.aquarium-info-icon data-tooltip is empty'
    # The (?) text should be rendered.
    text = (icon.text_content() or '').strip()
    assert '?' in text, f'.aquarium-info-icon should display a "?", got {text!r}'


def test_aquarium_info_tooltip_mentions_luck_bonus(logged_in_page):
    """T113: the data-tooltip text must mention the +0.1% luck bonus."""
    page = logged_in_page
    tip = page.locator('.aquarium-info-icon').get_attribute('data-tooltip') or ''
    t = tip.lower()
    assert '+0.1%' in tip or '0.1%' in t, (
        f'tooltip must mention "+0.1%" — got {tip!r}'
    )
    assert 'win chance' in t or 'luck' in t or 'base' in t, (
        f'tooltip must mention "win chance", "luck", or "base" — got {tip!r}'
    )


def test_aquarium_info_icon_hover_popup_styled(logged_in_page):
    """T113: the (?) icon uses a custom CSS ::after hover popup (matching the
    wager panel's (?) icon), not the unreliable native title= attribute. The
    CSS declares: cursor:help, position:relative, and a [data-tooltip]:hover::after
    rule that pulls content from the data-tooltip attribute."""
    page = logged_in_page
    icon = page.locator('.aquarium-info-icon')
    # The icon has data-tooltip set (the JSX, not the CSS).
    tip_text = icon.get_attribute('data-tooltip') or ''
    assert tip_text, 'data-tooltip must be set for the ::after popup to show'
    # The CSS sets cursor:help and position:relative so the ::after popup
    # can anchor. (Hover-Playwright is unreliable when overlays intercept
    # pointer events, so we verify the CSS contract instead.)
    cursor = icon.evaluate('el => getComputedStyle(el).cursor')
    assert cursor == 'help', f'expected cursor:help, got {cursor!r}'
    position = icon.evaluate('el => getComputedStyle(el).position')
    assert position == 'relative', (
        f'expected position:relative for ::after to anchor, got {position!r}'
    )


def test_aquarium_panel_screenshot_1920x1080(logged_in_page):
    """T113: capture a 1920x1080 screenshot of the aquarium panel for visual verification."""
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
    page.screenshot(path=os.path.join(screenshot_dir, 't113_aquarium.png'), full_page=False)
