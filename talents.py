"""Season 9 Charts: a limited-points talent system (docs/SEASON_9_DEEP_SPEC.md §3).

A Chart is ``{talent_id: rank}``. Ranks grant existing shop item ids into
``owned_items`` so ``_resolve_spin`` and the fishing helpers keep reading
``'item' in owned``. Talents with no item (Rich Waters, Steady Hands,
keystones) are read from the Chart directly via ``rank()`` / ``keystone()``.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from models import AUTO_SPIN_OFFLINE_CAP_S, CHIP_CAP, ITEM_CURRENCY

_LONDON = ZoneInfo('Europe/London')

# ── Tuned numbers (balance table: SEASON_9_DEEP_SPEC.md §8) ───────────────
START_POINTS = 1           # day 0 of a tide; +1 free each tide day
MAX_POINTS = 14            # one full tree plus a splash, of 32 ranks
LEVEL_COST_BASE = 1_000    # wins for the first bought point
LEVEL_COST_GROWTH = 8      # each bought point costs ×8 the last
ROW_GATE = {1: 0, 2: 2, 3: 4}   # points in earlier rows of ANY tree to unlock a row (Tide 9.3)
KEYSTONE_GATE = 6
SURGE_MULT_BY_RICH_WATERS = {0: 5, 1: 25, 2: 50, 3: 100}
SURGE_BAIT_BONUS_PER_RANK = 0.25
# Tide 9.3: on a Surge spin Undertow pays at least Surge's bonus × this.
UNDERTOW_SURGE_MULT = {0: 1, 1: 1.25, 2: 1.5, 3: 2}

# Tide Currents (Tide 9.4): each tide one tree's waters run strong, rotating from 9.4
# (season_number 13) so the best build shifts and a stale Chart isn't always right.
CURRENTS = ('riptide', 'angler', 'swell')
CURRENT_FIRST_SEASON = 13
CURRENT_DESC = {
    'riptide': "Daily 🪙 claim gives 2 more chips, and you can hold up to 8",
    'angler':  'Better Bait also raises 🎣 Surge pay by 25% a rank',
    'swell':   'Echo and Fortune Charm trigger twice as often',
}
RIPTIDE_CHIP_BONUS = 2
RIPTIDE_CHIP_CAP = 8

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
                      'desc': ['Streak bonuses ×2, or ×1.25 on top of 🎣 Surge', 'Streak bonuses ×4, or ×1.5 on top of 🎣 Surge',
                               'Streak bonuses ×8, or ×2 on top of 🎣 Surge']},
    'rising_tide':   {'tree': 'swell', 'row': 1, 'name': 'Rising Tide', 'grants': [['winmult_1'], ['winmult_2']],
                      'desc': ['Every win pays ×2, and +1 free 🪙 a day', 'Every win pays ×4, and +2 free 🪙 a day']},
    'steady_keel':   {'tree': 'swell', 'row': 2, 'name': 'Steady Keel', 'grants': [['resilience']],
                      'desc': ['Sometimes a loss only knocks your streak back one']},
    'fortune_charm': {'tree': 'swell', 'row': 2, 'name': 'Fortune Charm', 'grants': [['fortune_charm']],
                      'desc': ['Streak bonuses sometimes pay +25%']},
    'echo':          {'tree': 'swell', 'row': 2, 'name': 'Echo', 'grants': [['win_echo']],
                      'desc': ['Wins sometimes pay twice']},
    'breakwater':    {'tree': 'swell', 'row': 3, 'name': 'Breakwater', 'grants': [['regen_shield']],
                      'desc': ['Blocks one loss, recharges after 25 wins']},
    'spring_tide':   {'tree': 'swell', 'row': 'K', 'name': 'Spring Tide', 'grants': [[]],
                      'desc': ["Streak bonuses ×2 again, 🎣 Surge included — but not on staked or diced spins"]},
    # 🌀 Riptide
    'open_water':    {'tree': 'riptide', 'row': 1, 'name': 'Open Water', 'grants': [['wager_unlock']],
                      'desc': ["Stake up to 60% of today's haul (wins since midnight). Each staked spin costs 1 🪙"]},
    'loaded_dice':   {'tree': 'riptide', 'row': 1, 'name': 'Loaded Dice',
                      'grants': [['dice_charge_2'], ['dice_charge_3'], ['dice_charge_4']],
                      'desc': ['Hold 2 dice charges', 'Hold 3 dice charges', 'Hold 4 dice charges']},
    'deep_water':    {'tree': 'riptide', 'row': 2, 'name': 'Deep Water', 'requires': 'open_water',
                      'grants': [['wager_stake_extend_1'], ['wager_stake_extend_2']],
                      'desc': ['Stake up to 80% of the haul', 'Stake up to 100% of the haul']},
    'treasure':      {'tree': 'riptide', 'row': 2, 'name': 'Treasure', 'grants': [['jackpot']],
                      'desc': ['3% of wins are jackpots: ×25, or ×10 on a staked spin']},
    'safety_line':   {'tree': 'riptide', 'row': 2, 'name': 'Safety Line', 'requires': 'open_water',
                      'grants': [['wager_safety_net', 'wager_insurance']],
                      'desc': ['Staked losses refund half; your first insurance each day is free']},
    'third_die':     {'tree': 'riptide', 'row': 3, 'name': 'Third Die', 'grants': [['dice_extra']],
                      'desc': ['Roll three dice — and a pair of 1s no longer curses']},
    'double_or_nothing': {'tree': 'riptide', 'row': 3, 'name': 'Double or Nothing', 'requires': 'open_water',
                      'grants': [['wager_double_down']],
                      'desc': ['Re-stake your last win in one go — a win pays ×2.5']},
    'rogue_wave':    {'tree': 'riptide', 'row': 'K', 'name': 'Rogue Wave', 'grants': [[]],
                      'desc': ['Dice come back twice as fast and stack two higher — but 🎣 Surge skips diced spins']},
    # 🎣 Angler
    'rich_waters':   {'tree': 'angler', 'row': 1, 'name': 'Rich Waters', 'grants': [[], [], []],
                      'desc': ['Surge spins pay ×25 (base ×5)', 'Surge spins pay ×50', 'Surge spins pay ×100']},
    'better_bait':   {'tree': 'angler', 'row': 1, 'name': 'Better Bait', 'grants': [['lure_1', 'lure_2'], ['lure_3']],
                      'desc': ['Faster bites, bigger catches, +25% Surge', 'Even faster, even bigger, +50% Surge']},
    'deckhand':      {'tree': 'angler', 'row': 2, 'name': 'Deckhand', 'grants': [['autofisher_1'], ['autofisher_2']],
                      'desc': ["Auto-fish while you're away", 'Auto-fish catches more often']},
    'steady_hands':  {'tree': 'angler', 'row': 2, 'name': 'Steady Hands', 'grants': [[], [], []],
                      'desc': ['A wider reel bar', 'Wider bar, and it moves 50% faster',
                               'Wider, faster bar, and a slipping fish gets away 25% slower']},
    'auto_cast':     {'tree': 'angler', 'row': 2, 'name': 'Auto-Cast', 'grants': [['auto_cast']],
                      'desc': ['Recast automatically']},
    'old_salt':      {'tree': 'angler', 'row': 3, 'name': 'Old Salt', 'requires': 'deckhand',
                      'grants': [['autofisher_3', 'autofisher_4']],
                      'desc': ['Auto-fish catches rares, and more often']},
    'deep_sea':      {'tree': 'angler', 'row': 'K', 'name': 'Deep Sea', 'grants': [[]],
                      'desc': ['Only the big ones bite — and they take their time']},
}
ICONS = {
    'undertow': '🫧', 'rising_tide': '📈', 'steady_keel': '⚓', 'fortune_charm': '🍀', 'echo': '🔔',
    'breakwater': '🛡️', 'spring_tide': '🌕',
    'open_water': '🪙', 'loaded_dice': '🎲', 'deep_water': '🔱', 'treasure': '💎', 'safety_line': '🛟',
    'third_die': '🎯', 'double_or_nothing': '⚖️', 'rogue_wave': '🌪️',
    'rich_waters': '🐚', 'better_bait': '🪱', 'deckhand': '⛵', 'steady_hands': '✋', 'auto_cast': '🔁',
    'old_salt': '🧓', 'deep_sea': '🐋',
}
assert ICONS.keys() == TALENTS.keys()

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


def tide_start(now: datetime) -> datetime:
    """The last tide turn (Fri 21:00 London) at or before now."""
    shifted = now.astimezone(_LONDON).replace(tzinfo=None) + timedelta(days=2, hours=3)
    monday = datetime.combine(shifted.date() - timedelta(days=shifted.weekday()), datetime.min.time())
    return (monday - timedelta(days=2, hours=3)).replace(tzinfo=_LONDON)


def offline_floor(now: datetime, last_seen: datetime) -> datetime:
    """Earliest time offline catch-up credits: 72 h back, or back to the
    turn on a player's first visit of the tide, so late starters keep the week."""
    floor = now - timedelta(seconds=AUTO_SPIN_OFFLINE_CAP_S)
    start = tide_start(now)
    return min(floor, start) if last_seen < start else floor


