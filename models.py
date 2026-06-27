import random

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


# ── Fishing minigame catalog ───────────────────────────────────────────────
# weight values sum to 100; they represent percentage probability of a catch.
FISH_CATALOG = {
    'minnow':     {'emoji': '🐟', 'name': 'Minnow',     'value':   1, 'weight': 30.0, 'tier': 'Common'},
    'shrimp':     {'emoji': '🦐', 'name': 'Shrimp',      'value':   2, 'weight': 12.0, 'tier': 'Common'},
    'clownfish':  {'emoji': '🐠', 'name': 'Clownfish',   'value':   3, 'weight': 15.0, 'tier': 'Common'},
    'pufferfish': {'emoji': '🐡', 'name': 'Pufferfish',  'value':   3, 'weight': 12.0, 'tier': 'Common'},
    'crab':       {'emoji': '🦀', 'name': 'Crab',        'value':   8, 'weight': 10.0, 'tier': 'Uncommon'},
    'squid':      {'emoji': '🦑', 'name': 'Squid',       'value':   8, 'weight':  8.0, 'tier': 'Uncommon'},
    'octopus':    {'emoji': '🐙', 'name': 'Octopus',     'value':  12, 'weight':  5.0, 'tier': 'Uncommon'},
    'lobster':    {'emoji': '🦞', 'name': 'Lobster',     'value':  20, 'weight':  4.0, 'tier': 'Rare'},
    'dolphin':    {'emoji': '🐬', 'name': 'Dolphin',     'value':  30, 'weight':  2.0, 'tier': 'Rare'},
    'shark':      {'emoji': '🦈', 'name': 'Shark',       'value':  40, 'weight':  1.5, 'tier': 'Rare'},
    'whale':      {'emoji': '🐋', 'name': 'Blue Whale',  'value':  75, 'weight':  0.5, 'tier': 'Legendary'},
    'mermaid':    {'emoji': '🧜', 'name': 'Mermaid',     'value': 120, 'weight':  0.2, 'tier': 'Legendary'},
    'lucky':      {'emoji': '⭐', 'name': 'Lucky Fish',  'value': 100, 'weight':  0.3, 'tier': 'Legendary', 'doubles_next': True},
}

# Legendary fish never catchable by auto-fish at any level
_AUTO_FISH_LEGENDARY = frozenset({'whale', 'mermaid', 'lucky'})
# Rare fish excluded at autofisher levels 1–3; unlocked by autofisher_4 (Master Auto-Fisher)
_AUTO_FISH_RARE = frozenset({'lobster', 'dolphin', 'shark'})
# Combined exclusion for levels 1–3
AUTO_FISH_EXCLUDED = _AUTO_FISH_LEGENDARY | _AUTO_FISH_RARE

# Pre-built weighted lists for roll_fish()
_ALL_IDS     = list(FISH_CATALOG.keys())
_ALL_WEIGHTS = [FISH_CATALOG[k]['weight'] for k in _ALL_IDS]
# Levels 1–3: common + uncommon only
_AUTO_IDS    = [k for k in _ALL_IDS if k not in AUTO_FISH_EXCLUDED]
_AUTO_WEIGHTS= [FISH_CATALOG[k]['weight'] for k in _AUTO_IDS]
# Level 4 (Master): common + uncommon + rare; still no legendary
_AUTO_RARE_IDS    = [k for k in _ALL_IDS if k not in _AUTO_FISH_LEGENDARY]
_AUTO_RARE_WEIGHTS= [FISH_CATALOG[k]['weight'] for k in _AUTO_RARE_IDS]


def roll_fish(
    auto_mode: bool,
    allow_rare: bool = False,
    master_lure: bool = False,
    happy_hour: bool = False,
) -> str:
    """Return a random fish species ID weighted by rarity.
    master_lure=True adds +1% to each legendary species — manual only.
    happy_hour=True adds +50% weight to legendary species — manual only.
    """
    if auto_mode:
        if allow_rare:
            return random.choices(_AUTO_RARE_IDS, weights=_AUTO_RARE_WEIGHTS, k=1)[0]
        return random.choices(_AUTO_IDS, weights=_AUTO_WEIGHTS, k=1)[0]
    if master_lure or happy_hour:
        legend_bonus = (1.0 if master_lure else 0.0)
        hh_bonus     = 0.5 if happy_hour else 0.0
        boosted = [
            w + (legend_bonus + FISH_CATALOG[k]['weight'] * hh_bonus if k in _AUTO_FISH_LEGENDARY else 0.0)
            for k, w in zip(_ALL_IDS, _ALL_WEIGHTS)
        ]
        return random.choices(_ALL_IDS, weights=boosted, k=1)[0]
    return random.choices(_ALL_IDS, weights=_ALL_WEIGHTS, k=1)[0]


