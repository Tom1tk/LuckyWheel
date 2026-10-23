"""Per-player, per-tide counters (tide_stats): the tide date, the upsert, and
each bump site landing in the right column against the real DB (wheeldb_test)."""
import datetime as dt
import sys
from datetime import timezone

import psycopg2
import psycopg2.extras
import pytest

import tide_stats
from tests.test_charts import _chart, _reset, _set, user  # noqa: F401
from tests.test_spin_integration import (  # noqa: F401
    _ROLL_LOSE, _ROLL_WIN, _post_spin, _read_csrf, _today_london, _user_id_for, force_random,
    game_app,
)

NOW = dt.datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


def _exec(db_url, sql, params=()):
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
    finally:
        conn.close()


def _tide(db_url, username):
    """The user's only tide_stats row (the fixture wipes them before each test)."""
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM tide_stats WHERE user_id = (SELECT id FROM users WHERE username = %s)',
                        (username,))
            rows = cur.fetchall()
    finally:
        conn.close()
    assert len(rows) == 1, rows
    return rows[0]


@pytest.fixture(autouse=True)
def _clear_tide(request, db_url):
    if 'user' in request.fixturenames:
        username = request.getfixturevalue('user')[1]
        _exec(db_url, 'DELETE FROM tide_stats WHERE user_id = (SELECT id FROM users WHERE username = %s)',
              (username,))
    yield


class _Cur:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


# ── tide_date ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize('utc,expected', [
    (dt.datetime(2026, 10, 9, 19, 59, tzinfo=timezone.utc), dt.date(2026, 10, 2)),   # Fri 20:59 BST
    (dt.datetime(2026, 10, 9, 20, 0, tzinfo=timezone.utc), dt.date(2026, 10, 9)),    # Fri 21:00 BST: turn
    (dt.datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc), dt.date(2026, 10, 9)),   # Sat
    (dt.datetime(2026, 10, 8, 23, 0, tzinfo=timezone.utc), dt.date(2026, 10, 2)),    # Thu
    (dt.datetime(2026, 12, 4, 20, 59, tzinfo=timezone.utc), dt.date(2026, 11, 27)),  # Fri 20:59 GMT
    (dt.datetime(2026, 12, 4, 21, 0, tzinfo=timezone.utc), dt.date(2026, 12, 4)),    # Fri 21:00 GMT: turn
])
def test_tide_date_is_the_friday_turn_in_london(utc, expected):
    assert tide_stats.tide_date(utc) == expected


# ── bump ──────────────────────────────────────────────────────────────────

def test_bump_drops_zeros_and_skips_the_query_when_nothing_is_left():
    cur = _Cur()
    tide_stats.bump(cur, 7, NOW, manual_spins=0, surge_spent=0)
    assert cur.calls == []
    tide_stats.bump(cur, 7, NOW, manual_spins=1, surge_spent=0)
    sql, params = cur.calls[0]
    assert params == (7, tide_stats.tide_date(NOW), 1)
    assert 'surge_spent' not in sql


def test_bump_rejects_unknown_columns():
    with pytest.raises(ValueError):
        tide_stats.bump(_Cur(), 7, NOW, not_a_column=1)


def test_bump_adds_into_the_same_tide_row(user, db_url):  # noqa: F811
    client, username = user
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            tide_stats.bump(cur, _user_id_for(db_url, username), NOW, manual_spins=1, surge_spent=2)
            tide_stats.bump(cur, _user_id_for(db_url, username), NOW, manual_spins=2)
        conn.commit()
    finally:
        conn.close()
    row = _tide(db_url, username)
    assert row['manual_spins'] == 3 and row['surge_spent'] == 2


# ── spin ──────────────────────────────────────────────────────────────────

def test_manual_unstaked_spin_counts_one_manual_spin(user, db_url, force_random):  # noqa: F811
    client, username = user
    with force_random(_ROLL_WIN):
        status, _ = _post_spin(client, _read_csrf(client))
    assert status == 200
    row = _tide(db_url, username)
    assert row['manual_spins'] == 1
    assert row['staked_spins'] == 0 and row['stake_wins_sum'] == 0


@pytest.mark.parametrize('roll,won', [(_ROLL_WIN, True), (_ROLL_LOSE, False)])
def test_staked_spin_counts_the_wins_it_moved(user, db_url, force_random, roll, won):  # noqa: F811
    client, username = user
    _chart(client, {'open_water': 1})
    _set(db_url, username, insurance_tokens=1, haul=1000, haul_date=_today_london())
    with force_random(roll):
        status, body = _post_spin(client, _read_csrf(client), stake=10)
    assert status == 200
    d = body['wins_delta']
    assert (d > 0) == won and d != 0
    row = _tide(db_url, username)
    assert row['staked_spins'] == 1 and row['manual_spins'] == 1
    assert row['stake_pct_sum'] == body['stake'] > 0
    assert row['staked_wins_gained'] == max(d, 0) and row['staked_wins_lost'] == max(-d, 0)
    assert row['stake_wins_sum'] > 0


