"""RV-12: /api/patch-notes serves the Season 9 entry first."""
from tests.test_spin_integration import game_app  # noqa: F401


def test_patch_notes_lead_with_season_9(game_app):  # noqa: F811
    r = game_app.test_client().get('/api/patch-notes')
    assert r.status_code == 200
    first_entry = r.get_json()['content'].split('\n## ')[1]
    assert first_entry.startswith('Season 9 — Tides')
