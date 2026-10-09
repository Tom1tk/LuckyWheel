"""Season 9 fish catalog: 46 species, when they bite, and how big they are
(docs/SEASON_9_DEEP_SPEC.md §6).

The 13 original ids keep their names and values and are always available.
Newer species bite only in their London time ``window`` and/or ``tide``;
migrants only in their slot (tide week % 4).
"""
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from wheel_modes import get_week_number

_LONDON = ZoneInfo('Europe/London')

TIDE_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)   # a high tide
TIDE_PERIOD_S = 6 * 3600 + 12 * 60 + 30                    # 6h 12m 30s
MIGRANT_SLOTS = 4
DEEP_SEA_BIG_MULT = 3.0
DEEP_SEA_BITE_MULT = 1.5
RARITIES = ('junk', 'common', 'uncommon', 'rare', 'legendary')
WINDOWS = ('dawn', 'day', 'dusk', 'night')


def _f(emoji, name, rarity, weight, value, kg, hint, hue=0, win=None, tide=None, migrant=None):
    return {'emoji': emoji, 'name': name, 'rarity': rarity, 'tier': rarity.capitalize(),
            'weight': weight, 'value': value, 'kg': kg, 'hint': hint, 'hue': hue,
            'windows': win, 'tide': tide, 'migrant': migrant}


