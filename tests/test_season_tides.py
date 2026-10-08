"""RV-01: season config, tide sub-numbers, season_log, and the Friday 21:00 London rollover.

DB tests run against wheeldb_test inside a transaction that the fixture rolls
back (the pattern from test_backfill_season8_theme.py). advance_season() commits
internally, so the connection is wrapped to turn that commit into a no-op.
"""
import importlib.util
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg2
import psycopg2.extras
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from loadout import COSMETIC_SLOTS  # noqa: E402
from models import ITEM_CURRENCY, SHOP_ITEMS  # noqa: E402
from season_config import SEASON_CONFIG  # noqa: E402


def _load_seasons():
    # Load the real seasons.py, bypassing any sys.modules stub another test installs.
    spec = importlib.util.spec_from_file_location(
        '_real_seasons_for_rv01', REPO_ROOT / 'seasons.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


seasons = _load_seasons()

UTC = timezone.utc
LONDON = ZoneInfo('Europe/London')
TEST_SEASON = 9001  # internal season_number for the DB tests; never a real season


# ── Pure helpers (no DB) ─────────────────────────────────────────────────────

@pytest.mark.parametrize('pfn, sub, season_number, expected', [
    (9, 1, TEST_SEASON, '9.1'),
    (9, 2, TEST_SEASON, '9.2'),
    (8, None, 8, '8'),
    (None, None, 7, '7'),
    (None, 2, 7, '7'),
])
def test_season_label(pfn, sub, season_number, expected):
    assert seasons.season_label(pfn, sub, season_number) == expected


ROLLOVER_CASES = [
    # Wednesday 7 Oct 2026 (BST): next is Friday 9 Oct 21:00 BST = 20:00 UTC.
    (datetime(2026, 10, 7, 12, 0, tzinfo=UTC), datetime(2026, 10, 9, 20, 0, tzinfo=UTC)),
    # Friday 20:59 BST.
    (datetime(2026, 10, 9, 19, 59, tzinfo=UTC), datetime(2026, 10, 9, 20, 0, tzinfo=UTC)),
    # Friday 21:00 BST exactly: "strictly after", so next week.
    (datetime(2026, 10, 9, 20, 0, tzinfo=UTC), datetime(2026, 10, 16, 20, 0, tzinfo=UTC)),
    # Friday 21:01 BST.
    (datetime(2026, 10, 9, 20, 1, tzinfo=UTC), datetime(2026, 10, 16, 20, 0, tzinfo=UTC)),
    # BST ends Sunday 25 Oct 2026. Friday 23 Oct is still BST (21:00 BST = 20:00 UTC).
    (datetime(2026, 10, 22, 12, 0, tzinfo=UTC), datetime(2026, 10, 23, 20, 0, tzinfo=UTC)),
    (datetime(2026, 10, 23, 19, 59, tzinfo=UTC), datetime(2026, 10, 23, 20, 0, tzinfo=UTC)),
    # Friday 23 Oct 21:00 BST: next is Friday 30 Oct, GMT, so 21:00 UTC (a naive +7d gives 20:00).
    (datetime(2026, 10, 23, 20, 0, tzinfo=UTC), datetime(2026, 10, 30, 21, 0, tzinfo=UTC)),
    (datetime(2026, 10, 24, 12, 0, tzinfo=UTC), datetime(2026, 10, 30, 21, 0, tzinfo=UTC)),
    (datetime(2026, 10, 28, 12, 0, tzinfo=UTC), datetime(2026, 10, 30, 21, 0, tzinfo=UTC)),
    # Friday 30 Oct 21:00 GMT exactly: next is Friday 6 Nov, still GMT.
    (datetime(2026, 10, 30, 21, 0, tzinfo=UTC), datetime(2026, 11, 6, 21, 0, tzinfo=UTC)),
]


@pytest.mark.parametrize('now, expected', ROLLOVER_CASES)
def test_next_rollover_after(now, expected):
    result = seasons.next_rollover_after(now)
    assert result == expected
    assert result.utcoffset() == timedelta(0)


def test_shop_page_season9_matches_season8_and_is_equippable():
    assert SHOP_ITEMS['page_season9'] == SHOP_ITEMS['page_season8']
    assert ITEM_CURRENCY['page_season9'] == 'losses'
    assert COSMETIC_SLOTS['page_season9'] == 'page_theme'


# ── DB tests (rolled back) ───────────────────────────────────────────────────

class _NoCommit:
    """advance_season() commits internally. Swallow that so the fixture's
    rollback undoes everything the test wrote."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def commit(self):
        pass

    def rollback(self):
        self._conn.rollback()


@pytest.fixture
def conn(db_url):
    raw = psycopg2.connect(db_url)
    raw.autocommit = False
    try:
        yield _NoCommit(raw)
    finally:
        raw.rollback()
        raw.close()


def _seed_season(conn, pfn, sub, name, season_number=TEST_SEASON):
    """Make the single seasons row look like the given season."""
    with conn.cursor() as cur:
        cur.execute(
            '''UPDATE seasons
               SET season_number = %s, player_facing_number = %s, sub_number = %s,
                   name = %s, started_at = NOW() - INTERVAL '1 day', ends_at = NOW()
               WHERE id = (SELECT id FROM seasons ORDER BY id LIMIT 1)''',
            (season_number, pfn, sub, name),
        )


def _season_row(conn):
    """Return (season_number, player_facing_number, sub_number, name, ends_at)."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT season_number, player_facing_number, sub_number, name, ends_at '
            'FROM seasons ORDER BY id LIMIT 1'
        )
        return cur.fetchone()


