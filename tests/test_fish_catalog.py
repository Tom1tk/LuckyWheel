"""Season 9 D3: the 46-species catalog, availability, size, records and Surge
earned at every catch site (docs/SEASON_9_DEEP_SPEC.md §4–6, §13)."""
import datetime as dt
import random
from collections import Counter
from datetime import timezone

import sys

import pytest

import fish
import fish_catalog as fc
import talents
from fish_catalog import FISH_CATALOG
from tests.test_charts import _chart, _get, _reset, _set, user  # noqa: F401
from tests.test_spin_integration import _read_csrf, game_app  # noqa: F401

ORIGINALS = {'minnow': 1, 'shrimp': 2, 'clownfish': 3, 'pufferfish': 3, 'crab': 8, 'squid': 8,
             'octopus': 12, 'lobster': 20, 'dolphin': 30, 'shark': 40, 'whale': 75,
             'mermaid': 120, 'lucky': 100}


def _bst(h, m=0):
    """A Friday in October (BST = UTC+1) at London h:m."""
    return dt.datetime(2026, 10, 9, h, m, tzinfo=timezone.utc) - dt.timedelta(hours=1)


# ══════════════════════════════════════════════════════════════════════════
# A. Catalog data
# ══════════════════════════════════════════════════════════════════════════

def test_46_species_and_originals_unchanged():
    assert len(FISH_CATALOG) == 46
    for sid, value in ORIGINALS.items():
        f = FISH_CATALOG[sid]
        assert f['value'] == value
        assert f['windows'] is None and f['tide'] is None and f['migrant'] is None


@pytest.mark.parametrize('sid', sorted(FISH_CATALOG))
def test_every_field_is_valid(sid):
    f = FISH_CATALOG[sid]
    assert f['rarity'] in fc.RARITIES and f['tier'] == f['rarity'].capitalize()
    assert f['weight'] > 0 and f['emoji'] and f['name'] and f['hint']
    lo, hi = f['kg']
    assert 0 < lo < hi
    assert (f['value'] == 0) == (f['rarity'] == 'junk')
    assert f['windows'] is None or (f['windows'] and set(f['windows']) <= set(fc.WINDOWS))
    assert f['tide'] in (None, 'high', 'low')
    assert f['migrant'] in (None, 0, 1, 2, 3)
    assert 0 <= f['hue'] < 360


def test_two_migrants_per_slot():
    slots = Counter(f['migrant'] for f in FISH_CATALOG.values() if f['migrant'] is not None)
    assert slots == {0: 2, 1: 2, 2: 2, 3: 2}


# ══════════════════════════════════════════════════════════════════════════
# B. When they bite
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize('h,m,window', [
    (4, 59, 'night'), (5, 0, 'dawn'), (8, 59, 'dawn'), (9, 0, 'day'), (16, 59, 'day'),
    (17, 0, 'dusk'), (20, 59, 'dusk'), (21, 0, 'night'), (0, 0, 'night')])
def test_day_window_uses_london_time(h, m, window):
    assert fc.day_window(_bst(h, m)) == window


def test_tide_alternates_every_6h12m30s_from_a_high_epoch():
    p = dt.timedelta(seconds=fc.TIDE_PERIOD_S)
    assert fc.TIDE_PERIOD_S == 22350
    assert fc.tide(fc.TIDE_EPOCH) == ('high', 22350)
    assert fc.tide(fc.TIDE_EPOCH + p - dt.timedelta(seconds=1)) == ('high', 1)
    assert fc.tide(fc.TIDE_EPOCH + p)[0] == 'low'
    assert fc.tide(fc.TIDE_EPOCH + 2 * p)[0] == 'high'
    assert fc.tide(fc.TIDE_EPOCH + 3 * p + dt.timedelta(seconds=100)) == ('low', 22250)


def _at(window_hour, tide_phase):
    """A London time in the given hour whose tide is ``tide_phase``."""
    t = _bst(window_hour)
    while fc.tide(t)[0] != tide_phase or fc.day_window(t) != fc.day_window(_bst(window_hour)):
        t += dt.timedelta(days=1)
    return t


def test_availability_needs_every_condition():
    day_low, day_high = _at(12, 'low'), _at(12, 'high')
    night_low, night_high = _at(2, 'low'), _at(2, 'high')
    assert fc.is_available('mudskipper', day_low)
    assert not fc.is_available('mudskipper', day_high)
    assert not fc.is_available('mudskipper', night_low)
    assert fc.is_available('kraken', night_high) and not fc.is_available('kraken', night_low)
    assert fc.is_available('ghost_ship', night_low) and not fc.is_available('ghost_ship', day_low)
    assert fc.is_available('sea_dragon', _bst(6)) and not fc.is_available('sea_dragon', _bst(10))


