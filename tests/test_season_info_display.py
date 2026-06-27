"""T212: top-right Season widget shows the player-facing season number.

Operator's verbatim report (2026-06-27):
"The top right says season casino, this needs to say season 8."

Three layers of coverage:
  1. Source-string assertions against `static/app.jsx` and
     `migrations/055_seasons_player_facing_number.sql` — the cheapest
     checks; catch accidental removal of the new column / prop.
  2. Direct API test against `/api/season` — confirms the new
     `player_facing_number` key is present in the JSON response (its
     value depends on the staging DB's current season row).
  3. Playwright UI test against the live page — confirms the
     `.season-info` widget renders the player-facing number "8" (not
     "Casino" / "9") when the season row is set to the S8 (Casino)
     state. Also confirms the countdown timer is still ticking.

The staging DB's season row is updated to the S8 (Casino) state for
the duration of the module and restored at teardown so other test
files sharing the same database see their original state.
"""
import importlib.util
import inspect
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

import psycopg2
import pytest
from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent
APP_JSX = REPO_ROOT / 'static' / 'app.jsx'
APP_JS = REPO_ROOT / 'static' / 'app.js'
MIGRATION_055 = REPO_ROOT / 'migrations' / '055_seasons_player_facing_number.sql'

DSN = os.environ.get(
    'DATABASE_URL',
    'postgresql://wheelapp:a51f2d9685f4d6dca9d2f9d8d6e66374@localhost/wheeldb_staging',
)


# ── Source-string assertions (no server, no DB) ──────────────────────────────


def test_migration_055_file_exists():
    """T212: migration 055 adds the player_facing_number column."""
    assert MIGRATION_055.exists(), (
        f'{MIGRATION_055} is missing — T212 must add the player-facing '
        f'number column via a new migration.'
    )


def test_migration_055_adds_player_facing_number_column():
    """T212: migration 055 must ALTER TABLE seasons to add the new column
    and UPDATE the S8 (Casino) row to 8. Both statements must be
    idempotent so re-running the migration is safe."""
    sql = MIGRATION_055.read_text(encoding='utf-8')
    assert re.search(
        r'ALTER\s+TABLE\s+seasons\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+player_facing_number\s+INTEGER',
        sql, re.IGNORECASE,
    ), (
        f'migration 055 must ALTER TABLE seasons ADD COLUMN IF NOT EXISTS '
        f'player_facing_number INTEGER — got:\n{sql}'
    )
    assert "name = 'Casino'" in sql, (
        f'migration 055 must UPDATE the Casino row specifically — got:\n{sql}'
    )
    assert re.search(r'UPDATE\s+seasons\s+SET\s+player_facing_number\s*=\s*8', sql, re.IGNORECASE), (
        f'migration 055 must set player_facing_number = 8 for the Casino row — got:\n{sql}'
    )


def test_season_info_component_accepts_player_facing_number_prop():
    """T212: the SeasonInfo component (static/app.jsx) must accept a
    `playerFacingNumber` prop in its destructured signature."""
    src = APP_JSX.read_text(encoding='utf-8')
    assert re.search(
        r'function\s+SeasonInfo\s*\(\s*\{\s*seasonName\s*,\s*playerFacingNumber\s*,\s*endsAt\s*\}\s*\)',
        src,
    ), (
        'SeasonInfo must destructure { seasonName, playerFacingNumber, endsAt } '
        'so the new prop is wired up.'
    )


def test_season_info_prefers_player_facing_number_over_season_name():
    """T212: the component must display playerFacingNumber when present
    (the new field) and fall back to seasonName otherwise (legacy rows
    with player_facing_number = NULL)."""
    src = APP_JSX.read_text(encoding='utf-8')
    # Look for the conditional: prefer playerFacingNumber when not null.
    m = re.search(
        r'displayNumber\s*=\s*playerFacingNumber\s*!=\s*null\s*\?\s*playerFacingNumber\s*:\s*seasonName',
        src,
    )
    assert m, (
        'SeasonInfo must prefer playerFacingNumber over seasonName via a '
        '`displayNumber = playerFacingNumber != null ? ... : seasonName` '
        'ternary. The current SeasonInfo still prefers season_name.'
    )


def test_call_site_passes_player_facing_number():
    """T212: the <SeasonInfo ... /> call site must pass
    `playerFacingNumber={season.player_facing_number}` so the new
    prop is fed from the API response."""
    src = APP_JSX.read_text(encoding='utf-8')
    assert 'playerFacingNumber={season.player_facing_number}' in src, (
        'the <SeasonInfo ... /> call site must pass '
        'playerFacingNumber={season.player_facing_number} from the API '
        'response. The current call still only passes seasonName + endsAt.'
    )