def _make_user(conn):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, password_hash, ip_address) "
            "VALUES (%s, 'x', '203.0.113.7') RETURNING id",
            (f'rv01_{uuid.uuid4().hex[:12]}',),
        )
        user_id = cur.fetchone()[0]
        cur.execute('INSERT INTO game_state (user_id) VALUES (%s)', (user_id,))
    return user_id


def _owned_items(conn, user_id):
    with conn.cursor() as cur:
        cur.execute('SELECT owned_items FROM game_state WHERE user_id = %s', (user_id,))
        return cur.fetchone()[0]


def test_launch_sets_pfn_sub_name_and_label(conn):
    _seed_season(conn, pfn=8, sub=None, name='Casino')

    seasons.advance_season(conn, 9, 'Tides', 1)

    _, pfn, sub, name, _ = _season_row(conn)
    assert (pfn, sub, name) == (9, 1, 'Tides')
    assert seasons.get_season_info(conn)['season_label'] == '9.1'


def test_no_arg_call_after_launch_gives_9_2(conn):
    _seed_season(conn, pfn=8, sub=None, name='Casino')
    seasons.advance_season(conn, 9, 'Tides', 1)

    seasons.advance_season(conn)

    _, pfn, sub, name, _ = _season_row(conn)
    assert (pfn, sub, name) == (9, 2, 'Tides')
    assert seasons.get_season_info(conn)['season_label'] == '9.2'


@pytest.mark.parametrize('pfn, sub, name, expected_label', [
    (8, None, 'Casino', '8'),
    (9, 1, 'Tides', '9.1'),
])
def test_ending_season_is_written_to_season_log(conn, pfn, sub, name, expected_label):
    _seed_season(conn, pfn=pfn, sub=sub, name=name)

    seasons.advance_season(conn)

    with conn.cursor() as cur:
        cur.execute(
            'SELECT label, name, ended_at FROM season_log WHERE season_number = %s',
            (TEST_SEASON,),
        )
        row = cur.fetchone()
    assert row is not None, 'no season_log row for the ended season'
    label, logged_name, ended_at = row
    assert label == expected_label
    assert logged_name == name
    assert ended_at is not None


def test_rollover_grants_configured_theme(conn, monkeypatch):
    monkeypatch.setitem(SEASON_CONFIG, 'theme_item', 'page_probe_theme')
    user_id = _make_user(conn)
    _seed_season(conn, pfn=9, sub=1, name='Tides')

    seasons.advance_season(conn)

    owned = _owned_items(conn, user_id)
    assert 'page_probe_theme' in owned
    assert 'page_season9' not in owned


def test_rollover_grants_page_season9_by_default(conn):
    user_id = _make_user(conn)
    _seed_season(conn, pfn=9, sub=1, name='Tides')

    seasons.advance_season(conn)

    assert 'page_season9' in _owned_items(conn, user_id)


def test_ends_at_is_next_rollover_after_now(conn, monkeypatch):
    calls = []
    real_next_rollover = seasons.next_rollover_after

    def spy(now):
        calls.append(now)
        return real_next_rollover(now)

    monkeypatch.setattr(seasons, 'next_rollover_after', spy)
    _seed_season(conn, pfn=9, sub=1, name='Tides')

    seasons.advance_season(conn)

    assert calls, 'advance_season did not call next_rollover_after'
    *_, ends_at = _season_row(conn)
    assert ends_at == real_next_rollover(calls[0])
    local = ends_at.astimezone(LONDON)
    assert (local.weekday(), local.hour, local.minute) == (4, 21, 0)


def test_season_info_exposes_sub_number_and_label(conn):
    _seed_season(conn, pfn=9, sub=2, name='Tides')

    info = seasons.get_season_info(conn)
    assert info['sub_number'] == 2
    assert info['season_label'] == '9.2'
    assert {'season_number', 'season_name', 'player_facing_number', 'ends_at',
            'latest_winners'} <= set(info)

    current = seasons.ensure_current_season(conn)
    assert current['sub_number'] == 2
    assert current['season_label'] == '9.2'
    assert current['season_name'] == 'Tides'


