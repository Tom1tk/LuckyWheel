"""S9 RV-03: auto-spin is free from spin 1, so every account owns it.

Runs the real app against the real test DB (wheeldb_test): a new
registration is granted `auto_spin_unlock`, and the deleted
/api/register-season endpoint no longer exists.
"""
import uuid

import pytest

from tests.test_spin_integration import _register, game_app  # noqa: F401


@pytest.fixture(autouse=True)
def _fresh_rate_limiter(game_app):  # noqa: F811
    """/api/register is limited to 5/hour per IP; start each test clean."""
    from extensions import limiter
    limiter.reset()
    yield


def _owned_items(db_url, username):
    import psycopg2
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT owned_items FROM game_state '
                'WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                (username,),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def test_new_registration_owns_auto_spin_unlock(game_app, db_url):  # noqa: F811
    client = game_app.test_client()
    username = f'rv03{uuid.uuid4().hex[:8]}'
    status, body, _ = _register(client, username, 'testpass123')
    assert status == 201, f'register failed: {status} {body}'

    owned = _owned_items(db_url, username)
    assert 'auto_spin_unlock' in owned, (
        f'new accounts must own auto_spin_unlock from spin 1 (S9 RV-03), got: {owned}'
    )


def test_register_season_endpoint_is_removed(game_app):  # noqa: F811
    client = game_app.test_client()
    csrf = client.get('/api/me').get_json()['csrf_token']
    r = client.post('/api/register-season', json={}, headers={'X-CSRFToken': csrf})
    assert r.status_code == 404, (
        f'/api/register-season must be deleted (S9 RV-03), got {r.status_code}'
    )
