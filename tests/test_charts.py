"""Season 9 Charts (docs/SEASON_9_DEEP_SPEC.md §3, §4, §10).

Part A tests talents.py as pure logic. Part B runs the real app against
wheeldb_test: /api/charts, the gear shop lock, stake chips, Spring Tide,
Rogue Wave, Surge and the ×5 staked jackpot.
"""
import datetime as dt
import uuid
from datetime import timezone

import psycopg2
import psycopg2.extras
import pytest

import talents
from models import (DICE_RECHARGE_SECONDS, ROGUE_WAVE_RECHARGE_SECONDS,
                    dice_max_charges, dice_recharge_seconds)
from tests.test_spin_integration import (  # noqa: F401
    _ROLL_JACKPOT, _ROLL_LOSE, _ROLL_WIN, _post_spin, _read_csrf, _register,
    force_random, game_app,
)

LONDON_FRI_2100 = dt.datetime(2026, 10, 9, 20, 0, tzinfo=timezone.utc)  # 21:00 BST
FULL_SWELL = {'undertow': 3, 'rising_tide': 2, 'steady_keel': 1, 'fortune_charm': 1,
              'echo': 1, 'breakwater': 1, 'spring_tide': 1}


# ══════════════════════════════════════════════════════════════════════════
# A. talents.py
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize('days,expected', [(0, 4), (1, 5), (3, 7), (6, 10)])
def test_points_grow_one_a_day_from_the_turn(days, expected):
    now = LONDON_FRI_2100 + dt.timedelta(days=days, minutes=1)
    assert talents.tide_day(now) == days
    assert talents.points_total(now) == expected


def test_day_rolls_at_2100_london_not_midnight():
    assert talents.tide_day(LONDON_FRI_2100 - dt.timedelta(minutes=1)) == 6
    assert talents.tide_day(LONDON_FRI_2100) == 0
    # Winter (GMT): 21:00 London is 21:00 UTC.
    winter = dt.datetime(2026, 12, 4, 21, 0, tzinfo=timezone.utc)
    assert talents.tide_day(winter) == 0
    assert talents.tide_day(winter - dt.timedelta(seconds=1)) == 6


def test_full_swell_with_keystone_is_legal_at_ten():
    assert talents.validate(FULL_SWELL, 10) is None
    assert talents.validate(FULL_SWELL, 9) == 'Not enough points (10 > 9)'


@pytest.mark.parametrize('alloc,error', [
    ('nope', 'Chart must be an object'),
    ({'bogus': 1}, 'Unknown talent: bogus'),
    ({'undertow': 4}, 'Bad rank for undertow'),
    ({'undertow': -1}, 'Bad rank for undertow'),
    ({'undertow': True}, 'Bad rank for undertow'),
    ({'undertow': '1'}, 'Bad rank for undertow'),
    ({'steady_keel': 1}, 'Steady Keel needs 2 points in 🌊 Swell'),
    # Row 2 talents can't unlock each other.
    ({'steady_keel': 1, 'echo': 1, 'fortune_charm': 1}, 'Steady Keel needs 2 points in 🌊 Swell'),
    ({'undertow': 3, 'breakwater': 1}, 'Breakwater needs 4 points in 🌊 Swell'),
    ({'undertow': 3, 'rising_tide': 2, 'spring_tide': 1}, 'Spring Tide needs 6 points in 🌊 Swell'),
    ({'loaded_dice': 2, 'deep_water': 1}, 'Deep Water needs Open Water first'),
    ({'undertow': 3, 'rising_tide': 2, 'steady_keel': 1, 'spring_tide': 1,
      'rich_waters': 3, 'better_bait': 2, 'deep_sea': 1}, 'Not enough points (13 > 10)'),
])
def test_validate_rejects(alloc, error):
    assert talents.validate(alloc, 10) == error


def test_only_one_keystone():
    alloc = {'undertow': 3, 'rising_tide': 2, 'steady_keel': 1, 'spring_tide': 1,
             'rich_waters': 3, 'better_bait': 2, 'deep_sea': 1}
    assert talents.validate(alloc, 99) == 'Only one keystone'


def test_requires_needs_full_rank_of_prerequisite():
    assert talents.validate({'open_water': 1, 'loaded_dice': 1, 'deep_water': 2}, 10) is None
    assert talents.validate({'rich_waters': 2, 'deckhand': 1, 'better_bait': 1, 'old_salt': 1}, 10) \
        == 'Old Salt needs Deckhand first'