FISH_CATALOG = {
    'old_boot':       _f('👢', 'Old Boot', 'junk', 4, 0, (0.5, 1.5), 'Someone walked home with one shoe.'),
    'tin_can':        _f('🥫', 'Tin Can', 'junk', 3, 0, (0.1, 0.4), 'Please recycle.'),
    'minnow':         _f('🐟', 'Minnow', 'common', 14, 1, (0.01, 0.05), 'Everywhere, always.'),
    'shrimp':         _f('🦐', 'Shrimp', 'common', 7, 2, (0.01, 0.04), 'Small, but it counts.'),
    'clownfish':      _f('🐠', 'Clownfish', 'common', 7, 3, (0.1, 0.3), 'Lives in the reef.'),
    'pufferfish':     _f('🐡', 'Pufferfish', 'common', 6, 3, (0.2, 1.0), "Don't squeeze."),
    'sardine':        _f('🐟', 'Sardine', 'common', 7, 2, (0.05, 0.15), 'Swims in thousands.', hue=180),
    'mackerel':       _f('🐟', 'Mackerel', 'common', 6, 3, (0.3, 1.2), 'Bites in daylight.', hue=90, win={'day'}),
    'sea_snail':      _f('🐌', 'Sea Snail', 'common', 4, 2, (0.02, 0.1), 'Clings to rocks the tide uncovers.', tide='low'),
    'hermit_crab':    _f('🐚', 'Hermit Crab', 'common', 4, 3, (0.05, 0.3), 'Look in the rock pools.', tide='low'),
    'mudskipper':     _f('🐸', 'Mudskipper', 'common', 3, 4, (0.05, 0.2), 'Walks the mud flats in the sun.', win={'day'}, tide='low'),
    'crab':           _f('🦀', 'Crab', 'uncommon', 6, 8, (0.5, 3), 'Sideways and stubborn.'),
    'squid':          _f('🦑', 'Squid', 'uncommon', 5, 8, (0.3, 4), 'Ink and arms.'),
    'octopus':        _f('🐙', 'Octopus', 'uncommon', 3, 12, (1, 15), 'Too clever for most lines.'),
    'moon_jelly':     _f('🎐', 'Moon Jelly', 'uncommon', 3, 10, (0.2, 2), 'Glows after dark.', win={'night'}),
    'sea_turtle':     _f('🐢', 'Sea Turtle', 'uncommon', 2, 14, (20, 150), 'Rides the high tide in daylight.', win={'day'}, tide='high'),
    'moray_eel':      _f('🐍', 'Moray Eel', 'uncommon', 2, 12, (2, 30), 'Hunts at night.', win={'night'}),
    'parrotfish':     _f('🐠', 'Parrotfish', 'uncommon', 2.5, 10, (1, 9), 'Crunches coral by day.', hue=120, win={'day'}),
    'lionfish':       _f('🐡', 'Lionfish', 'uncommon', 2, 12, (0.5, 1.4), 'Comes out as the light goes.', hue=300, win={'dusk'}),
    'flounder':       _f('🐟', 'Flounder', 'uncommon', 2.5, 9, (0.5, 5), "Flat on the sand when the water's shallow.", hue=30, tide='low'),
    'pearl_oyster':   _f('🦪', 'Pearl Oyster', 'uncommon', 2, 15, (0.1, 0.5), 'Opens at first light.', win={'dawn'}),
    'lobster':        _f('🦞', 'Lobster', 'rare', 3, 20, (0.5, 9), 'Heavy claws.'),
    'dolphin':        _f('🐬', 'Dolphin', 'rare', 1.5, 30, (70, 300), 'Friendly, fast.'),
    'shark':          _f('🦈', 'Shark', 'rare', 1.2, 40, (50, 900), 'Bring a bigger rod.'),
    'grey_seal':      _f('🦭', 'Grey Seal', 'rare', 1.2, 30, (100, 300), 'Comes in on the high water.', tide='high'),
    'swordfish':      _f('🐟', 'Swordfish', 'rare', 1, 35, (50, 650), 'Fast in the sunlit water.', hue=200, win={'day'}),
    'hammerhead':     _f('🦈', 'Hammerhead', 'rare', 0.8, 45, (200, 500), 'Patrols at dusk.', hue=60, win={'dusk'}),
    'anglerfish':     _f('🏮', 'Anglerfish', 'rare', 0.8, 35, (0.5, 50), 'Follow the little light.', win={'night'}),
    'sunken_chest':   _f('🧰', 'Sunken Chest', 'rare', 0.6, 60, (5, 40), 'Glints at dawn.', win={'dawn'}),
    'message_bottle': _f('🍾', 'Message in a Bottle', 'rare', 0.8, 25, (0.5, 1), 'Drifts in with the evening.', win={'dusk'}),
    'orca':           _f('🐳', 'Orca', 'rare', 0.6, 50, (3000, 6000), 'Hunts the high tide.', tide='high'),
    'whale':          _f('🐋', 'Blue Whale', 'legendary', 0.4, 75, (50000, 150000), 'The biggest thing alive.'),
    'mermaid':        _f('🧜', 'Mermaid', 'legendary', 0.15, 120, (50, 90), "Sailors' stories are true."),
    'lucky':          _f('⭐', 'Lucky Fish', 'legendary', 0.25, 100, (0.1, 1), 'Doubles your next catch.'),
    'kraken':         _f('🦑', 'Kraken', 'legendary', 0.12, 150, (500, 2000), 'High water, dead of night.', hue=330, win={'night'}, tide='high'),
    'sea_dragon':     _f('🐉', 'Sea Dragon', 'legendary', 0.1, 180, (100, 900), 'Seen once at sunrise.', win={'dawn'}),
    'golden_koi':     _f('🐠', 'Golden Koi', 'legendary', 0.12, 140, (2, 12), 'Gold in the last light.', hue=40, win={'dusk'}),
    'ghost_ship':     _f('🏴‍☠️', 'Ghost Ship', 'legendary', 0.08, 200, (100000, 300000), 'Low tide, no moon, no crew.', win={'night'}, tide='low'),
    'narwhal':        _f('🦄', 'Narwhal', 'rare', 0.8, 45, (800, 1600), 'Visits every fourth tide.', migrant=0),
    'sea_otter':      _f('🦦', 'Sea Otter', 'uncommon', 2, 14, (14, 45), 'Visits every fourth tide.', migrant=0),
    'leatherback':    _f('🐢', 'Leatherback', 'rare', 0.8, 40, (250, 700), 'Visits every fourth tide.', hue=200, migrant=1),
    'penguin':        _f('🐧', 'Penguin', 'uncommon', 2, 12, (1, 30), 'Visits every fourth tide.', migrant=1),
    'ocean_sunfish':  _f('🌞', 'Ocean Sunfish', 'rare', 0.8, 45, (250, 1000), 'Visits every fourth tide.', migrant=2),
    'saltwater_croc': _f('🐊', 'Saltwater Croc', 'rare', 0.6, 50, (200, 1000), 'Visits every fourth tide.', migrant=2),
    'blue_marlin':    _f('🐟', 'Blue Marlin', 'rare', 0.7, 45, (100, 800), 'Visits every fourth tide.', hue=220, migrant=3),
    'coelacanth':     _f('🐟', 'Coelacanth', 'rare', 0.5, 60, (30, 90), 'Visits every fourth tide.', hue=260, migrant=3),
}