def test_season_info_span_renders_display_number():
    """T212: the rendered <span> must interpolate the (possibly new)
    displayNumber, not the raw seasonName. Regression: the old code
    was `<span>Season {seasonName} ends:</span>`."""
    src = APP_JSX.read_text(encoding='utf-8')
    assert '<span>Season {displayNumber} ends:</span>' in src, (
        'SeasonInfo must render <span>Season {displayNumber} ends:</span> '
        'so the player-facing number is shown.'
    )
    assert '<span>Season {seasonName} ends:</span>' not in src, (
        'the old <span>Season {seasonName} ends:</span> markup must be '
        'replaced — it shows "Season Casino" instead of "Season 8".'
    )


def test_transpiled_app_js_contains_player_facing_number_call():
    """T212: the transpiled app.js must contain the call-site
    `playerFacingNumber: season.player_facing_number` so the browser
    bundle ships the new wiring. (Catches forgetting to run `make
    build` after editing app.jsx.)"""
    assert APP_JS.exists(), f'{APP_JS} is missing — run `make build`'
    js_src = APP_JS.read_text(encoding='utf-8')
    assert 'playerFacingNumber: season.player_facing_number' in js_src, (
        'transpiled static/app.js is missing '
        '`playerFacingNumber: season.player_facing_number` — the babel '
        'build did not pick up the JSX change. Run `make build`.'
    )


# ── seasons.py source assertions ────────────────────────────────────────────


def _load_seasons_module():
    """Load the real seasons.py via importlib so we can inspect its
    source / symbols (mirrors the pattern in test_rollover.py)."""
    spec = importlib.util.spec_from_file_location(
        '_real_seasons_for_t212', REPO_ROOT / 'seasons.py',
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_get_season_info_returns_player_facing_number():
    """T212: get_season_info must SELECT and return player_facing_number
    so the /api/season endpoint surfaces the new field."""
    src = inspect.getsource(_load_seasons_module().get_season_info)
    assert 'player_facing_number' in src, (
        'seasons.get_season_info must include player_facing_number in '
        'the SELECT and the returned dict.'
    )


def test_advance_season_writes_player_facing_number():
    """T212: advance_season must UPDATE the new row's
    player_facing_number so the next rollover preserves the field."""
    src = inspect.getsource(_load_seasons_module().advance_season)
    # The UPDATE seasons SET ... clause must reference player_facing_number.
    assert re.search(
        r"UPDATE\s+seasons[\s\S]{0,400}player_facing_number\s*=\s*%s",
        src, re.IGNORECASE,
    ), (
        'advance_season must UPDATE seasons SET player_facing_number = %s '
        'so future rollovers preserve the new field.'
    )


# ── Live API + Playwright tests (need a running server) ─────────────────────


def _free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _http_get_json(url, timeout=5):
    req = urllib.request.Request(url, method='GET')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode('utf-8'))


