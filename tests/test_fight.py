"""S9 D4: the fishing fight — /api/reel hooks, /api/land pays out (spec §5)."""

import datetime as dt
from datetime import timezone

import pytest

import fish
from tests.test_charts import _get, _reset, _set, user  # noqa: F401
from tests.test_spin_integration import _read_csrf, game_app  # noqa: F401


def _post(client, path, body):
    r = client.post(path, json=body, headers={'X-CSRFToken': _read_csrf(client)})
    return r.status_code, r.get_json()


def _bite_now(db_url, username, ago=0.4):
    now = dt.datetime.now(timezone.utc)
    _set(db_url, username, fishing_cast_at=now - dt.timedelta(seconds=3),
         fishing_bite_at=now - dt.timedelta(seconds=ago), fishing_species=None, fishing_hooked_at=None)


def _hooked(db_url, username, species='shark', fought=7.0, **cols):
    _set(db_url, username, fishing_species=species,
         fishing_hooked_at=dt.datetime.now(timezone.utc) - dt.timedelta(seconds=fought), **cols)


def test_hook_stores_species_and_hides_it(user, db_url, monkeypatch):
    client, username = user
    monkeypatch.setattr(fish, 'roll_fish', lambda **k: 'shark')
    _bite_now(db_url, username)
    st, body = _post(client, '/api/reel', {})
    assert st == 200 and body['result'] == 'hooked'
    assert body['rarity'] == 'rare' and body['fight_s'] == 6.0 and 'species' not in body
    gs = _get(db_url, username)
    assert gs['fishing_species'] == 'shark' and gs['fishing_hooked_at'] is not None
    assert gs['fishing_cast_at'] is None


def test_hook_outside_window_misses(user, db_url):
    client, username = user
    _bite_now(db_url, username, ago=5)
    st, body = _post(client, '/api/reel', {})
    assert body['result'] == 'miss' and body['reason'] == 'bad_timing'
    assert _get(db_url, username)['fishing_species'] is None


def test_land_without_hook_is_no_session(user, db_url):
    client, username = user
    _set(db_url, username, fishing_species=None, fishing_hooked_at=None)
    st, body = _post(client, '/api/land', {'landed': True, 'quality': 1})
    assert st == 200 and body['reason'] == 'no_session'


def test_full_fight_pays_once(user, db_url, monkeypatch):
    client, username = user
    monkeypatch.setattr(fish, 'roll_fish', lambda **k: 'minnow')
    _set(db_url, username, fish_clicks=0, catch_of_the_day_date=None)
    _bite_now(db_url, username)
    assert _post(client, '/api/reel', {})[1]['fight_s'] == 3.0
    _set(db_url, username, fishing_hooked_at=dt.datetime.now(timezone.utc) - dt.timedelta(seconds=3.2))
    st, body = _post(client, '/api/land', {'landed': True, 'quality': 0.9})
    assert body['result'] == 'hit' and body['species'] == 'minnow' and body['catch_of_day_bonus']
    gs = _get(db_url, username)
    assert gs['fish_clicks'] == body['value'] and gs['fishing_species'] is None
    assert _post(client, '/api/land', {'landed': True, 'quality': 0.9})[1]['reason'] == 'no_session'


def test_land_too_fast_and_timeout(user, db_url):
    client, username = user
    _hooked(db_url, username, fought=3.0)  # shark needs ≥ 3.6 s
    assert _post(client, '/api/land', {'landed': True, 'quality': 1})[1]['reason'] == 'too_fast'
    _hooked(db_url, username, fought=46)
    assert _post(client, '/api/land', {'landed': True, 'quality': 1})[1]['reason'] == 'timeout'
    assert _get(db_url, username)['fishing_species'] is None


def test_lost_fish_clears_the_line_and_pays_nothing(user, db_url):
    client, username = user
    _hooked(db_url, username, fish_clicks=10)
    st, body = _post(client, '/api/land', {'landed': False, 'quality': 0})
    assert body == {'result': 'lost', 'fish_clicks': 10}
    gs = _get(db_url, username)
    assert gs['fishing_species'] is None and gs['fish_clicks'] == 10


@pytest.mark.parametrize('body', [{}, {'landed': 'yes', 'quality': 1}, {'landed': True, 'quality': 'x'},
                                  {'landed': True, 'quality': True}, {'landed': True, 'quality': None}])
def test_land_rejects_bad_payload(user, db_url, body):
    client, username = user
    _hooked(db_url, username)
    st, _ = _post(client, '/api/land', body)
    assert st == 400
    assert _get(db_url, username)['fishing_species'] == 'shark'


def test_quality_clamped_and_kg_in_bounds(user, db_url):
    client, username = user
    lo, hi = fish.FISH_CATALOG['shark']['kg']
    for q in (-5, 0, 0.5, 1, 99):
        _hooked(db_url, username)
        body = _post(client, '/api/land', {'landed': True, 'quality': q})[1]
        assert lo <= body['kg'] <= hi


def test_recast_clears_an_abandoned_hook(user, db_url):
    client, username = user
    _hooked(db_url, username)
    _set(db_url, username, fishing_cast_at=None, fishing_bite_at=None)
    st, _ = _post(client, '/api/cast', {})
    assert st == 200
    assert _get(db_url, username)['fishing_species'] is None