def day_window(now: datetime) -> str:
    h = now.astimezone(_LONDON).hour
    return 'dawn' if 5 <= h < 9 else 'day' if 9 <= h < 17 else 'dusk' if 17 <= h < 21 else 'night'


def tide(now: datetime) -> tuple[str, int]:
    """('high'|'low', seconds until it turns)."""
    elapsed = int((now - TIDE_EPOCH).total_seconds())
    phase, into = divmod(elapsed, TIDE_PERIOD_S)
    return ('high' if phase % 2 == 0 else 'low'), TIDE_PERIOD_S - into


def migrant_slot(now: datetime) -> int:
    return get_week_number(now) % MIGRANT_SLOTS


def is_available(sid: str, now: datetime) -> bool:
    f = FISH_CATALOG[sid]
    return ((f['windows'] is None or day_window(now) in f['windows'])
            and (f['tide'] is None or tide(now)[0] == f['tide'])
            and (f['migrant'] is None or migrant_slot(now) == f['migrant']))


def roll_fish(auto_mode: bool, allow_rare: bool = False, master_lure: bool = False,
              happy_hour: bool = False, now: datetime = None, deep_sea: bool = False) -> str:
    """Weighted pick among species biting at ``now``.

    Auto never catches legendaries, and rares only with ``allow_rare``.
    Deep Sea: no junk/common, rare and legendary ×3. ``master_lure`` adds +1
    and ``happy_hour`` +50% to legendary weights (manual only).
    """
    now = now or datetime.now(timezone.utc)
    ids, weights = [], []
    for sid, f in FISH_CATALOG.items():
        r = f['rarity']
        if not is_available(sid, now):
            continue
        if auto_mode and (r == 'legendary' or (r == 'rare' and not allow_rare)):
            continue
        if deep_sea and r in ('junk', 'common'):
            continue
        w = f['weight']
        if deep_sea and r in ('rare', 'legendary'):
            w *= DEEP_SEA_BIG_MULT
        if not auto_mode and r == 'legendary':
            w += (1.0 if master_lure else 0.0) + (f['weight'] * 0.5 if happy_hour else 0.0)
        ids.append(sid)
        weights.append(w)
    return random.choices(ids, weights=weights, k=1)[0]


def roll_kg(sid: str, quality: float, rand=random) -> tuple[float, float]:
    """(kg, size_ratio). Half luck, half catch quality in [0, 1]."""
    lo, hi = FISH_CATALOG[sid]['kg']
    ratio = 0.5 * rand.random() + 0.5 * min(1.0, max(0.0, quality))
    return round(lo + (hi - lo) * ratio, 3), ratio


def update_records(records: dict, sid: str, kg: float) -> tuple[dict, bool]:
    """New records dict and whether ``kg`` beat the old best."""
    if kg <= float((records or {}).get(sid, 0)):
        return dict(records or {}), False
    return {**(records or {}), sid: kg}, True


def catalog_payload(now: datetime) -> dict:
    phase, turns_in = tide(now)
    return {
        'tide': phase, 'tide_turns_in_s': turns_in,
        'window': day_window(now), 'migrant_slot': migrant_slot(now),
        'species': [
            {'id': sid, 'emoji': f['emoji'], 'hue': f['hue'], 'name': f['name'],
             'rarity': f['rarity'], 'value': f['value'], 'kg': list(f['kg']), 'hint': f['hint'],
             'windows': sorted(f['windows'], key=WINDOWS.index) if f['windows'] else None,
             'tide': f['tide'], 'migrant': f['migrant'], 'biting_now': is_available(sid, now)}
            for sid, f in FISH_CATALOG.items()
        ],
    }