def lure_bite_delay_seconds(lure_level: int) -> tuple[float, float]:
    """Return (min_seconds, max_seconds) wait between cast and bite.
    Base window is 3–10 s. Each lure tier reduces both bounds by a fixed percentage,
    making timing harder to bot (wide variance at all levels).
    """
    base_min, base_max = 3.0, 10.0
    reductions = {0: 0.0, 1: 0.10, 2: 0.20, 3: 0.35, 4: 0.50, 5: 0.65}
    r = reductions.get(min(lure_level, 5), 0.0)
    return (round(base_min * (1 - r), 2), round(base_max * (1 - r), 2))


def lure_value_multiplier(lure_level: int) -> float:
    """Multiplier applied to every catch at this lure level."""
    mults = {0: 1.0, 1: 1.5, 2: 2.0, 3: 5.0, 4: 10.0, 5: 20.0}
    return mults.get(lure_level, 20.0)


def autofisher_catch_rate(autofisher_level: int) -> float:
    """Probability [0,1) of a successful auto-fish tick."""
    rates = {0: 0.0, 1: 0.45, 2: 0.55, 3: 0.65, 4: 0.75}
    return rates.get(autofisher_level, 0.0)


def fish_value(species_id: str, lure_level: int) -> int:
    """Base catalog value × lure multiplier (Lucky Fish / Precise Angler doubling applied externally)."""
    base = FISH_CATALOG[species_id]['value']
    return max(1, int(base * lure_value_multiplier(lure_level)))


FISH_SKINS = {
    'fish_tropical': {'cost': 25},
    'fish_puffer':   {'cost': 50},
    'fish_octopus':  {'cost': 75},
    'fish_shark':    {'cost': 100},
    'fish_dolphin':  {'cost': 150},
    'fish_squid':    {'cost': 200},
    'fish_turtle':   {'cost': 350},
    'fish_crab':     {'cost': 600},
    'fish_lobster':  {'cost': 1_000},
    'fish_whale':    {'cost': 2_000},
    'fish_seal':     {'cost': 3_500},
    'fish_shrimp':   {'cost': 6_000},
    'fish_coral':    {'cost': 10_000},
    'fish_mermaid':  {'cost': 17_500},
    'fish_croc':     {'cost': 30_000},
    'fish_rocket':   {'cost': 50_000},
    'fish_comet':    {'cost': 85_000},
    'fish_saturn':   {'cost': 145_000},
    'fish_alien':    {'cost': 250_000},
    'fish_ufo':      {'cost': 425_000},
    'fish_dice':     {'cost': 600_000},
    'fish_joker':    {'cost': 850_000},
    'fish_diamond':  {'cost': 1_200_000},
    'fish_poker':    {'cost': 1_700_000},
    'fish_slot':     {'cost': 2_400_000},
}