@pytest.fixture(scope='module')
def server_url():
    port = _free_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    env.setdefault('WHEEL_SECRET_KEY', 't212-test-secret-key-for-playwright-only')
    env['DATABASE_URL'] = DSN
    proc = subprocess.Popen(
        [sys.executable, 'server.py'],
        cwd=str(REPO_ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f'http://127.0.0.1:{port}'
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
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
def season_s8_state():
    """Save the staging DB's current season row, set it to the S8
    (Casino) state with player_facing_number=8, yield, then restore.
    The seasons table is a single-row table, so all tests in this
    module share the modified state for the duration of the run.
    Other test files using the same staging DB see the original state
    again at teardown."""
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        'SELECT id, season_number, name, player_facing_number, '
        'started_at, ends_at FROM seasons ORDER BY id LIMIT 1'
    )
    original = cur.fetchone()
    assert original is not None, (
        'staging DB has no seasons row — cannot run the T212 UI test '
        '(it requires a row to flip to the S8 / Casino state).'
    )

    # S8 / Casino state: name='Casino', player_facing_number=8, ends in 7d.
    cur.execute(
        'UPDATE seasons SET name = %s, player_facing_number = %s, '
        'ends_at = NOW() + INTERVAL \'7 days\' WHERE id = %s',
        ('Casino', 8, original[0]),
    )
    yield {'id': original[0], 'season_number': original[1]}

    # Restore the original row state — name / pfn / ends_at go back
    # to whatever the staging DB had before this module ran.
    cur.execute(
        'UPDATE seasons SET name = %s, player_facing_number = %s, '
        'ends_at = %s WHERE id = %s',
        (original[2], original[3], original[5], original[0]),
    )
    conn.close()


@pytest.fixture(scope='module')
def logged_in_context(server_url, season_s8_state):
    """Register one user for the whole module. The S8 (Casino) state
    is set by the `season_s8_state` fixture above."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1366, 'height': 768})
        page = context.new_page()
        page.goto(server_url + '/')
        page.wait_for_load_state('domcontentloaded')
        username = f't212{uuid.uuid4().hex[:10]}'
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
        yield {
            'context': context,
            'username': username,
            'base_url': server_url,
        }
        browser.close()


@pytest.fixture()
def logged_in_page(logged_in_context):
    """Per-test page in the shared logged-in context. The page reload
    triggers the /api/season fetch that backs the SeasonInfo widget."""
    page = logged_in_context['context'].new_page()
    page.set_viewport_size({'width': 1366, 'height': 768})
    page.goto(logged_in_context['base_url'] + '/')
    page.wait_for_load_state('domcontentloaded')
    # Patch-notes overlay is rendered on first load; the .season-info
    # widget is part of the user-bar in the same viewport but the
    # overlay's backdrop has high z-index — we wait for the widget
    # explicitly, not just for the overlay to be dismissed, so the
    # test works whether or not the operator has configured a
    # default-open patch notes overlay.
    page.wait_for_selector('.season-info', timeout=10000, state='attached')
    yield page
    page.close()


# ── API tests ──────────────────────────────────────────────────────────────


def test_api_returns_player_facing_number(server_url, season_s8_state):
    """T212: GET /api/season must include the new
    `player_facing_number` key in the JSON response. The Casino row
    is set by the fixture so the value should be 8."""
    status, body = _http_get_json(server_url + '/api/season')
    assert status == 200, f'/api/season returned HTTP {status}'
    assert 'player_facing_number' in body, (
        f'/api/season response is missing the player_facing_number key — '
        f'response body: {body}'
    )
    assert body['player_facing_number'] == 8, (
        f'/api/season returned player_facing_number={body["player_facing_number"]!r}, '
        f'expected 8 for the S8 (Casino) row.'
    )
    # The other fields should still be present (regression — the new
    # field must not displace season_number / season_name / ends_at).
    for key in ('season_number', 'season_name', 'ends_at', 'latest_winners'):
        assert key in body, f'/api/season response is missing {key}'


# ── Playwright UI tests ─────────────────────────────────────────────────────


def test_season_info_shows_player_facing_number(logged_in_page):
    """T212 (Playwright): the top-right `.season-info` widget must
    contain the digit "8" for the S8 (Casino) row — not the literal
    text "Casino" or the DB row id "9". The operator reported the
    wrong text on 2026-06-27."""
    el = logged_in_page.locator('.season-info').first
    el.wait_for(state='visible', timeout=5000)
    text = (el.text_content() or '').strip()
    assert '8' in text, (
        f'.season-info text {text!r} does not contain the digit "8" — '
        f'the widget is still showing the wrong label (the operator '
        f'flagged this on 2026-06-27).'
    )
    # The legacy "Season Casino" string must NOT be the primary label
    # (the digit is the primary; the name may be elsewhere).
    assert 'Casino' not in text, (
        f'.season-info text {text!r} still contains "Casino" as a primary '
        f'label — the player-facing number "8" should be primary, with '
        f'"Casino" at most as a tooltip or subtitle.'
    )


def test_season_info_countdown_still_works(logged_in_page):
    """T212 (regression): the "ends in Xd Yh Zm" countdown must keep
    ticking after the SeasonInfo refactor. The countdown is in
    `.season-countdown` (sibling of the static "Season N ends:" span)."""
    countdown = logged_in_page.locator('.season-info .season-countdown').first
    countdown.wait_for(state='visible', timeout=5000)
    text = (countdown.text_content() or '').strip()
    assert text, '.season-countdown is empty — the countdown is not rendering'
    # The countdown format is "{d}d {h}h {m}m" / "{h}h {m}m" / "{m}m" /
    # "Ending...". Anything non-empty means the useEffect timer ran.
    assert re.match(r'^(\d+d \d+h \d+m|\d+h \d+m|\d+m|Ending\.\.\.)$', text), (
        f'.season-countdown text {text!r} is not in the expected format '
        f'(regression — countdown logic may be broken by the T212 refactor).'
    )