def points_total(now: datetime, bought: int = 0) -> int:
    return min(MAX_POINTS, START_POINTS + tide_day(now) + bought)


def level_cost(bought: int) -> int:
    """Wins for the next bought point, given how many were bought this tide."""
    return LEVEL_COST_BASE * LEVEL_COST_GROWTH ** bought


def rank(alloc: dict, talent_id: str) -> int:
    return int((alloc or {}).get(talent_id, 0))


def keystone(alloc: dict):
    return next((k for k in KEYSTONES if rank(alloc, k) > 0), None)


def surge_mult(alloc: dict) -> int:
    return SURGE_MULT_BY_RICH_WATERS[rank(alloc, 'rich_waters')]


def surge_bonus(alloc: dict) -> float:
    return 1.0 + SURGE_BAIT_BONUS_PER_RANK * rank(alloc, 'better_bait')


def current(season_number):
    """This tide's current, or None before Tide 9.4."""
    if not season_number or season_number < CURRENT_FIRST_SEASON:
        return None
    return CURRENTS[(season_number - CURRENT_FIRST_SEASON) % len(CURRENTS)]


def current_info(season_number):
    cur = current(season_number)
    return cur and {'id': cur, 'name': TREES[cur]['name'], 'desc': CURRENT_DESC[cur]}


