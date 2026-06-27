"""T205: S8 drawer must match shop style and not cover toolbar.

4 tests verify the operator's feedback from 2026-06-26:
  1. drawer bottom <= toolbar top (drawer sits above the toolbar)
  2. drawer z-index <= 150 (matches shop), not 10000
  3. no .mobile-drawer-close button (open/close via 🎒 toolbar only)
  4. no .mobile-drawer-header (the "📋 S8 Menu" title is gone)

Run:
    cd /home/user/wt-T205
    timeout 180 python3 -m pytest tests/test_mobile_drawer_style.py -v
    timeout 240 python3 -m pytest tests/ 2>&1 | tail -5

Expected: 4 PASS. Full suite: 432+ pass, 1 skip.
"""
# ── Helpers ───────────────────────────────────────────────────────────────

def _login_via_api(page, server_url):
    """Log in as the pre-existing 'testing7' user via the API. Faster
    and more reliable than driving the login UI.

    The session cookie is httponly, so we can't read the csrf_token
    from document.cookie. Instead, fetch /api/me (which returns the
    csrf_token in its JSON body) and use that value in the
    X-CSRFToken header. Same pattern as test_mobile_e2e._api_post.
    """
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


def _open_mobile_page(browser, server_url, w=390, h=844):
    """Open a fresh mobile context, log in as testing7, navigate to /,
    and dismiss the patch-notes overlay. Returns the page object."""
    ctx = browser.new_context(viewport={'width': w, 'height': h})
    page = ctx.new_page()
    _login_via_api(page, server_url)
    page.goto(f'{server_url}/')
    # Mark every season's patch notes as seen so the stats-overlay
    # doesn't cover the mobile-toolbar. Reload so React picks up the
    # flag and skips showing the overlay.
    page.evaluate(
        """() => {
          for (let i = 1; i <= 12; i++) {
            localStorage.setItem('patchNotesSeen_s'+i, '1');
          }
        }"""
    )
    page.reload()
    page.wait_for_selector('.mobile-toolbar', timeout=10000)
    return page


def _open_drawer(page):
    """Click the 🎒 toolbar button and wait for the drawer to slide in."""
    page.locator('.mobile-toolbar-btn[title="Drawer"]').click()
    page.wait_for_selector('.mobile-drawer.mobile-drawer-open', timeout=5000)
    page.wait_for_timeout(300)


# ═══════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════

def test_s8_drawer_does_not_cover_toolbar(browser, server_url):
    """T205: drawer bottom must be <= toolbar top. The drawer must sit
    above the mobile toolbar, not cover it. Pre-T205 the drawer's
    bottom: 0 made it stretch over the toolbar (y=788-844)."""
    page = _open_mobile_page(browser, server_url)
    try:
        _open_drawer(page)
        r = page.evaluate("""() => {
          const dr = document.querySelector('.mobile-drawer');
          const tb = document.querySelector('.mobile-toolbar');
          return {
            drawerBottom: dr.getBoundingClientRect().bottom,
            drawerTop: dr.getBoundingClientRect().top,
            toolbarTop: tb.getBoundingClientRect().top,
          };
        }""")
        assert r['drawerBottom'] <= r['toolbarTop'] + 1, (
            f'drawer covers toolbar: drawer.bottom={r["drawerBottom"]:.1f} '
            f'> toolbar.top={r["toolbarTop"]:.1f}'
        )
    finally:
        page.close()


def test_s8_drawer_z_index_matches_shop(browser, server_url):
    """T205: drawer z-index <= 150 (matches the shop panel). Pre-T205
    the drawer had z-index: 10000, which made it float above every
    other UI element including the mobile toolbar."""
    page = _open_mobile_page(browser, server_url)
    try:
        _open_drawer(page)
        z = page.evaluate(
            "() => parseInt(getComputedStyle(document.querySelector('.mobile-drawer')).zIndex)"
        )
        assert z <= 150, f'drawer z-index too high: {z} (expected <= 150)'
    finally:
        page.close()


def test_s8_drawer_no_close_button(browser, server_url):
    """T205: the .mobile-drawer-close ✕ button is dropped. Open/close
    is via the 🎒 toolbar icon only — toggling on the same button the
    user opened it with."""
    page = _open_mobile_page(browser, server_url)
    try:
        _open_drawer(page)
        n = page.evaluate(
            "() => document.querySelectorAll('.mobile-drawer-close').length"
        )
        assert n == 0, f'expected 0 close buttons, got {n}'
    finally:
        page.close()


def test_s8_drawer_no_header(browser, server_url):
    """T205: the .mobile-drawer-header "📋 S8 Menu" title is dropped.
    The operator wants the drawer to look like a continuation of the
    page (no banner, no chrome — just the panels)."""
    page = _open_mobile_page(browser, server_url)
    try:
        _open_drawer(page)
        n = page.evaluate(
            "() => document.querySelectorAll('.mobile-drawer-header').length"
        )
        assert n == 0, f'expected 0 headers, got {n}'
    finally:
        page.close()
