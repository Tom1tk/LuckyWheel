"""Fair Winds (Tide 9.4): a daily pick of one of three boons, good until London midnight."""
import datetime as dt
from datetime import timezone

import pytest

import fair_winds

from tests.test_charts import _chart, _get, _reset, _set, user  # noqa: F401
from tests.test_spin_integration import _post_spin, _read_csrf, game_app  # noqa: F401

NOON = dt.datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)  # 12:00 GMT
ALL_FOUR = {'treasure': 1, 'echo': 1, 'fortune_charm': 1, 'steady_keel': 1}


@pytest.fixture(autouse=True)
def _no_wind(request, db_url, _reset):  # noqa: F811
    if 'user' in request.fixturenames:
        _set(db_url, request.getfixturevalue('user')[1], fair_winds_boon=None, fair_winds_at=None)


def test_offers_are_fixed_for_the_day_and_skip_charted_talents():
    day = NOON.date()
    o = fair_winds.offers(7, {}, day)
    assert o[:2] == ['high_water', 'spare_change'] and o == fair_winds.offers(7, {}, day)
    assert fair_winds.offers(7, {'echo': 1, 'fortune_charm': 1, 'steady_keel': 1}, day)[2] == 'borrow:treasure'
    assert fair_winds.offers(7, ALL_FOUR, day) == ['high_water', 'spare_change']


def test_boon_runs_from_the_pick_to_london_midnight():
    gs = {'fair_winds_boon': 'high_water', 'fair_winds_at': NOON}
    assert fair_winds.active(gs, NOON - dt.timedelta(seconds=3)) is None  # catch-up spins before the pick
    assert fair_winds.active(gs, NOON + dt.timedelta(hours=11, minutes=59)) == 'high_water'
    assert fair_winds.active(gs, NOON + dt.timedelta(hours=12)) is None


def test_lend_adds_a_borrowed_talent_only_when_missing():
    assert fair_winds.lend(['x'], 'borrow:treasure') == (['x', 'jackpot'], 'jackpot')
    assert fair_winds.lend(['jackpot'], 'borrow:treasure') == (['jackpot'], None)
    assert fair_winds.lend(['x'], 'high_water') == (['x'], None)


def test_high_water_raises_surge_pay_by_half():
    import game
    ctx = {'effective_win_mult': 1, 'bonus_mult': 1}
    gs = {'talent_alloc': {'rich_waters': 1}}
    assert game._surge_mults(ctx, gs, 1, staked=False, diced=False, high_water=True) == (37.5, 37.5, 1)
    assert game._surge_mults(ctx, gs, 0, staked=False, diced=False, high_water=True) == (1, 1, 0)


def _pick(client, boon):
    r = client.post('/api/fair-winds', json={'boon': boon}, headers={'X-CSRFToken': _read_csrf(client)})
    return r.status_code, r.get_json()


def test_spare_change_goes_past_the_cap_and_only_once_a_day(user, db_url):
    client, username = user
    assert client.get('/api/state').get_json()['fair_winds']['picked'] is None
    _set(db_url, username, insurance_tokens=6)
    assert _pick(client, 'borrow:nonsense')[0] == 400
    status, body = _pick(client, 'spare_change')
    assert status == 200 and body['insurance_tokens'] == 7 and body['fair_winds']['picked']['id'] == 'spare_change'
    assert _pick(client, 'high_water')[0] == 409
    assert client.get('/api/state').get_json()['fair_winds']['offers'] == []


def test_borrowed_treasure_pays_a_jackpot_and_never_sticks(user, db_url, monkeypatch):
    import game
    client, username = user
    status, body = _chart(client, {'undertow': 2, 'echo': 1, 'fortune_charm': 1, 'steady_keel': 1})
    assert status == 200, body

    def spin():
        rolls = iter([0.5, 0.0])  # a plain win, then every proc roll succeeds
        with monkeypatch.context() as m:
            m.setattr(game.random, 'random', lambda: next(rolls, 0.99))
            status, body = _post_spin(client, _read_csrf(client))
        assert status == 200, body
        return body

    assert not spin()['jackpot_hit']
    status, body = _pick(client, 'borrow:treasure')
    assert status == 200, body
    assert spin()['jackpot_hit']
    assert 'jackpot' not in _get(db_url, username)['owned_items']
