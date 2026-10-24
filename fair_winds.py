"""Fair Winds (Tide 9.4): once a London day, pick one of three small boons.

A boon works from the moment it's picked until the next London midnight, and only
on spins timed in that window, so offline catch-up spins from before the pick
don't get it. It lives in its own columns, never in owned_items or talent_alloc.
"""
import random
from datetime import datetime

import talents

HIGH_WATER_MULT = 1.5
BORROWABLE = ('treasure', 'echo', 'fortune_charm', 'steady_keel')
BOONS = {
    'high_water':   {'icon': '🐚', 'name': 'High Water',   'desc': '🎣 Surge spins pay ×1.5'},
    'spare_change': {'icon': '🪙', 'name': 'Spare Change', 'desc': '+1 🪙 chip now, even past the cap'},
}
_BORROW = 'borrow:'


def offers(user_id: int, alloc: dict, day) -> list:
    """Today's offers: always High Water and Spare Change, plus one talent the
    player hasn't charted, the same all day for a given Chart."""
    missing = [t for t in BORROWABLE if talents.rank(alloc, t) == 0]
    picks = ['high_water', 'spare_change']
    if missing:
        picks.append(_BORROW + random.Random(f'{user_id}:{day}').choice(missing))
    return picks


def describe(boon: str) -> dict:
    if boon.startswith(_BORROW):
        t = boon[len(_BORROW):]
        return {'id': boon, 'icon': talents.ICONS[t], 'name': f"Borrowed {talents.TALENTS[t]['name']}",
                'desc': talents.TALENTS[t]['desc'][0]}
    return {'id': boon, **BOONS[boon]}


def picked_today(gs: dict, now: datetime) -> bool:
    at = gs.get('fair_winds_at')
    return bool(at) and talents.london_date(at) == talents.london_date(now)


def active(gs: dict, at: datetime):
    """The boon in force for a spin timed at `at`, or None."""
    picked = gs.get('fair_winds_at')
    if gs.get('fair_winds_boon') and picked and picked <= at and talents.london_date(picked) == talents.london_date(at):
        return gs['fair_winds_boon']
    return None


def borrowed_item(boon):
    if boon and boon.startswith(_BORROW):
        return talents.TALENTS[boon[len(_BORROW):]]['grants'][0][0]
    return None


def lend(owned: list, boon):
    """Owned list for one spin with any borrowed talent added, and the item to
    strip from the result (None when nothing was lent)."""
    item = borrowed_item(boon)
    if item and item not in owned:
        return owned + [item], item
    return owned, None


def payload(user_id: int, gs: dict, now: datetime) -> dict:
    day = talents.london_date(now)
    if picked_today(gs, now):
        return {'day': day.isoformat(), 'picked': describe(gs['fair_winds_boon']), 'offers': []}
    return {'day': day.isoformat(), 'picked': None,
            'offers': [describe(b) for b in offers(user_id, gs.get('talent_alloc'), day)]}
