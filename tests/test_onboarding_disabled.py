"""T114: Onboarding modal must never appear, regardless of onboarding_step.

AC:
1. After login, no `.onboarding-overlay` element is visible (or does not exist).
2. `showOnboarding` is `false` regardless of the persisted `onboarding_step` value
   (we directly mutate the DB to set `onboarding_step = 2` and confirm the
   modal is still hidden — this is the value that would previously have shown
   the coach-mark for "Try setting a wager stake!").
3. No onboarding step text appears anywhere on the page (no `.coach-mark`,
   none of the step-specific copy strings).

The backend's `onboarding_step` is preserved untouched — only the
frontend `useState(false)` gate is changed. Other modals that share the
`onboarding-overlay` CSS class (prestige confirmation, legacy boards)
are gated on their own state and still render when opened.
"""
import os
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


def _db_dsn():
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://wheelapp:a51f2d9685f4d6dca9d2f9d8d6e66374@localhost/wheeldb_staging',
    )


def _register(page, base_url, username, password):
    return page.evaluate(
        '''async ({u, p, base}) => {
            const me = await fetch(base + '/api/me');
            const meData = await me.json();
            const csrf = meData.csrf_token;
            const r = await fetch(base + '/api/register', {
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
        {'u': username, 'p': password, 'base': base_url},
    )


def _user_id_for(username):
    conn = psycopg2.connect(_db_dsn())
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def _set_onboarding_step(user_id, step):
    conn = psycopg2.connect(_db_dsn())
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE game_state SET onboarding_step = %s WHERE user_id = %s',
                (step, user_id),
            )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(scope='module')
def server_url():
    port = _free_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    env.setdefault('WHEEL_SECRET_KEY', 't114-test-secret-key-for-playwright-only')
    env.setdefault('DATABASE_URL', _db_dsn())
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


@pytest.fixture()
def fresh_page(server_url):
    """Yield a fresh browser page logged in as a brand-new user with
    onboarding_step = 0 (the default). Each test gets its own user so
    there's no shared state to leak between tests."""
    username = f't114{uuid.uuid4().hex[:10]}'
    password = 'testpass123'
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context()
        page = ctx.new_page()
        page.goto(server_url + '/')
        page.wait_for_load_state('domcontentloaded')
        result = _register(page, server_url, username, password)
        if not result['ok'] and result['error'] and 'taken' not in (result['error'] or ''):
            b.close()
            pytest.fail(f'register failed: {result["error"]}')
        page.reload()
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_selector('.season8-wager-panel', timeout=10000)
        yield {'page': page, 'username': username, 'base_url': server_url}
        b.close()


def test_onboarding_overlay_not_visible_after_login(fresh_page):
    """AC #1: no `.onboarding-overlay` element is visible (or does not exist)
    after a fresh login. We accept "not present" because the prestige/legacy
    boards modals — which DO use `.onboarding-overlay` — are closed by default
    and have their own state, so the class should not appear at all on
    the landing page."""
    page = fresh_page['page']
    overlays = page.locator('.onboarding-overlay')
    count = overlays.count()
    assert count == 0, (
        f"expected no .onboarding-overlay elements on the landing page, "
        f"found {count}"
    )
    for i in range(count):
        assert not overlays.nth(i).is_visible(), (
            f".onboarding-overlay[{i}] is visible on the landing page — "
            f"the onboarding modal (or a sibling modal) is leaking through"
        )


def test_onboarding_overlay_still_hidden_when_step_is_2(fresh_page):
    """AC #2: even with `onboarding_step = 2` (the value that previously
    showed the 'Try setting a wager stake!' coach-mark), the modal must
    stay hidden. We directly UPDATE the game_state row to simulate a
    player who has partially completed onboarding in a previous session."""
    page = fresh_page['page']
    username = fresh_page['username']
    uid = _user_id_for(username)
    assert uid is not None, f'no users row for {username}'
    _set_onboarding_step(uid, 2)
    page.reload()
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_selector('.season8-wager-panel', timeout=10000)
    page.wait_for_timeout(300)

    assert page.locator('.onboarding-overlay').count() == 0, (
        ".onboarding-overlay appeared after setting onboarding_step=2"
    )
    assert page.locator('.coach-mark').count() == 0, (
        ".coach-mark appeared after setting onboarding_step=2 — the "
        "T114 hardcode showOnboarding=false in the initial state failed"
    )


def test_onboarding_step_text_not_anywhere_on_page(fresh_page):
    """AC #3: the onboarding step display (the `.coach-mark` with its
    step-specific copy) must not appear anywhere on the page."""
    page = fresh_page['page']
    ONBOARDING_COPY = [
        'Spin the wheel to get started',
        'Try setting a wager stake',
        'Catch a fish',
        'Check your bounties',
    ]
    body_text = page.locator('body').inner_text()
    for snippet in ONBOARDING_COPY:
        assert snippet not in body_text, (
            f'onboarding copy {snippet!r} appeared on the page — the '
            f'coach-mark is rendering for an unstarted onboarding flow'
        )
    assert page.locator('.coach-mark').count() == 0, (
        '.coach-mark element rendered despite showOnboarding=false'
    )
    assert page.locator('.coach-mark-text').count() == 0, (
        '.coach-mark-text element rendered despite showOnboarding=false'
    )