SHOP_ITEMS = {
    # Dice charge upgrades (unlocked via tier gating)
    'dice_charge_2':  {'cost': 2_000,        'requires': None},
    'dice_charge_3':  {'cost': 15_000,       'requires': 'dice_charge_2'},
    'dice_charge_4':  {'cost': 100_000,      'requires': 'dice_charge_3'},
    # Extra Die — roll 3 dice; requires Tier 3 + dice_charge_3
    'dice_extra':     {'cost': 1_000_000,    'requires': 'dice_charge_3'},
    # Win power (Season 6: shallower scaling — matches winmult_inf tier_costs)
    'winmult_1':      {'cost': 200,         'requires': None},
    'winmult_2':      {'cost': 600,         'requires': 'winmult_1'},
    'winmult_3':      {'cost': 2000,        'requires': 'winmult_2'},
    'winmult_4':      {'cost': 6400,        'requires': 'winmult_3'},
    'winmult_5':      {'cost': 20000,       'requires': 'winmult_4'},
    'winmult_6':      {'cost': 64000,       'requires': 'winmult_5'},
    'winmult_7':      {'cost': 200000,      'requires': 'winmult_6'},
    # Bonus power (Season 6: shallower scaling — matches bonusmult_inf tier_costs)
    'bonusmult_1':    {'cost': 300,         'requires': None},
    'bonusmult_2':    {'cost': 900,         'requires': 'bonusmult_1'},
    'bonusmult_3':    {'cost': 2800,        'requires': 'bonusmult_2'},
    'bonusmult_4':    {'cost': 8500,        'requires': 'bonusmult_3'},
    'bonusmult_5':    {'cost': 26000,       'requires': 'bonusmult_4'},
    'bonusmult_6':    {'cost': 80000,       'requires': 'bonusmult_5'},
    # Fish size (cosmetic — controls fishing panel scale; all 1 loss as accessibility features)
    'fishsize_small': {'cost': 1,            'requires': None},
    'fishsize_1':     {'cost': 1,            'requires': None},
    'fishsize_2':     {'cost': 1,            'requires': 'fishsize_1'},
    'fishsize_3':     {'cost': 1,            'requires': 'fishsize_2'},
    # Trails (cosmetic)
    'trail_1':        {'cost': 125,          'requires': None},
    'trail_2':        {'cost': 500,          'requires': 'trail_1'},
    'trail_3':        {'cost': 2_000,        'requires': 'trail_2'},
    'trail_4':        {'cost': 7_000,        'requires': 'trail_3'},
    'trail_5':        {'cost': 22_000,       'requires': 'trail_4'},
    'trail_6':        {'cost': 70_000,       'requires': 'trail_5'},
    # Protection (Season 8 rework — see spec S7)
    'guard':          {'cost': 1_000,        'requires': None},
    'guard_charge':   {'cost': 10_000,       'requires': 'guard'},
    'regen_shield':   {'cost': 5_000,        'requires': None},
    # Wheel themes (cosmetic)
    'theme_fire':     {'cost': 250,          'requires': None},
    'theme_ice':      {'cost': 1_000,        'requires': 'theme_fire'},
    'theme_neon':     {'cost': 4_000,        'requires': 'theme_ice'},
    'theme_void':     {'cost': 12_000,       'requires': 'theme_neon'},
    'theme_gold':     {'cost': 40_000,       'requires': 'theme_void'},
    # Misc cosmetics
    'golden_wheel':   {'cost': 300,          'requires': None},
    'page_season1':   {'cost': 1_000,        'requires': None},
    'page_season2':   {'cost': 1_000,        'requires': None},
    'page_season3':   {'cost': 1_000,        'requires': None},
    'page_season4':   {'cost': 1_000,        'requires': None},
    'page_season5':   {'cost': 1_000,        'requires': None},
    'page_season6':   {'cost': 1_000,        'requires': None},
    'page_season7':   {'cost': 1_000,        'requires': None},
    'page_season8':   {'cost': 1_000,        'requires': None},
    'party_mode':     {'cost': 150,          'requires': None},
    'confetti_1':     {'cost': 75,           'requires': None},
    'confetti_2':     {'cost': 300,          'requires': 'confetti_1'},
    'confetti_3':     {'cost': 1_200,        'requires': 'confetti_2'},
    # Backgrounds (cosmetic)
    'bg_royal':       {'cost': 400,          'requires': None},
    'bg_inferno':     {'cost': 1_600,        'requires': 'bg_royal'},
    'bg_forest':      {'cost': 5_000,        'requires': 'bg_inferno'},
    'bg_abyss':       {'cost': 15_000,       'requires': 'bg_forest'},
    'bg_cosmic':      {'cost': 50_000,       'requires': 'bg_abyss'},
    # Bonus functional upgrades (resilience/jackpot reworked in Season 8 — see below)
    'fortune_charm':  {'cost': 1_000_000,    'requires': None},
    'lucky_seven':    {'cost': 7_000_000,    'requires': None},
    'win_echo':       {'cost': 1_000_000,    'requires': None},
    # Season 7 classes — own any, equip one at a time; functional tier 3
    'class_earth': {'cost': 10_000_000, 'requires': None},
    'class_moon':  {'cost': 10_000_000, 'requires': None},
    'class_star':  {'cost': 10_000_000, 'requires': None},
    # singularity removed in Season 8 — now a server-wide community meter (spec S13)
    # ── Fishing gear (Season 6) ──────────────────────────────────────────────
    # auto_cast: auto-casts line; player still taps the bite window manually.
    'auto_cast':      {'cost': 1_000,        'requires': None},
    # Lure upgrades: reduce bite wait time and add flat value bonus to every catch.
    # Both manual and auto-fish benefit.
    'lure_1':         {'cost': 100,          'requires': None},
    'lure_2':         {'cost': 500,          'requires': 'lure_1'},
    'lure_3':         {'cost': 2_500,        'requires': 'lure_2'},
    'lure_4':         {'cost': 15_000,       'requires': 'lure_3'},
    'lure_5':         {'cost': 500_000,      'requires': 'lure_4'},
    # Auto-Fisher upgrades: unlock Auto-Fish tickbox; improve auto catch rate.
    # Auto-Fish NEVER catches whale/mermaid/lucky at any level.
    'autofisher_1':   {'cost': 300,          'requires': None},
    'autofisher_2':   {'cost': 2_000,        'requires': 'autofisher_1'},
    'autofisher_3':   {'cost': 12_000,       'requires': 'autofisher_2'},
    'autofisher_4':   {'cost': 500_000,      'requires': 'autofisher_3'},
    # Precise Angler upgrades: tiered multipliers for early reels.
    # Level 1: ≤50% → 1.2x  (Tier 2 gate: 1 000 wins)
    # Level 2: ≤20% → 1.5x  (≤50% still gives 1.2x)
    # Level 3: ≤15% → 2.0x  (Master Angler — encyclopaedia locked)
    # Multipliers are exclusive: highest gate hit wins.
    'precise_angler_1': {'cost':  50_000,    'requires': None},
    'precise_angler_2': {'cost': 100_000,    'requires': 'precise_angler_1'},
    'precise_angler_3': {'cost': 500_000,    'requires': 'precise_angler_2'},
    # ── Season 8: Wager system (spec S3) ──────────────────────────────────────
    'wager_unlock':      {'cost': 500,       'requires': None},
    'wager_safety_net':  {'cost': 2_000,     'requires': 'wager_unlock'},
    'wager_hot_streak':  {'cost': 8_000,     'requires': 'wager_unlock'},
    'wager_double_down': {'cost': 25_000,    'requires': 'wager_hot_streak'},
    'wager_insurance':   {'cost': 50_000,    'requires': 'wager_unlock'},
    # T102+T104: stake extension items — 30% base → 35% → 40% → 45%
    'wager_stake_extend_1': {'cost': 5_000,    'requires': 'wager_unlock'},
    'wager_stake_extend_2': {'cost': 15_000,   'requires': 'wager_stake_extend_1'},
    'wager_stake_extend_3': {'cost': 40_000,   'requires': 'wager_stake_extend_2'},
    # ── Season 8: Prestige system (spec S5) ───────────────────────────────────
    # T121: only prestige_unlock is buyable from the shop. prestige_efficiency
    # and prestige_legacy have been retired — they're no longer in SHOP_ITEMS
    # (so /api/buy rejects them with 403 via the RETIRED_ITEMS guard) and
    # the prestige flow no longer reads their effect.
    'prestige_unlock':     {'cost': 1_000_000, 'requires': None},
    # ── Season 8: Fishing integration (spec S6) ───────────────────────────────
    'fish_to_wager':       {'cost': 5_000,   'requires': None},
    'catch_of_the_day':    {'cost': 3_000,   'requires': None},
    'aquarium':            {'cost': 15_000,  'requires': None},
    'lure_specialization': {'cost': 10_000,  'requires': 'fish_to_wager'},
    # ── Season 8: Wheel themes (spec S16) ─────────────────────────────────────
    'theme_tidal':   {'cost': 250,          'requires': None},
    'theme_ember':   {'cost': 1_000,        'requires': 'theme_tidal'},
    'theme_frost':   {'cost': 4_000,        'requires': 'theme_ember'},
    'theme_aurora':  {'cost': 12_000,       'requires': 'theme_frost'},
    'theme_vintage': {'cost': 40_000,       'requires': None},
    # ── Season 8: Resilience rework (spec S7) ──────────────────────────────────
    'resilience':    {'cost': 20_000,       'requires': None},
    'jackpot':       {'cost': 3_000_000,    'requires': None},
    # ── Season 8: Auto-spin as upgrade (T107) ─────────────────────────────────
    # T107: one-time unlock. While active, the stake slider is hidden in the UI
    # (auto-spin always uses 0% stake). DD + insurance remain visible but
    # are no-ops during auto-spin (server already prevents them).
    'auto_spin_unlock': {'cost': 5_000,    'requires': None},
}