def _set_state(conn, user_id, **cols):
    sets = ', '.join(f'{k} = %s' for k in cols)
    with conn.cursor() as cur:
        cur.execute(f'UPDATE game_state SET {sets} WHERE user_id = %s', (*cols.values(), user_id))


def _state(conn, user_id):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute('SELECT * FROM game_state WHERE user_id = %s', (user_id,))
        return cur.fetchone()


def test_rollover_keeps_cosmetics_and_species_drops_functional(conn):
    """RV-02: cosmetics, active cosmetics, equipped skin and species persist."""
    user_id = _make_user(conn)
    _set_state(conn, user_id,
               owned_items=['trail_2', 'theme_ice', 'page_season5', 'fish_puffer',
                            'winmult_3', 'wager_unlock'],
               active_cosmetics=['trail_2', 'page_season5'],
               equipped_fish='fish_puffer', caught_species=['cod', 'eel'])
    _seed_season(conn, pfn=9, sub=1, name='Tides')

    seasons.advance_season(conn)

    gs = _state(conn, user_id)
    assert set(gs['owned_items']) == {'trail_2', 'theme_ice', 'page_season5', 'fish_puffer',
                                      'page_season9', 'auto_spin_unlock'}
    assert gs['active_cosmetics'] == ['trail_2', 'page_season5']  # own page theme kept
    assert gs['equipped_fish'] == 'fish_puffer'
    assert sorted(gs['caught_species']) == ['cod', 'eel']


def test_rollover_equips_season_theme_when_no_page_theme_active(conn):
    user_id = _make_user(conn)
    _set_state(conn, user_id, owned_items=['trail_2', 'winmult_3'],
               active_cosmetics=['trail_2', 'winmult_3'])
    _seed_season(conn, pfn=9, sub=1, name='Tides')

    seasons.advance_season(conn)

    assert _state(conn, user_id)['active_cosmetics'] == ['trail_2', 'page_season9']


def test_rollover_keeps_running_auto_spin_and_leaves_stopped_alone(conn):
    running, stopped = _make_user(conn), _make_user(conn)
    _set_state(conn, running, auto_spin_since=datetime(2026, 1, 1, tzinfo=timezone.utc))
    _set_state(conn, stopped, auto_spin_since=None)
    _seed_season(conn, pfn=9, sub=1, name='Tides')

    seasons.advance_season(conn)

    assert _state(conn, running)['auto_spin_since'] > datetime(2026, 1, 2, tzinfo=timezone.utc)
    assert _state(conn, stopped)['auto_spin_since'] is None


# ── RV-05: rollover chat message + weekly goal ───────────────────────────────

def _podium_users(conn, wins_list):
    """Zero every player's wins (rolled back), then seed real-IP users with these wins."""
    with conn.cursor() as cur:
        cur.execute('UPDATE game_state SET wins = 0')
    names = []
    for wins in wins_list:
        uid = _make_user(conn)
        with conn.cursor() as cur:
            cur.execute('UPDATE game_state SET wins = %s WHERE user_id = %s', (wins, uid))
            cur.execute('SELECT username FROM users WHERE id = %s', (uid,))
            names.append(cur.fetchone()[0])
    return names


def _tide_messages(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT message FROM chat_messages WHERE message LIKE '🌊 Tide %' ORDER BY id")
        return [r[0] for r in cur.fetchall()]


def test_tide_rollover_posts_podium_message_every_time(conn):
    _seed_season(conn, pfn=9, sub=1, name='Tides')
    first, second, third = _podium_users(conn, [300, 200, 100])
    before = len(_tide_messages(conn))

    seasons.advance_season(conn)
    seasons.advance_season(conn)  # within the 30 s throttle window: must still post

    msgs = _tide_messages(conn)[before:]
    assert msgs[0] == (f'🌊 Tide 9.1 has turned! 🥇 {first} · 🥈 {second} · 🥉 {third}'
                       ' — Tide 9.2 starts now. Good luck!')
    assert msgs[1] == '🌊 Tide 9.2 has turned! — Tide 9.3 starts now. Good luck!'


def test_launch_from_whole_season_posts_no_tide_message(conn):
    _seed_season(conn, pfn=8, sub=None, name='Casino')
    before = len(_tide_messages(conn))

    seasons.advance_season(conn, 9, 'Tides', 1)

    assert len(_tide_messages(conn)) == before


def test_rollover_starts_a_goal_for_the_new_tide(conn):
    _seed_season(conn, pfn=9, sub=1, name='Tides')

    seasons.advance_season(conn)

    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM community_goals WHERE season_number = %s',
                    (TEST_SEASON + 1,))
        assert cur.fetchone()[0] == 1
