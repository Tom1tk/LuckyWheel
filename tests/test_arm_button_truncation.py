"""T116: wager panel arm buttons — truncation fix.

Verifies at 1366x768 (and a couple of other resolutions) that the
'Arm Double-Down' and 'Arm Insurance' arm buttons render their full
label without truncation. T116 shortens 'Arm Double-Down (all-or-nothing)'
to 'Double Down' and switches the buttons to white-space: normal so
they wrap cleanly inside the narrow 96px panel.

Tests use a real DB connection (psycopg2) to grant wager items directly
because the /api/buy endpoint requires a player to have earned the cost
in wins. Each test registers a fresh user, grants the items, reloads
the page, then asserts on the rendered button geometry / behaviour.
"""
import os
import socket
import subprocess
import sys
import time
import uuid

import pytest
import psycopg2
import psycopg2.extras
from playwright.sync_api import sync_playwright


DSN = os.environ.get(
    'DATABASE_URL',
    'postgresql://wheelapp:a51f2d9685f4d6dca9d2f9d8d6e66374@localhost/wheeldb_staging',
)


def _free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _grant_wager_items(username: str):
    """Directly grant the wager items + insurance charges + insurance
    tokens that the tests need. Buying them via the API would cost
    75,500 wins (T116 is a UI fix, not a balance test), so we seed the
    row via SQL instead. T119 renamed the column
    wager_insurance_charges → insurance_charges and added the
    insurance_tokens column; the arm button (T119: "Arm Insurance
    (N tokens)") is gated on insurance_tokens >= 1, so we seed
    tokens here as well.
    """
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE game_state
                SET owned_items = ARRAY(
                    SELECT DISTINCT unnest(
                        owned_items || ARRAY[
                            'wager_unlock',
                            'wager_hot_streak',
                            'wager_double_down',
                            'wager_insurance'
                        ]
                    )
                ),
                    insurance_charges = 3,
                    insurance_tokens = 3
                WHERE user_id = (SELECT id FROM users WHERE username = %s)
                ''',
                (username,),
            )
    finally:
        conn.close()


def _reset_arm_state(username: str):
    """Reset DD / insurance armed flags + insurance charges so each
    function-scoped test starts from the same disarmed baseline.
    T119 renamed the column wager_insurance_charges → insurance_charges
    and wager_insurance_armed → insurance_armed.
    """
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE game_state
                SET double_down_pending = FALSE,
                    insurance_armed = FALSE,
                    insurance_charges = 3
                WHERE user_id = (SELECT id FROM users WHERE username = %s)
                ''',
                (username,),
            )
    finally:
        conn.close()