def test_granted_items_are_cumulative():
    assert talents.granted_items({'undertow': 2}) == ['bonusmult_1', 'bonusmult_2']
    assert talents.granted_items({'better_bait': 1}) == ['lure_1', 'lure_2']
    assert talents.granted_items({'rich_waters': 3, 'spring_tide': 1}) == []


def test_recompute_owned_keeps_cosmetics_and_strips_ungranted_gear():
    owned = ['trail_2', 'page_season9', 'auto_spin_unlock', 'winmult_3', 'lucky_seven', 'wager_unlock']
    out = talents.recompute_owned(owned, {'open_water': 1, 'deep_water': 1})
    assert set(out) == {'trail_2', 'page_season9', 'auto_spin_unlock',
                        'wager_unlock', 'wager_stake_extend_1'}


def test_refund_detection():
    assert not talents.is_refund({}, {'undertow': 1})
    assert not talents.is_refund({'undertow': 1}, {'undertow': 2, 'echo': 0})
    assert talents.is_refund({'undertow': 2}, {'undertow': 1})
    assert talents.is_refund({'echo': 1}, {})


def test_surge_numbers():
    assert talents.surge_mult({}) == 5
    assert talents.surge_mult({'rich_waters': 3}) == 100
    assert talents.surge_bonus({'better_bait': 2}) == 1.5


def test_every_grant_is_real_gear():
    from models import SHOP_ITEMS
    assert talents.GRANTABLE <= set(SHOP_ITEMS)
    assert 'auto_spin_unlock' not in talents.CHART_REPLACES


def test_rogue_wave_dice_rules():
    assert dice_max_charges(['dice_charge_2']) == 2
    assert dice_max_charges(['dice_charge_2'], {'rogue_wave': 1}) == 4
    assert dice_max_charges([], {'rogue_wave': 1}) == 3
    assert dice_recharge_seconds({}) == DICE_RECHARGE_SECONDS
    assert dice_recharge_seconds({'rogue_wave': 1}) == ROGUE_WAVE_RECHARGE_SECONDS


# ══════════════════════════════════════════════════════════════════════════
# B. Live routes
# ══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope='module')
def user(game_app, db_url):  # noqa: F811
    from extensions import limiter
    limiter.reset()
    client = game_app.test_client()
    username = f'chart{uuid.uuid4().hex[:8]}'
    status, body, _csrf = _register(client, username, 'testpass123')
    if status != 201:
        pytest.fail(f'register failed: {status} {body}')
    yield client, username
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute('DELETE FROM users WHERE username = %s', (username,))
    conn.close()


@pytest.fixture(autouse=True)
def _reset(request, db_url, monkeypatch):
    if 'user' in request.fixturenames:
        monkeypatch.setattr(talents, 'points_total', lambda now: 10)
        _set(db_url, request.getfixturevalue('user')[1],
             talent_alloc={}, talent_rechart_date=None, owned_items=['auto_spin_unlock'],
             surge_spins=0, insurance_tokens=0, wins=1000, losses=0, streak=0, spin_count=0,
             wager_last_stake=0, double_down_pending=False, active_wheel_mode='steady',
             dice_rolled_since_spin=False, pending_dice=None, auto_spin_since=None)
        from extensions import limiter
        limiter.reset()
    yield


def _set(db_url, username, **cols):
    cols = {k: psycopg2.extras.Json(v) if isinstance(v, dict) else v for k, v in cols.items()}
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'UPDATE game_state SET {", ".join(f"{k} = %s" for k in cols)} '
                'WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                (*cols.values(), username))
    finally:
        conn.close()


def _get(db_url, username):
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM game_state WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                        (username,))
            return cur.fetchone()
    finally:
        conn.close()


def _chart(client, alloc):
    r = client.post('/api/charts', json={'alloc': alloc}, headers={'X-CSRFToken': _read_csrf(client)})
    return r.status_code, r.get_json()


def test_get_charts_lists_trees_and_points(user):
    client, _ = user
    body = client.get('/api/charts').get_json()
    assert body['points'] == 10 and body['spent'] == 0 and body['can_rechart'] is True
    assert set(body['trees']) == {'swell', 'riptide', 'angler'}
    assert {t['id'] for t in body['talents']} == set(talents.TALENTS)


