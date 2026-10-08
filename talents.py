"""Season 9 Charts: a limited-points talent system (docs/SEASON_9_DEEP_SPEC.md §3).

A Chart is ``{talent_id: rank}``. Ranks grant existing shop item ids into
``owned_items`` so ``_resolve_spin`` and the fishing helpers keep reading
``'item' in owned``. Talents with no item (Rich Waters, Steady Hands,
keystones) are read from the Chart directly via ``rank()`` / ``keystone()``.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from models import ITEM_CURRENCY

_LONDON = ZoneInfo('Europe/London')

# ── Tuned numbers (balance table: SEASON_9_DEEP_SPEC.md §8) ───────────────
BASE_POINTS = 4            # day 0 of a tide
MAX_POINTS = 10            # reached on the tide's last day (day 6)
ROW_GATE = {1: 0, 2: 2, 3: 4}   # points already in the tree to unlock a row
KEYSTONE_GATE = 6
SURGE_MULT_BY_RICH_WATERS = {0: 5, 1: 25, 2: 50, 3: 100}
SURGE_BAIT_BONUS_PER_RANK = 0.25

TREES = {
    'swell':   {'name': '🌊 Swell',   'motto': 'ride the streak'},
    'riptide': {'name': '🌀 Riptide', 'motto': 'bet the tide'},
    'angler':  {'name': '🎣 Angler',  'motto': 'read the water'},
}

# grants[i] = items added at rank i+1 (rank n grants grants[0..n-1]).
# row 'K' = keystone. Order here is the display order.
TALENTS = {
    # 🌊 Swell
    'undertow':      {'tree': 'swell', 'row': 1, 'name': 'Undertow', 'grants': [['bonusmult_1'], ['bonusmult_2'], ['bonusmult_3']],
                      'desc': ['Streak bonuses ×2', 'Streak bonuses ×4', 'Streak bonuses ×8']},
    'rising_tide':   {'tree': 'swell', 'row': 1, 'name': 'Rising Tide', 'grants': [['winmult_1'], ['winmult_2']],
                      'desc': ['Every win pays ×2', 'Every win pays ×4']},
    'steady_keel':   {'tree': 'swell', 'row': 2, 'name': 'Steady Keel', 'grants': [['resilience']],
                      'desc': ['Sometimes a loss only knocks your streak back one']},
    'fortune_charm': {'tree': 'swell', 'row': 2, 'name': 'Fortune Charm', 'grants': [['fortune_charm']],
                      'desc': ['Streak bonuses sometimes pay +25%']},
    'echo':          {'tree': 'swell', 'row': 2, 'name': 'Echo', 'grants': [['win_echo']],
                      'desc': ['Wins sometimes pay twice']},
    'breakwater':    {'tree': 'swell', 'row': 3, 'name': 'Breakwater', 'grants': [['regen_shield']],
                      'desc': ['Blocks one loss, recharges after 25 wins']},
    'spring_tide':   {'tree': 'swell', 'row': 'K', 'name': 'Spring Tide', 'grants': [[]],
                      'desc': ["Streak bonuses ×2 again — but you can't stake or roll dice"]},
    # 🌀 Riptide
    'open_water':    {'tree': 'riptide', 'row': 1, 'name': 'Open Water', 'grants': [['wager_unlock']],
                      'desc': ['Stake up to 30% of your wins. Each staked spin costs 1 🪙']},
    'loaded_dice':   {'tree': 'riptide', 'row': 1, 'name': 'Loaded Dice',
                      'grants': [['dice_charge_2'], ['dice_charge_3'], ['dice_charge_4']],
                      'desc': ['Hold 2 dice charges', 'Hold 3 dice charges', 'Hold 4 dice charges']},
    'deep_water':    {'tree': 'riptide', 'row': 2, 'name': 'Deep Water', 'requires': 'open_water',
                      'grants': [['wager_stake_extend_1'], ['wager_stake_extend_2']],
                      'desc': ['Stake up to 35%', 'Stake up to 40%']},
    'treasure':      {'tree': 'riptide', 'row': 2, 'name': 'Treasure', 'grants': [['jackpot']],
                      'desc': ['1% of wins are jackpots: ×25, or ×5 on a staked spin']},
    'safety_line':   {'tree': 'riptide', 'row': 2, 'name': 'Safety Line', 'requires': 'open_water',
                      'grants': [['wager_safety_net', 'wager_insurance']],
                      'desc': ['Staked losses refund a little; arm insurance once a day']},
    'third_die':     {'tree': 'riptide', 'row': 3, 'name': 'Third Die', 'grants': [['dice_extra']],
                      'desc': ['Roll three dice']},
    'double_or_nothing': {'tree': 'riptide', 'row': 3, 'name': 'Double or Nothing', 'requires': 'open_water',
                      'grants': [['wager_double_down']],
                      'desc': ['Re-stake your last win in one go']},
    'rogue_wave':    {'tree': 'riptide', 'row': 'K', 'name': 'Rogue Wave', 'grants': [[]],
                      'desc': ['Dice come back twice as fast and stack two higher — but no 🎣 Surge for you']},
    # 🎣 Angler
    'rich_waters':   {'tree': 'angler', 'row': 1, 'name': 'Rich Waters', 'grants': [[], [], []],
                      'desc': ['Surge spins pay ×25 (base ×5)', 'Surge spins pay ×50', 'Surge spins pay ×100']},
    'better_bait':   {'tree': 'angler', 'row': 1, 'name': 'Better Bait', 'grants': [['lure_1', 'lure_2'], ['lure_3']],
                      'desc': ['Faster bites, bigger catches, +25% Surge', 'Even faster, even bigger, +50% Surge']},
    'deckhand':      {'tree': 'angler', 'row': 2, 'name': 'Deckhand', 'grants': [['autofisher_1'], ['autofisher_2']],
                      'desc': ["Auto-fish while you're away", 'Auto-fish catches more often']},
    'steady_hands':  {'tree': 'angler', 'row': 2, 'name': 'Steady Hands', 'grants': [[]],
                      'desc': ['A wider sweet zone in the fight']},
    'auto_cast':     {'tree': 'angler', 'row': 2, 'name': 'Auto-Cast', 'grants': [['auto_cast']],
                      'desc': ['Recast automatically']},
    'old_salt':      {'tree': 'angler', 'row': 3, 'name': 'Old Salt', 'requires': 'deckhand',
                      'grants': [['autofisher_3', 'autofisher_4']],
                      'desc': ['Auto-fish catches rares, and more often']},
    'deep_sea':      {'tree': 'angler', 'row': 'K', 'name': 'Deep Sea', 'grants': [[]],
                      'desc': ['Only the big ones bite — and they take their time']},
}
KEYSTONES = frozenset(t for t, d in TALENTS.items() if d['row'] == 'K')
GRANTABLE = frozenset(i for d in TALENTS.values() for g in d['grants'] for i in g)
# Gear that a Chart replaces: every wins-priced item except universal auto-spin.
CHART_REPLACES = frozenset(i for i, c in ITEM_CURRENCY.items() if c == 'wins') - {'auto_spin_unlock'}
assert GRANTABLE <= CHART_REPLACES, GRANTABLE - CHART_REPLACES


def london_date(now: datetime):
    return now.astimezone(_LONDON).date()


def tide_day(now: datetime) -> int:
    """Days since the tide turned (Fri 21:00 London) → 0..6."""
    london = now.astimezone(_LONDON).replace(tzinfo=None)
    return (london + timedelta(days=2, hours=3)).weekday()


def points_total(now: datetime) -> int:
    return min(MAX_POINTS, BASE_POINTS + tide_day(now))


def rank(alloc: dict, talent_id: str) -> int:
    return int((alloc or {}).get(talent_id, 0))


def keystone(alloc: dict):
    return next((k for k in KEYSTONES if rank(alloc, k) > 0), None)


def surge_mult(alloc: dict) -> int:
    return SURGE_MULT_BY_RICH_WATERS[rank(alloc, 'rich_waters')]


def surge_bonus(alloc: dict) -> float:
    return 1.0 + SURGE_BAIT_BONUS_PER_RANK * rank(alloc, 'better_bait')


def max_rank(talent_id: str) -> int:
    return len(TALENTS[talent_id]['grants'])


def validate(alloc, points: int):
    """Return an error string, or None if ``alloc`` is a legal Chart."""
    if not isinstance(alloc, dict):
        return 'Chart must be an object'
    spent = 0
    for tid, r in alloc.items():
        if tid not in TALENTS:
            return f'Unknown talent: {tid}'
        if not isinstance(r, int) or isinstance(r, bool) or r < 0 or r > max_rank(tid):
            return f'Bad rank for {tid}'
        spent += r
    if spent > points:
        return f'Not enough points ({spent} > {points})'
    if sum(1 for k in KEYSTONES if alloc.get(k)) > 1:
        return 'Only one keystone'
    for tid, r in alloc.items():
        if not r:
            continue
        d = TALENTS[tid]
        # Gates count points in the tree's *earlier* rows, so rows can't unlock each other.
        top = 4 if d['row'] == 'K' else d['row']
        below = sum(rank(alloc, o) for o, od in TALENTS.items()
                    if od['tree'] == d['tree'] and od['row'] != 'K' and od['row'] < top)
        gate = KEYSTONE_GATE if d['row'] == 'K' else ROW_GATE[d['row']]
        if below < gate:
            return f"{d['name']} needs {gate} points in {TREES[d['tree']]['name']}"
        req = d.get('requires')
        if req and rank(alloc, req) < max_rank(req):
            return f"{d['name']} needs {TALENTS[req]['name']} first"
    return None


def is_refund(old: dict, new: dict) -> bool:
    """True if ``new`` takes back any rank that ``old`` had."""
    return any(rank(new, t) < r for t, r in (old or {}).items())


def granted_items(alloc: dict) -> list:
    out = []
    for tid, d in TALENTS.items():
        for g in d['grants'][:rank(alloc, tid)]:
            out.extend(i for i in g if i not in out)
    return out


def recompute_owned(owned: list, alloc: dict) -> list:
    """Non-gear items (cosmetics, auto-spin) stay; gear is exactly the Chart's grants."""
    kept = [i for i in owned if i not in CHART_REPLACES]
    return kept + [i for i in granted_items(alloc) if i not in kept]


def clean(alloc: dict) -> dict:
    return {t: r for t, r in alloc.items() if r}


def catalog() -> list:
    """Client-facing talent list (the UI renders straight from this)."""
    out = []
    for tid, d in TALENTS.items():
        out.append({'id': tid, 'tree': d['tree'], 'row': d['row'], 'name': d['name'],
                    'max_rank': max_rank(tid), 'desc': d['desc'], 'requires': d.get('requires')})
    return out