def test_inverted_stake_counts_as_staked_but_not_as_wins(user, db_url, force_random):  # noqa: F811
    client, username = user
    _chart(client, {'open_water': 1})
    _set(db_url, username, insurance_tokens=1, losses=1000, active_wheel_mode='inverted')  # stake comes out of losses
    with force_random(_ROLL_WIN):
        status, body = _post_spin(client, _read_csrf(client), stake=10)
    assert status == 200 and body['stake'] > 0
    row = _tide(db_url, username)
    assert row['staked_spins'] == 1 and row['stake_pct_sum'] == body['stake']
    assert row['staked_wins_gained'] == 0 and row['staked_wins_lost'] == 0
    assert row['stake_wins_sum'] == 0


def test_surge_spent_on_a_spin_is_counted(user, db_url, force_random):  # noqa: F811
    client, username = user
    _chart(client, {'rich_waters': 3})
    _set(db_url, username, surge_spins=2)
    with force_random(_ROLL_WIN):
        _, body = _post_spin(client, _read_csrf(client))
    assert body['surge_used'] is True
    row = _tide(db_url, username)
    assert row['surge_spent'] == 1 and row['manual_spins'] == 1


def test_insurance_firing_on_an_unstaked_loss_is_counted(user, db_url, force_random):  # noqa: F811
    client, username = user
    _set(db_url, username, insurance_armed=True)
    with force_random(_ROLL_LOSE):
        status, body = _post_spin(client, _read_csrf(client))
    assert status == 200 and body['insurance_used'] is True and body['stake'] == 0
    row = _tide(db_url, username)
    assert row['insurance_used'] == 1 and row['staked_spins'] == 0


# ── dice ──────────────────────────────────────────────────────────────────

def test_roll_dice_counts_one_dice_roll(user, db_url):  # noqa: F811
    client, username = user
    _set(db_url, username, streak=5, dice_charges=1)
    r = client.post('/api/roll-dice', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 200, r.get_json()
    assert _tide(db_url, username)['dice_rolls'] == 1


# ── tick (auto-spins) ─────────────────────────────────────────────────────

def test_tick_counts_auto_spins_and_surge_spent(user, db_url):  # noqa: F811
    client, username = user
    _chart(client, {'rich_waters': 1})
    past = dt.datetime.now(timezone.utc) - dt.timedelta(seconds=10)
    _set(db_url, username, surge_spins=2, auto_spin_since=past, last_spin_at=past, insurance_tokens=4)
    r = client.post('/api/tick', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 200 and len(r.get_json()['spins']) == 3
    row = _tide(db_url, username)
    assert row['auto_spins'] == 3 and row['surge_spent'] == 2 and row['manual_spins'] == 0


# ── fishing (Surge from catches) ──────────────────────────────────────────

def test_land_counts_surge_from_catch(user, db_url):  # noqa: F811
    client, username = user
    _set(db_url, username, fishing_species='shark', fish_records={},
         fishing_hooked_at=dt.datetime.now(timezone.utc) - dt.timedelta(seconds=7))
    body = client.post('/api/land', json={'landed': True, 'quality': 0.5},
                       headers={'X-CSRFToken': _read_csrf(client)}).get_json()
    assert body['result'] == 'hit' and body['surge'] > 0
    assert _tide(db_url, username)['surge_from_catch'] == body['surge']


def _auto_fish_setup(db_url, username, monkeypatch, seconds_ago):
    _set(db_url, username, owned_items=['auto_spin_unlock', 'autofisher_1'], auto_spin_since=None,
         auto_fish_enabled=True, fish_records={},
         auto_fish_last_tick=dt.datetime.now(timezone.utc) - dt.timedelta(seconds=seconds_ago))
    fish = sys.modules['fish']
    monkeypatch.setattr(fish, 'roll_fish', lambda **k: 'crab')
    monkeypatch.setattr(fish, 'autofisher_catch_rate', lambda lvl: 1.0)


def test_afk_catch_up_via_tick_counts_surge_from_catch_up(user, db_url, monkeypatch):  # noqa: F811
    client, username = user
    _auto_fish_setup(db_url, username, monkeypatch, seconds_ago=61)
    r = client.post('/api/tick', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    catch = r.get_json()['fish_catchup']
    assert catch['surge'] > 0
    assert _tide(db_url, username)['surge_from_catch_up'] == catch['surge']


def test_afk_catch_up_via_auto_fish_tick_counts_surge_from_catch_up(user, db_url, monkeypatch):  # noqa: F811
    client, username = user
    _auto_fish_setup(db_url, username, monkeypatch, seconds_ago=61)
    body = client.post('/api/auto-fish-tick', json={}, headers={'X-CSRFToken': _read_csrf(client)}).get_json()
    assert body['result'] == 'catchup' and body['fish_catchup']['surge'] > 0
    assert _tide(db_url, username)['surge_from_catch_up'] == body['fish_catchup']['surge']


def test_auto_fish_catch_counts_surge_from_auto_fish(user, db_url, monkeypatch):  # noqa: F811
    client, username = user
    _auto_fish_setup(db_url, username, monkeypatch, seconds_ago=7)
    body = client.post('/api/auto-fish-tick', json={}, headers={'X-CSRFToken': _read_csrf(client)}).get_json()
    assert body['result'] == 'hit' and body['surge'] > 0
    assert _tide(db_url, username)['surge_from_auto_fish'] == body['surge']
