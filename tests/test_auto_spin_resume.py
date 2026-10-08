"""S9: reloading the page resumes server-side auto-spin instead of stopping it (old T216 behaviour)."""
import uuid

from tests.test_tab_takeover import PASSWORD, _new_context
from tests.test_mobile_e2e import _api_post


def test_reload_keeps_auto_spin_running(server_url, playwright_instance):
    browser = playwright_instance.chromium.launch()
    try:
        page = _new_context(browser).new_page()
        page.goto(server_url + '/')
        assert _api_post(page, '/api/register', {'username': f'rs{uuid.uuid4().hex[:8]}', 'password': PASSWORD})['ok']
        page.reload()
        assert _api_post(page, '/api/auto-spin/start', {})['ok']

        page.reload()
        page.locator('.autospin-row input[type=checkbox]:checked').wait_for(timeout=10000)
        page.wait_for_timeout(1500)
        state = page.evaluate("fetch('/api/state').then(r => r.json())")
        assert state['auto_spin_active'] is True
    finally:
        browser.close()