# T121: active prestige items (buyable). Kept separate from SHOP_ITEMS so the
# prestige atomic-flow doesn't need to walk the full shop dict — only one item
# is buyable here and it's the unlock for the prestige loop itself.
PRESTIGE_ITEMS = {
    'prestige_unlock': {'cost': 1_000_000, 'requires': None},
}

# T121: items that USED to be buyable from the prestige section of the shop
# (S5-era `prestige_efficiency` and `prestige_legacy`). Operator removed them
# because they added an unnecessary meta-progression. Kept here as a tombstone
# so /api/buy can reject malicious calls with a clear 403 instead of an
# ambiguous 400 "Unknown item" — defence-in-depth. Players who somehow already
# own these from staging legacy data see no effect: get_legacy_keep_count
# returns 0 and compute_wins_kept returns 0 unconditionally.
RETIRED_ITEMS = {
    'prestige_efficiency': {'cost': 500_000,   'requires': 'prestige_unlock',
                            'retired_in': 'T121'},
    'prestige_legacy':     {'cost': 1_000_000, 'requires': 'prestige_unlock',
                            'retired_in': 'T121'},
}

# T106: upgrade tier gating — items not listed here are Tier 1 (always available)
# Thresholds are based on cumulative_wins (lifetime value of wins gained, T106).
# Updated from the old win_count (count of winning spins) which was too slow
# for the manual-wager era.
UPGRADE_TIER_THRESHOLDS = {2: 10_000, 3: 100_000}
UPGRADE_TIER_2 = {
    'regen_shield', 'guard_charge', 'dice_charge_2',
    'precise_angler_1',
    'aquarium', 'lure_specialization',
}
UPGRADE_TIER_3 = {
    'fortune_charm', 'lucky_seven', 'win_echo', 'jackpot', 'resilience',
    'dice_charge_3', 'dice_charge_4', 'dice_extra',
    'class_earth', 'class_moon', 'class_star',
    'wager_double_down', 'wager_insurance',
    'prestige_unlock',
}

