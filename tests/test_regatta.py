"""Tide Regatta: first 3 stakes per race count, scored 0/1/5 on the wheel outcome,
placed 5/3/2/1 with ties sharing the higher place (wheeldb_test)."""
import datetime as dt
from datetime import timezone

import psycopg2
import pytest

import regatta
import tide_stats
from tests.test_charts import _chart, _reset, _set, user  # noqa: F401
from tests.test_spin_integration import (  # noqa: F401
    _ROLL_LOSE, _ROLL_WIN, _post_spin, _read_csrf, _today_london, force_random, game_app,
)


def _exec(db_url, sql, params=()):
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() if cur.description else None
    finally:
        conn.close()


@pytest.fixture
def racer(user, db_url):  # noqa: F811
    """A test user that shows in the Regatta (test IPs are hidden from it)."""
    client, username = user
    _exec(db_url, "UPDATE users SET ip_address = '10.99.0.1' WHERE username = %s", (username,))
    _exec(db_url, 'DELETE FROM regatta_stakes WHERE user_id = (SELECT id FROM users WHERE username = %s)',
          (username,))
    _chart(client, {'open_water': 1})
    _set(db_url, username, insurance_tokens=6, haul=10_000, haul_date=_today_london())
    return client, username


def _scores(db_url, username):
    return [r[0] for r in _exec(
        db_url, 'SELECT score FROM regatta_stakes WHERE user_id = (SELECT id FROM users WHERE username = %s) '
                'ORDER BY n', (username,))]


def test_placings_share_ties_and_zero_does_not_place():
    race = {1: ('a', 5, []), 2: ('b', 5, []), 3: ('c', 2, []), 4: ('d', 0, [])}
    assert regatta.placings(race) == {1: 5, 2: 5, 3: 2, 4: 0}


def test_race_end_messages():
    assert regatta.race_end_msg(3, {1: ('worm', 7, []), 2: ('tom', 2, [])}) == '🏁 Race 3 goes to worm, scoring 7.'
    assert regatta.race_end_msg(2, {1: ('worm', 1, []), 2: ('tom', 1, [])}) == \
        '🏁 Race 2 is a dead heat: tom and worm, scoring 1.'
    assert regatta.race_end_msg(1, {1: ('worm', 0, [])}) is None


def test_race_number_and_end_follow_the_tide_day():
    fri_after_turn = dt.datetime(2026, 11, 6, 21, 30, tzinfo=timezone.utc)
    assert regatta.race_number(fri_after_turn) == 1
    assert regatta.race_ends_at(fri_after_turn) == dt.datetime(2026, 11, 7, 21, 0, tzinfo=timezone.utc)
    fri = dt.datetime(2026, 11, 13, 20, 0, tzinfo=timezone.utc)
    assert regatta.race_number(fri) == 7
    assert regatta.race_ends_at(fri) == dt.datetime(2026, 11, 13, 21, 0, tzinfo=timezone.utc)


def test_only_the_first_three_stakes_count(racer, db_url, force_random):
    client, username = racer
    for roll in (_ROLL_WIN, _ROLL_LOSE, _ROLL_WIN, _ROLL_WIN):
        with force_random(roll):
            status, body = _post_spin(client, _read_csrf(client), stake=10)
        assert status == 200 and body['stake'] > 0
    assert _scores(db_url, username) == [1, 0, 1]
    r = client.get('/api/regatta').get_json()
    assert r['my_scores'] == [1, 0, 1] and r['my_score'] == 2 and r['my_place'] == 1
    assert r['races'] == 7 and r['stakes'] == 3


def test_unstaked_spins_do_not_race(racer, db_url, force_random):
    client, username = racer
    with force_random(_ROLL_WIN):
        status, _ = _post_spin(client, _read_csrf(client))
    assert status == 200
    assert _scores(db_url, username) == []


def test_announce_posts_each_finished_race_once(db_url):
    now = dt.datetime(2026, 11, 8, 22, 0, tzinfo=timezone.utc)   # race 3 under way
    tide = tide_stats.tide_date(now)
    _exec(db_url, 'DELETE FROM regatta_announced WHERE tide_date IN (%s, %s)', (tide, tide - dt.timedelta(days=7)))
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            regatta.announce_finished(cur, now)
            cur.execute('SELECT race FROM regatta_announced WHERE tide_date = %s ORDER BY race', (tide,))
            assert [r[0] for r in cur.fetchall()] == [1, 2]
            assert regatta.announce_finished(cur, now) == []
    finally:
        conn.rollback()
        conn.close()


def test_leaderboard_ranks_by_race_points(racer, db_url, force_random):
    client, username = racer
    with force_random(_ROLL_WIN):
        _post_spin(client, _read_csrf(client), stake=10)
    now = dt.datetime.now(timezone.utc)
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            pts = regatta.tide_points(cur, tide_stats.tide_date(now))
            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            uid = cur.fetchone()[0]
    finally:
        conn.close()
    assert pts[uid] >= 1
    rows = client.get('/api/leaderboard').get_json()
    mine = [r for r in rows if r['username'] == username]
    assert mine and mine[0]['race_points'] == pts[uid]