def test_migrants_only_in_their_slot(monkeypatch):
    for slot in range(4):
        monkeypatch.setattr(fc, 'get_week_number', lambda now, s=slot: 40 + s)
        here = {sid for sid, f in FISH_CATALOG.items()
                if f['migrant'] is not None and fc.is_available(sid, _bst(12))}
        assert here == {sid for sid, f in FISH_CATALOG.items() if f['migrant'] == (40 + slot) % 4}


SAMPLE_TIMES = [_bst(h) + dt.timedelta(hours=6.2 * k) for h in (2, 6, 12, 18) for k in range(2)]


@pytest.mark.parametrize('now', SAMPLE_TIMES)
def test_roll_never_returns_an_unavailable_species(now):
    random.seed(1)
    for kw in ({'auto_mode': False}, {'auto_mode': True}, {'auto_mode': True, 'allow_rare': True},
               {'auto_mode': False, 'deep_sea': True, 'happy_hour': True}):
        for _ in range(300):
            assert fc.is_available(fc.roll_fish(now=now, **kw), now)


def test_auto_never_legendary_and_rare_only_with_old_salt():
    random.seed(2)
    now = _bst(12)
    plain = Counter(FISH_CATALOG[fc.roll_fish(True, now=now)]['rarity'] for _ in range(3000))
    salt = Counter(FISH_CATALOG[fc.roll_fish(True, allow_rare=True, now=now)]['rarity'] for _ in range(3000))
    assert not plain['legendary'] and not plain['rare']
    assert not salt['legendary'] and salt['rare'] > 0


def test_deep_sea_only_the_big_ones():
    random.seed(3)
    now = _bst(12)
    deep = Counter(FISH_CATALOG[fc.roll_fish(False, now=now, deep_sea=True)]['rarity'] for _ in range(4000))
    normal = Counter(FISH_CATALOG[fc.roll_fish(False, now=now)]['rarity'] for _ in range(4000))
    assert not deep['junk'] and not deep['common']
    assert deep['rare'] / 4000 > 3 * normal['rare'] / 4000


# ══════════════════════════════════════════════════════════════════════════
# C. Size, records, Surge
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize('quality', [-1, 0, 0.5, 1, 7])
def test_kg_within_bounds_and_quality_clamped(quality):
    rng = random.Random(4)
    for sid in ('minnow', 'whale', 'ghost_ship'):
        lo, hi = FISH_CATALOG[sid]['kg']
        for _ in range(200):
            kg, ratio = fc.roll_kg(sid, quality, rng)
            assert lo <= kg <= hi and 0 <= ratio <= 1
            if quality >= 1:
                assert ratio >= 0.5


def test_records_only_go_up():
    r, new = fc.update_records({}, 'crab', 1.5)
    assert r == {'crab': 1.5} and new
    r2, new2 = fc.update_records(r, 'crab', 1.2)
    assert r2 == {'crab': 1.5} and not new2
    r3, new3 = fc.update_records(r2, 'crab', 2.0)
    assert r3 == {'crab': 2.0} and new3 and r2 == {'crab': 1.5}


@pytest.mark.parametrize('rarity,ratio,expected', [
    ('junk', 1.0, 0), ('common', 0.5, 6), ('uncommon', 0.5, 15), ('rare', 0.5, 40),
    ('legendary', 0.5, 150), ('legendary', 1.0, 225), ('common', 0.0, 3)])
def test_manual_surge_table(rarity, ratio, expected):
    assert talents.catch_surge({}, rarity, ratio, auto=False) == expected


def test_auto_surge_is_a_quarter_with_a_floor_of_one():
    assert talents.catch_surge({}, 'common', 0.0, auto=True) == 1   # 0.75 → 1
    assert talents.catch_surge({}, 'rare', 0.5, auto=True) == 10
    assert talents.catch_surge({}, 'junk', 1.0, auto=True) == 0


def test_better_bait_adds_25_percent_per_rank_and_rogue_wave_earns_nothing():
    assert talents.catch_surge({'better_bait': 2}, 'rare', 0.5, auto=False) == 60
    assert talents.catch_surge({'rogue_wave': 1}, 'legendary', 1.0, auto=False) == 0
    assert talents.catch_surge({'rogue_wave': 1}, 'common', 1.0, auto=True) == 0


def test_size_up_scales_value_and_junk_is_worthless():
    random.seed(5)
    junk = fish.size_up_catch('old_boot', 0, 1.0, {}, {}, auto=False)
    assert junk['value'] == 0 and junk['surge'] == 0
    for _ in range(100):
        c = fish.size_up_catch('shark', 40, 0.5, {}, {}, auto=False)
        assert 20 <= c['value'] <= 60 and c['new_record']


