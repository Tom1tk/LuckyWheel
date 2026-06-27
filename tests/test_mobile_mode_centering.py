"""T206: mobile mode buttons must be centered inside .season8-wheel-mode.

1 test verifies the operator's feedback from 2026-06-26:
  1. .wheel-mode-btns sits inside .season8-wheel-mode with
     gapLeft ≈ gapRight (within 1px), so the button row is centered
     under the centered label above it.

Pre-T206 the flex row had no justify-content, so the buttons clustered
on the left (gapLeft=0, gapRight=43 on a 390px viewport with
testing7 logged in). The fix is a single CSS rule
(`justify-content: center;`) inside the @media (max-width: 768px)
block at line ~5495.

Run:
    cd /home/user/wt-T206
    timeout 180 python3 -m pytest tests/test_mobile_mode_centering.py -v
    timeout 240 python3 -m pytest tests/ 2>&1 | tail -5

Expected: 1 PASS. Full suite: 432+ pass, 2 skip.
"""
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────

def _login_via_api(page, server_url):
    """Log in as the pre-existing 'testing7' user via the API. Same
    pattern as test_mobile_e2e._api_post: fetch /api/me for the
    csrf_token (httponly cookie, not in document.cookie), then POST
    /api/login with X-CSRFToken header."""
    page.goto(f'{server_url}/')
    result = page.evaluate(
        """async () => {
            const me = await fetch('/api/me');
            const meData = await me.json();
            const csrf = meData.csrf_token;
            const r = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf
                },
                body: JSON.stringify({username: 'testing7', password: 'pw1234'})
            });
            return {ok: r.ok, status: r.status};
        }"""
    )
    assert result['ok'], f'login failed: {result}'


@pytest.fixture
def mobile_page(browser, server_url):
    """Open a 390x844 mobile context, log in as testing7, dismiss the
    patch-notes overlay (so it doesn't shift layout), and wait for
    .season8-wheel-mode to render. Closes the page on teardown."""
    ctx = browser.new_context(viewport={'width': 390, 'height': 844})
    page = ctx.new_page()
    _login_via_api(page, server_url)
    page.goto(f'{server_url}/')
    page.evaluate(
        """() => {
          for (let i = 1; i <= 12; i++) {
            localStorage.setItem('patchNotesSeen_s'+i, '1');
          }
        }"""
    )
    page.reload()
    page.wait_for_selector('.season8-wheel-mode', timeout=10000)
    yield page
    page.close()


# ═══════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════

def test_mode_buttons_centered_on_mobile(mobile_page):
    """T206: .wheel-mode-btns is centered inside .season8-wheel-mode.

    Pre-T206 the .season8-wheel-mode .wheel-mode-btns rule had no
    justify-content, so the flex row defaulted to flex-start and the
    three mode buttons (Steady / Volatile / Long Shot) clustered on
    the left. Measured: gapLeft=0, gapRight=43 on a 390x844 viewport
    with testing7 logged in.

    The fix is a single CSS line:
        justify-content: center;
    inside the @media (max-width: 768px) block. After the fix the
    row should be centered so |gapLeft - gapRight| <= 1px.
    """
    data = mobile_page.evaluate("""() => {
      const wm = document.querySelector('.season8-wheel-mode');
      const btns = wm.querySelector('.wheel-mode-btns');
      const wr = wm.getBoundingClientRect();
      const br = btns.getBoundingClientRect();
      return {
        wm: {x: wr.x, w: wr.width, right: wr.right},
        btns: {x: br.x, w: br.width, right: br.right},
        gapLeft: br.x - wr.x,
        gapRight: wr.right - br.right,
      };
    }""")
    assert abs(data['gapLeft'] - data['gapRight']) <= 1, (
        f'mode buttons not centered: '
        f'gapLeft={data["gapLeft"]:.1f}, gapRight={data["gapRight"]:.1f}'
    )
