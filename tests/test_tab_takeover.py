"""RV-11: a second tab gets the "Play here" banner on 423 and can take the lock over.

Also pins the bite-poll limit: the client polls at 4/s, so the limit must sit above it.
"""
import inspect
import uuid

from tests.test_mobile_e2e import _api_post, _dismiss_patch_notes_init

PASSWORD = 'testpass123'


def test_bite_poll_limit_is_above_client_poll_rate():
    import game
    assert "@limiter.limit('8 per second')\ndef bite_poll" in inspect.getsource(game)


def _new_context(browser):
    context = browser.new_context()
    context.add_init_script(_dismiss_patch_notes_init())
    context.add_init_script("localStorage.setItem('whatsNewSeen_s9_charts', '1')")
    return context


def test_second_tab_can_take_over(server_url, playwright_instance):
    username = f'rv11{uuid.uuid4().hex[:8]}'
    browser = playwright_instance.chromium.launch()
    try:
        # Tab A registers and spins, so it holds the lock for 30 s.
        context = _new_context(browser)
        page_a = context.new_page()
        page_a.goto(server_url + '/')
        assert _api_post(page_a, '/api/register', {'username': username, 'password': PASSWORD})['ok']
        assert _api_post(page_a, '/api/spin', {'tab_id': 'tab-a'})['ok']

        # Tab B, same browser session (logging in elsewhere would end A's session), tries to spin.
        page_b = context.new_page()
        page_b.goto(server_url + '/')
        page_b.locator('.spin-prompt').click(force=True, timeout=10000)
        banner = page_b.locator('.tab-paused-banner')
        banner.wait_for(timeout=5000)
        assert 'this tab is paused' in banner.inner_text()

        page_b.get_by_role('button', name='Play here').click()
        banner.wait_for(state='detached', timeout=5000)

        # B now holds the lock: A is refused, B can spin.
        refused = _api_post(page_a, '/api/spin', {'tab_id': 'tab-a'})
        assert refused['status'] == 423
        tab_b = page_b.evaluate("sessionStorage.getItem('wheel_tab_id')")
        assert _api_post(page_b, '/api/spin', {'tab_id': tab_b})['ok']
    finally:
        browser.close()