def chip_cap(season_number) -> int:
    return RIPTIDE_CHIP_CAP if current(season_number) == 'riptide' else CHIP_CAP


def free_chips(alloc: dict, season_number) -> int:
    """Chips the daily claim gives: 3, +1 per Rising Tide rank, +2 in a Riptide current."""
    riptide = RIPTIDE_CHIP_BONUS if current(season_number) == 'riptide' else 0
    return 3 + rank(alloc, 'rising_tide') + riptide


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
        # Row gates count earlier rows of every tree (Tide 9.3), so hybrids pay no toll;
        # keystones still need their own tree. Rows can't unlock each other.
        top = 4 if d['row'] == 'K' else d['row']
        below = sum(rank(alloc, o) for o, od in TALENTS.items()
                    if (d['row'] != 'K' or od['tree'] == d['tree']) and od['row'] != 'K' and od['row'] < top)
        gate = KEYSTONE_GATE if d['row'] == 'K' else ROW_GATE[d['row']]
        if below < gate:
            where = TREES[d['tree']]['name'] if d['row'] == 'K' else 'earlier rows'
            return f"{d['name']} needs {gate} points in {where}"
        req = d.get('requires')
        if req and rank(alloc, req) < max_rank(req):
            return f"{d['name']} needs {TALENTS[req]['name']} first"
    return None


def fit(alloc: dict, points: int) -> dict:
    """Re-place a saved Chart rank by rank, earliest rows first, as far as
    ``points`` and the gates allow. Talents since retired are skipped."""
    out = {}
    saved = [(t, r) for t, r in (alloc or {}).items() if t in TALENTS and isinstance(r, int)]
    for tid, r in sorted(saved, key=lambda tr: 4 if TALENTS[tr[0]]['row'] == 'K' else TALENTS[tr[0]]['row']):
        for _ in range(min(r, max_rank(tid))):
            trial = {**out, tid: out.get(tid, 0) + 1}
            if validate(trial, points):
                break
            out = trial
    return out


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
        out.append({'id': tid, 'tree': d['tree'], 'row': d['row'], 'name': d['name'], 'icon': ICONS[tid],
                    'max_rank': max_rank(tid), 'desc': d['desc'], 'requires': d.get('requires')})
    return out


SURGE_BY_RARITY = {'junk': 0, 'common': 6, 'uncommon': 15, 'rare': 40, 'legendary': 150}
AUTO_SURGE_MULT = 0.5


def catch_surge(alloc: dict, rarity: str, size_ratio: float, auto: bool) -> int:
    """Surge spins a catch earns (spec §4)."""
    base = SURGE_BY_RARITY[rarity]
    if not base:
        return 0
    s = base * (0.5 + size_ratio) * surge_bonus(alloc)
    return max(1, round(s * AUTO_SURGE_MULT)) if auto else round(s)
