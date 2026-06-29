"""Shared pytest fixtures for the mobile / e2e test suite.

T232: extract the duplicated server/db/playwright fixtures from the
~9 test files that boot a Flask server, register users, and drive
the UI with Playwright (`test_aquarium_panel`, `test_arm_button_truncation`,
`test_mobile_drawer_style`, `test_mobile_e2e`, `test_mobile_mode_centering`,
`test_onboarding_disabled`, `test_prestige_tooltip`, `test_season_info_display`,
`test_wager_panel_layout`).

Fixtures:
  - `db_url`              — DATABASE_URL (env, with .env fallback; no hardcoded literal)
  - `server_url`          — boot Flask in a subprocess on a free port
  - `playwright_instance` — module-scoped `sync_playwright()` context
  - `browser`             — function-scoped chromium browser (fresh per test)

The DB-backfill tests (`test_backfill_season8_theme`,
`test_legacy_wins_separation`) have their own `db_url` fixture with extra
safety guards (read from a fixed staging `.env` path, assert the URL
looks like staging) — they are intentionally NOT consolidated here.
T234 will rotate the staging credential and refactor the remaining
literal-bearing helpers across the test files.
"""
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright


# ── T242: pre-load flask_limiter (T242 follow-up) ───────────────────────────
# A few test modules do real `import game` / `import community_goals` /
# `import fish` at module load time. Those cascade through chat.py →
# extensions.py → flask_limiter → flask.{wrappers,ctx,signals,...}.
#
# Pre-T242, sibling test files used `sys.modules.setdefault(<name>, <stub>)`
# at module-load time, and whichever file was collected first won the race
# — so by the time `test_community_goals.py` was collected, `flask` was
# already the stub. T242 moved those into setup_module (post-collection),
# leaving a window where `import community_goals` triggers the real
# chain and fails.
#
# Fix: pre-load flask_limiter and flask_login here so their import
# chains run at conftest import time, NOT during pytest collection.
# If the chains fail here, we surface a clear error rather than
# letting collection fail with a confusing traceback.
try:
    import flask_limiter  # noqa: F401
    import flask_login    # noqa: F401
except ImportError as _exc:
    import sys
    print(
        f'WARNING: tests/conftest.py could not pre-load flask_limiter: {_exc}\n'
        f'Tests that do real `import community_goals` / `import fish` /\n'
        f'`import game` at module load time will fail to collect.',
        file=sys.stderr,
    )


REPO_ROOT = Path(__file__).resolve().parent.parent
_TEST_DOTENV = REPO_ROOT / '.env'


def _free_port() -> int:
    """Bind a TCP socket to port 0 to ask the kernel for a free port,
    then release it. The port is unlikely to be re-claimed before the
    server binds to it (kernel reuses freed ports sparingly)."""
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _resolve_db_url() -> str:
    """Return the DATABASE_URL the test should use.

    Reads from `os.environ` first. If not set, falls back to the
    repo-root `.env` file (via python-dotenv) so the staging `.env`
    is picked up automatically when developers run tests locally.

    Fails with a clear error if `DATABASE_URL` is not set anywhere.
    (T232 removes the hardcoded staging credential as a silent
    fallback; T234 will do the full credential rotation.)

    T246 safety check: if the URL points at the PRODUCTION database
    (i.e. the path component is `/wheeldb`, not `/wheeldb_test` /
    `/wheeldb_staging`), refuse and fail with a clear error. Tests
    must run against `wheeldb_test` (or `wheeldb_staging` for the
    backfill tests, which have their own guard). This is the
    canonical defense against the pytest-suits-writing-to-prod
    problem flagged in §3 of the advisor audit.
    """
    if not os.environ.get('DATABASE_URL') and _TEST_DOTENV.is_file():
        load_dotenv(_TEST_DOTENV, override=False)
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError(
            'DATABASE_URL is not set. Export it in the environment, '
            'or put DATABASE_URL=... in a .env file at the repo root.'
        )
    # Refuse to run tests against the production DB. The path component
    # is the last `/...` segment of the URL.
    dbname = url.rsplit('/', 1)[-1].split('?')[0]
    if dbname == 'wheeldb':
        raise RuntimeError(
            f'Refusing to run tests against the production database '
            f'(DATABASE_URL={url!r}). Use wheeldb_test (run '
            f'`make test-db-reset && make test`) or wheeldb_staging.'
        )
    return url


@pytest.fixture(scope='session')
def db_url() -> str:
    """Session-scoped: the DATABASE_URL the test should use, resolved
    from env (with .env fallback). Fails with a clear error if unset."""
    return _resolve_db_url()


@pytest.fixture(scope='module')
def server_url(db_url: str) -> str:
    """Module-scoped: boot a Flask server on a free port and yield its
    base URL. All tests in a module share one server process (boot is
    ~2s; spinning up a fresh server per test is prohibitively slow).

    The subprocess inherits the test process's environment, with:
      - PORT set to a free local port
      - WHEEL_SECRET_KEY set to a stable test value (Flask needs a
        non-empty key to sign sessions — see `app.py:14-19`)
      - DATABASE_URL set to the resolved `db_url` so the server uses
        the same DB the tests query directly
    """
    port = _free_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['WHEEL_SECRET_KEY'] = 'wheel-test-secret-key-for-playwright-only'
    env['DATABASE_URL'] = db_url
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
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        pytest.fail('Flask server did not start within 20s')
    yield base
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope='module')
def playwright_instance():
    """Module-scoped: one `sync_playwright()` context shared across the
    module's tests. Opening multiple `sync_playwright()` blocks in the
    same pytest run can hit the "Sync API inside asyncio loop" error —
    sharing one context avoids that."""
    with sync_playwright() as p:
        yield p


@pytest.fixture
def browser(playwright_instance):
    """Function-scoped: a fresh chromium browser per test. The
    underlying Playwright instance is shared (`playwright_instance`),
    but the browser is launched per test so contexts/pages do not
    leak between tests."""
    b = playwright_instance.chromium.launch()
    yield b
    b.close()