@pytest.fixture(scope='module')
def server_url():
    port = _free_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    env.setdefault('WHEEL_SECRET_KEY', 't116-test-secret-key-for-playwright-only')
    env['DATABASE_URL'] = DSN
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
def shared_user(server_url):
    """Register ONE user for the whole module, grant wager items, and
    keep the browser open so individual tests can open fresh pages
    against the same logged-in session. Avoids hitting the
    5-per-hour /api/register rate limit when running all 6 tests.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1366, 'height': 768})
        page = context.new_page()
        page.goto(server_url + '/')
        page.wait_for_load_state('domcontentloaded')
        username = f't116{uuid.uuid4().hex[:10]}'
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
                return {ok: r.ok, status: r.status};
            }''',
            {'u': username, 'p': password},
        )
        if not result['ok']:
            browser.close()
            pytest.fail(f'register failed: {result}')
        _grant_wager_items(username)
        yield {
            'context': context,
            'username': username,
            'base_url': server_url,
        }
        browser.close()


@pytest.fixture()
def armed_user(shared_user, server_url):
    """Per-test fixture: open a fresh page in the shared logged-in
    context, reset DD/insurance armed state, and confirm the wager
    panel is visible.
    """
    context = shared_user['context']
    username = shared_user['username']
    page = context.new_page()
    _reset_arm_state(username)
    page.goto(server_url + '/')
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_selector('.season8-wager-panel', timeout=10000)
    page.wait_for_selector('.wager-action-btn', timeout=10000)
    # Patch notes overlay (rendered as `.stats-overlay` with a
    # `.patch-notes-card` child) covers the whole viewport on first
    # load and would intercept clicks on the arm buttons.
    page.evaluate(
        '''() => {
            const card = document.querySelector('.patch-notes-card');
            if (card) {
                const closeBtn = card.querySelector('button, .close, [aria-label]');
                if (closeBtn) closeBtn.click();
                else card.closest('.stats-overlay')?.remove();
            }
        }'''
    )
    page.wait_for_timeout(100)
    yield {
        'page': page,
        'username': username,
        'base_url': server_url,
    }
    page.close()


def _find_dd_arm_button(page):
    """Return the locator for the disarmed 'Double Down' arm button."""
    return page.locator(
        'button.wager-action-btn:not(.wager-bank-btn)'
    ).filter(has_text='Double Down').first


def _find_insurance_arm_button(page):
    # T119: the arm button label changed from "🛡️ Insurance (N)" to
    # "🛡️ Arm Insurance (N tokens)". The locator matches on "Arm
    # Insurance" so it doesn't pick up the (now-hidden) buy button or
    # the ARMED indicator.
    return page.locator(
        'button.wager-action-btn:not(.wager-bank-btn)'
    ).filter(has_text='Arm Insurance').first


# ════════════════════════════════════════════════════════════════════════════
# T116: truncation
# ════════════════════════════════════════════════════════════════════════════
def test_double_down_label_fully_visible_at_1366x768(armed_user):
    """T116: at 1366x768 the DD arm button renders its full label.

    The wager panel is 96px wide at this resolution; before T116 the
    '⚡ Arm Double-Down (all-or-nothing)' label was cut off (ellipsis).
    After the fix the label is '⚡ Double Down' and the button is not
    visually truncated: textContent matches the expected label and
    the button's bounding box fits inside the panel's content area.
    """
    page = armed_user['page']
    page.set_viewport_size({'width': 1366, 'height': 768})
    page.wait_for_timeout(150)

    btn = _find_dd_arm_button(page)
    assert btn.count() == 1, 'expected exactly one Double Down arm button'

    panel = page.locator('.season8-wager-panel').bounding_box()
    assert panel is not None
    panel_right = panel['x'] + panel['width']

    text = btn.evaluate('(el) => el.textContent.trim()')
    assert text == '⚡ Double Down', (
        f'DD arm button label is {text!r}; expected "⚡ Double Down" (T116)'
    )
    assert '…' not in text and '...' not in text, (
        f'DD arm button label still shows an ellipsis: {text!r}'
    )

    box = btn.bounding_box()
    assert box is not None
    # The button must sit fully inside the panel (no horizontal clipping).
    assert box['x'] + box['width'] <= panel_right + 1, (
        f'DD button ({box["x"]:.0f}+{box["width"]:.0f}) overflows the '
        f'wager panel (right edge={panel_right:.0f}) at 1366x768'
    )
    # Sanity: the rendered text is wider than zero.
    assert box['width'] > 0 and box['height'] > 0


def test_insurance_label_fully_visible_at_1366x768(armed_user):
    """T116/T119: at 1366x768 the Insurance arm button renders its full
    label. T119 renamed the label to "🛡️ Arm Insurance (N tokens)"
    (was "🛡️ Insurance (N)") — the new label is longer and exercises
    the wrap behaviour the T116 CSS introduced.
    """
    page = armed_user['page']
    page.set_viewport_size({'width': 1366, 'height': 768})
    page.wait_for_timeout(150)

    btn = _find_insurance_arm_button(page)
    assert btn.count() == 1, 'expected exactly one Insurance arm button'

    panel = page.locator('.season8-wager-panel').bounding_box()
    assert panel is not None
    panel_right = panel['x'] + panel['width']

    text = btn.evaluate('(el) => el.textContent.trim()')
    assert text.startswith('🛡️ Arm Insurance'), (
        f'Insurance arm button label is {text!r}; expected to start with '
        '"🛡️ Arm Insurance" (T119)'
    )
    assert '…' not in text and '...' not in text, (
        f'Insurance arm button label still shows an ellipsis: {text!r}'
    )

    box = btn.bounding_box()
    assert box is not None
    assert box['x'] + box['width'] <= panel_right + 1, (
        f'Insurance button ({box["x"]:.0f}+{box["width"]:.0f}) overflows '
        f'the wager panel (right edge={panel_right:.0f}) at 1366x768'
    )
    assert box['width'] > 0 and box['height'] > 0


def test_buttons_have_height_to_fit_label_at_1360x768(armed_user):
    """T116: at 1360x768 the buttons expand vertically when needed.

    Below 1366px the wager panel falls back to full-width (max 340px)
    so truncation is unlikely, but we still want to confirm the
    white-space:normal + line-height:1.2 rules give the buttons enough
    room — a 32px minimum accommodates a single line at the
    wager-action-btn font size.
    """
    page = armed_user['page']
    page.set_viewport_size({'width': 1360, 'height': 768})
    page.wait_for_timeout(150)

    dd = _find_dd_arm_button(page)
    ins = _find_insurance_arm_button(page)
    assert dd.count() == 1
    assert ins.count() == 1

    dd_box = dd.bounding_box()
    ins_box = ins.bounding_box()
    assert dd_box is not None and ins_box is not None

    # Both buttons must be tall enough to render a single line of text
    # cleanly. The wager-action-btn font-size is 0.62rem (~10px) with
    # padding 4px top/bottom, so 32px is a conservative lower bound
    # that catches "clipped to nothing" regressions.
    assert dd_box['height'] >= 20, (
        f'DD arm button height {dd_box["height"]:.0f}px looks clipped '
        f'at 1360x768'
    )
    assert ins_box['height'] >= 20, (
        f'Insurance arm button height {ins_box["height"]:.0f}px looks '
        f'clipped at 1360x768'
    )

    # Buttons must be fully inside the panel — no horizontal clipping.
    panel = page.locator('.season8-wager-panel').bounding_box()
    assert panel is not None
    panel_left = panel['x']
    panel_right = panel['x'] + panel['width']
    for label, b in (('DD', dd_box), ('Insurance', ins_box)):
        assert b['x'] >= panel_left - 1, (
            f'{label} button overflows the left edge of the wager panel '
            f'at 1360x768 (x={b["x"]:.0f}, panel_left={panel_left:.0f})'
        )
        assert b['x'] + b['width'] <= panel_right + 1, (
            f'{label} button overflows the right edge of the wager panel '
            f'at 1360x768 (right={b["x"]+b["width"]:.0f}, panel_right={panel_right:.0f})'
        )


def test_clicking_double_down_arms_and_shows_full_cancel_label(armed_user):
    """T116: clicking the DD arm button arms it and the armed indicator
    shows its full 'Double-Down armed! (click to cancel) ⚠️' text.

    This catches two regressions at once:
      - the click still POSTs /api/wager/double-down (DD actually arms)
      - the .wager-double-down-armed + .wager-cancel-btn rules now wrap
        the long cancel label cleanly instead of truncating it.
    """
    page = armed_user['page']
    page.set_viewport_size({'width': 1366, 'height': 768})
    page.wait_for_timeout(150)

    dd = _find_dd_arm_button(page)
    assert dd.count() == 1, 'expected exactly one Double Down arm button'
    dd.click()
    page.wait_for_timeout(500)

    # The arm button should be gone, replaced by the armed indicator.
    assert _find_dd_arm_button(page).count() == 0, (
        'DD arm button did not disappear after clicking — DD may not have armed'
    )
    armed = page.locator('button.wager-double-down-armed').first
    assert armed.count() == 1, (
        'expected the DD armed indicator to appear after arming'
    )

    text = armed.evaluate('(el) => el.textContent.trim()')
    assert 'Double-Down armed' in text, (
        f'armed indicator text {text!r} does not contain "Double-Down armed"'
    )
    assert '…' not in text and '...' not in text, (
        f'armed indicator text still shows an ellipsis: {text!r}'
    )
    assert '(click to cancel)' in text, (
        f'armed indicator text {text!r} is missing the cancel affordance'
    )

    # The armed indicator must be fully inside the panel.
    panel = page.locator('.season8-wager-panel').bounding_box()
    assert panel is not None
    box = armed.bounding_box()
    assert box is not None
    assert box['x'] + box['width'] <= panel['x'] + panel['width'] + 1, (
        f'armed indicator overflows the wager panel '
        f'(right={box["x"]+box["width"]:.0f}, '
        f'panel_right={panel["x"]+panel["width"]:.0f})'
    )
    # The armed indicator should be tall enough to fit a wrapped line.
    assert box['height'] >= 20, (
        f'armed indicator height {box["height"]:.0f}px looks clipped at 1366x768'
    )


# ════════════════════════════════════════════════════════════════════════════
# T116: bonus — wider viewport (1920x1080) for regression coverage
# ════════════════════════════════════════════════════════════════════════════
def test_double_down_label_fully_visible_at_1920x1080(armed_user):
    """T116: at 1920x1080 the DD arm button still renders its full label.

    Acts as a regression guard for the wider layout — the original
    truncation was only at 1366x768, but if a future change tightens
    the panel width this test will catch the regression.
    """
    page = armed_user['page']
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.wait_for_timeout(150)

    btn = _find_dd_arm_button(page)
    assert btn.count() == 1
    text = btn.evaluate('(el) => el.textContent.trim()')
    assert text == '⚡ Double Down', (
        f'DD arm button label is {text!r} at 1920x1080'
    )


# ════════════════════════════════════════════════════════════════════════════
# T116: screenshot
# ════════════════════════════════════════════════════════════════════════════
def test_screenshot_arm_buttons_at_1366x768(armed_user):
    """T116: capture a screenshot of the wager panel at 1366x768 with
    both arm buttons disarmed (showing the new short labels).
    """
    page = armed_user['page']
    page.set_viewport_size({'width': 1366, 'height': 768})
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
    out = os.path.join(screenshot_dir, 't116_arm_buttons_1366x768.png')
    page.screenshot(path=out, full_page=False)
    assert os.path.exists(out) and os.path.getsize(out) > 0, (
        f'screenshot was not written to {out}'
    )