# ══════════════════════════════════════════════════════════════════════════
# D. Live routes (wheeldb_test)
# ══════════════════════════════════════════════════════════════════════════

def _land_shark(client, db_url, username):
    _set(db_url, username, fishing_species='shark', fish_records={},
         fishing_hooked_at=dt.datetime.now(timezone.utc) - dt.timedelta(seconds=7))
    return client.post('/api/land', json={'landed': True, 'quality': 0.5},
                       headers={'X-CSRFToken': _read_csrf(client)}).get_json()


def test_land_earns_surge_and_sets_a_record(user, db_url):
    client, username = user
    body = _land_shark(client, db_url, username)
    assert body['result'] == 'hit' and body['rarity'] == 'rare' and body['new_record']
    assert 20 <= body['surge'] <= 60
    gs = _get(db_url, username)
    assert gs['surge_spins'] == body['surge']
    assert gs['fish_records'] == {'shark': body['kg']}


def test_rogue_wave_land_earns_no_surge(user, db_url):
    client, username = user
    _chart(client, {'open_water': 1, 'loaded_dice': 3, 'treasure': 1, 'deep_water': 1, 'rogue_wave': 1})
    body = _land_shark(client, db_url, username)
    assert body['result'] == 'hit' and body['surge'] == 0
    assert _get(db_url, username)['surge_spins'] == 0


DECKHAND = {'rich_waters': 2, 'deckhand': 1}
DECKHAND_ROGUE = {'loaded_dice': 3, 'treasure': 1, 'open_water': 1, 'deep_water': 1, 'rogue_wave': 1}


@pytest.mark.parametrize('rogue', [False, True])
def test_auto_fish_tick_earns_a_quarter(user, db_url, monkeypatch, rogue):
    client, username = user
    _chart(client, DECKHAND)
    if rogue:  # Rogue Wave can't reach Deckhand; grant the autofisher directly.
        _chart(client, {})
        _set(db_url, username, talent_alloc=DECKHAND_ROGUE, owned_items=['autofisher_1'])
    _set(db_url, username, auto_fish_last_tick=None)
    monkeypatch.setattr(fish, 'roll_fish', lambda **k: 'crab')
    monkeypatch.setattr(fish, 'autofisher_catch_rate', lambda lvl: 1.0)
    body = client.post('/api/auto-fish-tick', json={}, headers={'X-CSRFToken': _read_csrf(client)}).get_json()
    assert body['result'] == 'hit' and body['rarity'] == 'uncommon'
    if rogue:
        assert body['surge'] == 0
    else:
        assert 2 <= body['surge'] <= 6  # round(15 × [0.5, 1.5] × 0.25)
    assert _get(db_url, username)['surge_spins'] == body['surge']


@pytest.mark.parametrize('rogue', [False, True])
def test_afk_catch_up_earns_surge_and_records(user, db_url, monkeypatch, rogue):
    client, username = user
    _set(db_url, username, owned_items=['auto_spin_unlock', 'autofisher_1'],
         talent_alloc=DECKHAND_ROGUE if rogue else DECKHAND)
    past = dt.datetime.now(timezone.utc) - dt.timedelta(seconds=10)
    _set(db_url, username, auto_spin_since=past, last_spin_at=past, auto_fish_enabled=True,
         auto_fish_last_tick=dt.datetime.now(timezone.utc) - dt.timedelta(seconds=61), fish_records={})
    game = sys.modules['game']  # game_app re-imports it; patch the live copy
    monkeypatch.setattr(game, 'roll_fish', lambda **k: 'crab')
    monkeypatch.setattr(game, 'autofisher_catch_rate', lambda lvl: 1.0)
    r = client.post('/api/tick', json={}, headers={'X-CSRFToken': _read_csrf(client)})
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    catch = data['fish_catchup']
    assert catch['fish_count'] == 10
    gs = _get(db_url, username)
    if rogue:
        assert catch['surge'] == 0
    else:
        assert 20 <= catch['surge'] <= 60
    # Auto-spins spend surge before the catch-up adds it.
    assert gs['surge_spins'] == catch['surge'] == data['state']['surge_spins']
    assert set(gs['fish_records']) == {'crab'}


def test_fish_catalog_route(user):
    client, _ = user
    body = client.get('/api/fish-catalog').get_json()
    assert len(body['species']) == 46
    assert body['tide'] in ('high', 'low') and 0 < body['tide_turns_in_s'] <= fc.TIDE_PERIOD_S
    assert body['window'] in fc.WINDOWS and body['migrant_slot'] in range(4)
    by_id = {s['id']: s for s in body['species']}
    assert all(by_id[sid]['biting_now'] for sid in ORIGINALS)
    assert by_id['kraken']['windows'] == ['night'] and by_id['kraken']['tide'] == 'high'