def test_chart_grants_gear_and_keeps_cosmetics(user, db_url):
    client, username = user
    _set(db_url, username, owned_items=['auto_spin_unlock', 'trail_2', 'winmult_7'])
    status, body = _chart(client, {'undertow': 2, 'open_water': 1})
    assert status == 200, body
    owned = set(_get(db_url, username)['owned_items'])
    assert owned == {'auto_spin_unlock', 'trail_2', 'bonusmult_1', 'bonusmult_2', 'wager_unlock'}
    assert set(body['owned_items']) == owned
    assert body['spent'] == 3 and body['max_stake_pct'] == 30


def test_adding_is_free_refund_once_a_day(user, db_url):
    client, username = user
    assert _chart(client, {'undertow': 1})[0] == 200
    assert _chart(client, {'undertow': 2})[0] == 200
    assert _chart(client, {'undertow': 2, 'echo': 0, 'rising_tide': 1})[0] == 200
    status, body = _chart(client, {'undertow': 1})      # refund #1 — allowed
    assert status == 200 and body['can_rechart'] is False
    status, body = _chart(client, {})                   # refund #2 same day — refused
    assert status == 409
    assert body['error'] == 'You can re-chart once a day — come back tomorrow.'
    assert _get(db_url, username)['talent_alloc'] == {'undertow': 1}
    assert _chart(client, {'undertow': 2})[0] == 200    # adding still works


def test_bad_chart_is_400_and_changes_nothing(user, db_url):
    client, username = user
    for bad in ({'undertow': 9}, {'bogus': 1}, {'steady_keel': 1}, None, [1]):
        status, body = _chart(client, bad)
        assert status == 400, (bad, body)
    assert _get(db_url, username)['talent_alloc'] == {}