def item_tier(item_id: str) -> int:
    """Return the tier (1, 2, or 3) required to purchase this item."""
    if item_id in UPGRADE_TIER_3:
        return 3
    if item_id in UPGRADE_TIER_2:
        return 2
    return 1

assert not (set(FISH_SKINS) & set(SHOP_ITEMS)), (
    f"FISH_SKINS and SHOP_ITEMS share keys: {set(FISH_SKINS) & set(SHOP_ITEMS)}"
)
ALL_ITEMS = {**FISH_SKINS, **SHOP_ITEMS}
VALID_FISH_IDS = set(FISH_SKINS.keys()) | {'default'}

# Season 3: currency classification for each item.
# 'wins'       — functional items; purchasing deducts from the player's win count.
# 'losses'     — cosmetic items (fish skins + cosmetic shop items); deducts from loss count.
# Functional shop items are the exception; everything else in SHOP_ITEMS is cosmetic.
# FISH_SKINS are all cosmetic by definition.
_FUNCTIONAL_SHOP_ITEMS = {
    'guard', 'guard_charge', 'regen_shield',
    'winmult_1', 'winmult_2', 'winmult_3', 'winmult_4', 'winmult_5', 'winmult_6', 'winmult_7',
    'bonusmult_1', 'bonusmult_2', 'bonusmult_3', 'bonusmult_4', 'bonusmult_5', 'bonusmult_6',
    'fortune_charm', 'lucky_seven', 'win_echo', 'resilience', 'jackpot',
    'class_earth', 'class_moon', 'class_star',
    'auto_cast',
    'lure_1', 'lure_2', 'lure_3', 'lure_4', 'lure_5',
    'autofisher_1', 'autofisher_2', 'autofisher_3', 'autofisher_4',
    'precise_angler_1', 'precise_angler_2', 'precise_angler_3',
    'dice_charge_2', 'dice_charge_3', 'dice_charge_4', 'dice_extra',
    # Season 8 additions
    'wager_unlock', 'wager_safety_net', 'wager_hot_streak', 'wager_double_down', 'wager_insurance',
    'wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3',
    'auto_spin_unlock',
    'prestige_unlock',
    'fish_to_wager', 'catch_of_the_day', 'aquarium', 'lure_specialization',
}


ITEM_CURRENCY = {}
for _id in ALL_ITEMS:
    if _id in FISH_SKINS or _id not in _FUNCTIONAL_SHOP_ITEMS:
        ITEM_CURRENCY[_id] = 'losses'
    else:
        ITEM_CURRENCY[_id] = 'wins'

# Season 8: old infinite upgrades removed (spec S5). Columns remain in DB
# for historical queries but are frozen at 0 and not read by _resolve_spin().
# Only clickmult_inf is retained (not in the S5 removal list).
INFINITE_UPGRADES = {
    'clickmult_inf': {
        'db_column':    'clickmult_inf_level',
        'tier_costs':   [75, 250, 600, 1400, 3000],
        'inf_base_cost': 10_000,
        'inf_scale':     1.5,
    },
}

# Season 8: Singularity meter per-player contribution cap (spec S13).
# Resets each time the meter fills (tracked per fill_count).
SINGULARITY_PER_PLAYER_CAP = 25_000_000


def inf_upgrade_cost(item_id: str, current_level: int) -> int:
    """Cost to advance from current_level to current_level+1."""
    cfg = INFINITE_UPGRADES[item_id]
    tiers = cfg['tier_costs']
    if current_level < len(tiers):
        return tiers[current_level]
    excess = current_level - len(tiers)
    return int(cfg['inf_base_cost'] * cfg['inf_scale'] ** excess)


# ── Season 7 upgrade multipliers ──────────────────────────────────────────────

def lure_mastery_mult(level: int) -> float:
    """Additional fish-value multiplier on top of the lure tier cap. +10% per level."""
    return 1.0 + level * 0.10


# ── Season 7 class effect constants ───────────────────────────────────────────
CLASS_EARTH_FISH_BONUS = 0.25   # Earth: +25% to fish-click income
CLASS_MOON_PROC_BONUS  = 0.05   # Moon:  +5% added to each proc rate (jackpot, echo, charm, resilience)
CLASS_STAR_WIN_BONUS   = 0.20   # Star:  +20% to win_mult payout


def streak_bonus(count: int) -> int:
    """Season 6 streak bonus formula.
    Keeps exponential through streak 15, then buffs mid/high range.
    Hard cap at streak 150 to prevent runaway numbers.
    """
    if count < 3:
        return 0
    if count <= 15:
        return 1 << (count - 3)                      # exponential: 1 → 4096 (unchanged)
    if count <= 35:
        return 4096 + (count - 15) ** 3 * 2          # cubic ×2: 4096 → 20,096
    if count <= 75:
        return 20096 + (count - 35) * 1200           # linear 1.2k/step: 20,096 → 68,096
    if count <= 150:
        return 68096 + (count - 75) * 600            # slower linear: 68,096 → 113,096
    return 113096                                     # hard cap


# Dice roll constants (Season 5)
DICE_RECHARGE_SECONDS = 600   # 10 minutes per charge
DICE_MAX_CHARGES_BASE = 1     # default max without upgrades


def dice_max_charges(owned_items: list) -> int:
    """Return the maximum dice charges based on owned upgrades."""
    if 'dice_charge_4' in owned_items:
        return 4
    if 'dice_charge_3' in owned_items:
        return 3
    if 'dice_charge_2' in owned_items:
        return 2
    return DICE_MAX_CHARGES_BASE


LOCKOUT_RULES = [
    (20, 3600),  # 20+ fails → 1 hour
    (10, 300),   # 10+ fails → 5 minutes
    (5,  60),    # 5+ fails  → 1 minute
]

# Season 7: server-side auto-spinning
AUTO_SPIN_INTERVAL_SECONDS = 3.0   # 1 spin every 3 seconds
MAX_SPINS_PER_TICK         = 100  # Season 8: capped auto-spin (was 100800)
CATCH_UP_THRESHOLD         = 10    # above this many pending spins, use summary mode

# Auto-fish AFK catch-up
AUTO_FISH_INTERVAL_SECONDS = 6.0   # 1 auto-fish tick every 6 seconds
MAX_FISH_CATCHUP_TICKS     = 14_400  # cap at 24 hours (86400s / 6s)
FISH_CATCHUP_THRESHOLD     = 2     # min missed ticks before catch-up fires

# Happy Hour: 9pm–10pm BST (20:00–21:00 UTC)
HAPPY_HOUR_START_UTC = 20
HAPPY_HOUR_END_UTC   = 21

REGEN_SHIELD_RECHARGE_WINS = 5

# T215: Guard Charge passive regen — 1 charge every N spins.
# The shop description claims this mechanic exists; previously it did not.
# Applied in the /api/spin handler after the win/loss resolution.
GUARD_CHARGE_RECHARGE_SPINS = 50
GUARD_CHARGE_MAX = 3

DEVICE_COOKIE = 'device_id'
DEVICE_COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year