@pytest.mark.parametrize('item', sorted(talents.CHART_REPLACES))
def test_gear_is_not_for_sale(user, db_url, item):
    client, username = user
    _set(db_url, username, wins=10**15, cumulative_wins=10**15)
    r = client.post('/api/buy', json={'item_id': item}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 403
    assert item not in _get(db_url, username)['owned_items']


def test_cosmetics_still_sell(user, db_url):
    client, username = user
    _set(db_url, username, losses=10**12)
    r = client.post('/api/buy', json={'item_id': 'trail_1'}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 200, r.get_json()


def test_staked_spin_without_chips_is_refused(user, db_url):
    client, username = user
    _chart(client, {'open_water': 1})
    status, body = _post_spin(client, _read_csrf(client), stake=10)
    assert status == 400
    assert body['error'] == "Out of 🪙 chips — claim today's 3"
    gs = _get(db_url, username)
    assert gs['spin_count'] == 0 and int(gs['wins']) == 1000


def test_staked_spin_costs_one_chip_unstaked_costs_none(user, db_url, force_random):  # noqa: F811
    client, username = user
    _chart(client, {'open_water': 1})
    _set(db_url, username, insurance_tokens=3)
    with force_random(_ROLL_WIN):
        status, body = _post_spin(client, _read_csrf(client), stake=10)
    assert status == 200 and body['insurance_tokens'] == 2 and body['tokens_spent'] == 1
    with force_random(_ROLL_WIN):
        status, body = _post_spin(client, _read_csrf(client), stake=0)
    assert status == 200 and body['insurance_tokens'] == 2
    assert _get(db_url, username)['insurance_tokens'] == 2


def test_stake_without_open_water_is_free_and_ignored(user, db_url, force_random):  # noqa: F811
    client, username = user
    with force_random(_ROLL_WIN):
        status, body = _post_spin(client, _read_csrf(client), stake=10)
    assert status == 200 and body['stake'] == 0
    assert _get(db_url, username)['insurance_tokens'] == 0


def test_spring_tide_forces_stake_zero_and_blocks_dice(user, db_url, force_random):  # noqa: F811
    client, username = user
    _set(db_url, username, owned_items=['auto_spin_unlock', 'wager_unlock'], insurance_tokens=0)
    assert _chart(client, FULL_SWELL)[0] == 200
    with force_random(_ROLL_WIN):
        status, body = _post_spin(client, _read_csrf(client), stake=20)
    assert status == 200 and body['stake'] == 0
    _set(db_url, username, streak=5, dice_charges=1)
    r = client.post('/api/roll-dice', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 403 and r.get_json()['error'] == 'Spring Tide: no dice'


def test_spring_tide_doubles_streak_bonus(user, db_url, force_random):  # noqa: F811
    client, username = user
    alloc = dict(FULL_SWELL)
    del alloc['spring_tide']
    _chart(client, alloc)
    _set(db_url, username, streak=4)
    with force_random(_ROLL_WIN):
        _, plain = _post_spin(client, _read_csrf(client))
    _set(db_url, username, streak=4, talent_alloc=FULL_SWELL)
    with force_random(_ROLL_WIN):
        _, spring = _post_spin(client, _read_csrf(client))
    assert spring['bonus_earned'] == 2 * plain['bonus_earned'] > 0


def test_surge_adds_to_multipliers_and_spends_one(user, db_url, force_random):  # noqa: F811
    client, username = user
    _chart(client, {'rich_waters': 3})
    with force_random(_ROLL_WIN):
        _, plain = _post_spin(client, _read_csrf(client))
    _set(db_url, username, streak=0, surge_spins=2)
    with force_random(_ROLL_WIN):
        _, surged = _post_spin(client, _read_csrf(client))
    assert plain['surge_used'] is False and surged['surge_used'] is True
    assert surged['surge_spins'] == 1 and _get(db_url, username)['surge_spins'] == 1
    assert surged['wins_delta'] == plain['wins_delta'] + 99


def test_rogue_wave_never_spends_surge(user, db_url, force_random):  # noqa: F811
    client, username = user
    _chart(client, {'open_water': 1, 'loaded_dice': 3, 'treasure': 1, 'deep_water': 1, 'rogue_wave': 1})
    _set(db_url, username, surge_spins=5)
    with force_random(_ROLL_WIN):
        _, body = _post_spin(client, _read_csrf(client))
    assert body['surge_used'] is False and body['surge_spins'] == 5


def test_tick_spends_surge_per_auto_spin(user, db_url):
    client, username = user
    _chart(client, {'rich_waters': 1})
    past = dt.datetime.now(timezone.utc) - dt.timedelta(seconds=10)
    _set(db_url, username, surge_spins=2, auto_spin_since=past, last_spin_at=past, insurance_tokens=4)
    r = client.post('/api/tick', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 200, r.get_json()
    assert len(r.get_json()['spins']) == 3
    gs = _get(db_url, username)
    assert gs['surge_spins'] == 0 and r.get_json()['state']['surge_spins'] == 0
    assert gs['insurance_tokens'] == 4  # auto-spin never charges chips


def test_staked_jackpot_pays_five_times_the_stake(user, db_url, force_random):  # noqa: F811
    client, username = user
    _chart(client, {'open_water': 1})
    _set(db_url, username, insurance_tokens=1)
    with force_random(_ROLL_JACKPOT):
        status, body = _post_spin(client, _read_csrf(client), stake=10)
    assert status == 200 and body['result'] == 'jackpot', body
    assert int(_get(db_url, username)['wins']) == 1000 + 100 * 5


def test_state_exposes_charts_and_surge(user, db_url):
    client, username = user
    _chart(client, {'rich_waters': 2})
    _set(db_url, username, surge_spins=7)
    body = client.get('/api/state').get_json()
    assert body['charts']['alloc'] == {'rich_waters': 2}
    assert body['charts']['surge_mult'] == 50 and body['charts']['points'] == 10
    assert body['surge_spins'] == 7


def test_pending_double_down_without_open_water_needs_no_chip(user, db_url, force_random):  # noqa: F811
    client, username = user
    _set(db_url, username, double_down_pending=True, wager_last_win_amount=50)
    with force_random(_ROLL_WIN):
        status, body = _post_spin(client, _read_csrf(client))
    assert status == 200, body


def test_rechart_drops_armed_double_down_insurance_and_class(user, db_url):
    client, username = user
    full = {'open_water': 1, 'loaded_dice': 1, 'safety_line': 1, 'treasure': 1,
            'third_die': 1, 'double_or_nothing': 1}
    assert _chart(client, full)[0] == 200
    _set(db_url, username, double_down_pending=True, insurance_armed=True, equipped_class='star')
    assert _chart(client, {'open_water': 1})[0] == 200
    gs = _get(db_url, username)
    assert not gs['double_down_pending'] and not gs['insurance_armed'] and gs['equipped_class'] is None


def test_wins_to_fish_exchange_is_closed(user, db_url):
    client, username = user
    r = client.post('/api/wins-exchange', json={'amount': 'all'}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 403
    assert _get(db_url, username)['wins'] == 1000
