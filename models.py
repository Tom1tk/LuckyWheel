from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


FISH_SKINS = {
    'fish_tropical': {'cost': 250},
    'fish_puffer':   {'cost': 500},
    'fish_octopus':  {'cost': 750},
    'fish_shark':    {'cost': 1_000},
    'fish_dolphin':  {'cost': 1_500},
    'fish_squid':    {'cost': 2_000},
    'fish_turtle':   {'cost': 3_500},
    'fish_crab':     {'cost': 6_000},
    'fish_lobster':  {'cost': 10_000},
    'fish_whale':    {'cost': 20_000},
    'fish_seal':     {'cost': 50_000},
    'fish_shrimp':   {'cost': 150_000},
    'fish_coral':    {'cost': 500_000},
    'fish_mermaid':  {'cost': 1_500_000},
    'fish_croc':     {'cost': 5_000_000},
}

SHOP_ITEMS = {
    # Spin speed
    'speed_boost':    {'cost': 100,          'requires': None},
    'turbo_spin':     {'cost': 1_000,        'requires': 'speed_boost'},
    'hyperspin':      {'cost': 10_000,       'requires': 'turbo_spin'},
    'ultraspin':      {'cost': 100_000,      'requires': 'hyperspin'},
    'maxspin':        {'cost': 1_000_000,    'requires': 'ultraspin'},
    # Auto speed
    'autospeed_1':    {'cost': 200,          'requires': None},
    'autospeed_2':    {'cost': 10_000,       'requires': 'autospeed_1'},
    'autospeed_3':    {'cost': 1_000_000,    'requires': 'autospeed_2'},
    # Win power
    'winmult_1':      {'cost': 200,         'requires': None},
    'winmult_2':      {'cost': 800,         'requires': 'winmult_1'},
    'winmult_3':      {'cost': 3200,        'requires': 'winmult_2'},
    'winmult_4':      {'cost': 12800,       'requires': 'winmult_3'},
    'winmult_5':      {'cost': 51200,       'requires': 'winmult_4'},
    'winmult_6':      {'cost': 204800,      'requires': 'winmult_5'},
    'winmult_7':      {'cost': 819200,      'requires': 'winmult_6'},
    # Bonus power
    'bonusmult_1':    {'cost': 300,         'requires': None},
    'bonusmult_2':    {'cost': 1200,        'requires': 'bonusmult_1'},
    'bonusmult_3':    {'cost': 4800,        'requires': 'bonusmult_2'},
    'bonusmult_4':    {'cost': 20000,       'requires': 'bonusmult_3'},
    'bonusmult_5':    {'cost': 80000,       'requires': 'bonusmult_4'},
    'bonusmult_6':    {'cost': 300000,      'requires': 'bonusmult_5'},
    # Fish size (cosmetic)
    'fishsize_1':     {'cost': 100,          'requires': None},
    'fishsize_2':     {'cost': 5_000,        'requires': 'fishsize_1'},
    'fishsize_3':     {'cost': 500_000,      'requires': 'fishsize_2'},
    # Trails (cosmetic)
    'trail_1':        {'cost': 250,          'requires': None},
    'trail_2':        {'cost': 2_500,        'requires': 'trail_1'},
    'trail_3':        {'cost': 25_000,       'requires': 'trail_2'},
    'trail_4':        {'cost': 250_000,      'requires': 'trail_3'},
    'trail_5':        {'cost': 2_500_000,    'requires': 'trail_4'},
    'trail_6':        {'cost': 25_000_000,   'requires': 'trail_5'},
    # Click power
    'double_click':   {'cost': 100,         'requires': None},
    'double_click_2': {'cost': 400,         'requires': 'double_click'},
    'double_click_3': {'cost': 900,         'requires': 'double_click_2'},
    'double_click_4': {'cost': 2000,        'requires': 'double_click_3'},
    'double_click_5': {'cost': 4500,        'requires': 'double_click_4'},
    'clickfrenzy_1':  {'cost': 300,          'requires': None},
    'clickfrenzy_2':  {'cost': 3_000,        'requires': 'clickfrenzy_1'},
    'clickfrenzy_3':  {'cost': 30_000,       'requires': 'clickfrenzy_2'},
    'clickfrenzy_4':  {'cost': 300_000,      'requires': 'clickfrenzy_3'},
    'clickfrenzy_5':  {'cost': 3_000_000,    'requires': 'clickfrenzy_4'},
    'final_frenzy':   {'cost': 30_000_000,   'requires': 'clickfrenzy_5'},
    # Protection
    'guard':          {'cost': 500,          'requires': None},
    'auto_guard':     {'cost': 50_000,       'requires': 'guard'},
    'regen_shield':   {'cost': 1_500,        'requires': None},
    # Wheel themes (cosmetic)
    'theme_fire':     {'cost': 500,          'requires': None},
    'theme_ice':      {'cost': 5_000,        'requires': 'theme_fire'},
    'theme_neon':     {'cost': 50_000,       'requires': 'theme_ice'},
    'theme_void':     {'cost': 500_000,      'requires': 'theme_neon'},
    'theme_gold':     {'cost': 5_000_000,    'requires': 'theme_void'},
    # Misc cosmetics
    'golden_wheel':   {'cost': 500,          'requires': None},
    'page_season1':   {'cost': 5_000,        'requires': None},
    'page_season2':   {'cost': 5_000,        'requires': None},
    'page_season3':   {'cost': 5_000,        'requires': None},
    'party_mode':     {'cost': 300,          'requires': None},
    'confetti_1':     {'cost': 150,          'requires': None},
    'confetti_2':     {'cost': 1_500,        'requires': 'confetti_1'},
    'confetti_3':     {'cost': 15_000,       'requires': 'confetti_2'},
    # Backgrounds (cosmetic)
    'bg_ocean':       {'cost': 200,          'requires': None},
    'bg_royal':       {'cost': 2_000,        'requires': 'bg_ocean'},
    'bg_inferno':     {'cost': 20_000,       'requires': 'bg_royal'},
    'bg_forest':      {'cost': 200_000,      'requires': 'bg_inferno'},
    'bg_abyss':       {'cost': 2_000_000,    'requires': 'bg_forest'},
    'bg_cosmic':      {'cost': 20_000_000,   'requires': 'bg_abyss'},
    # Bonus functional upgrades
    'fortune_charm':  {'cost': 50_000,       'requires': None},
    'lucky_seven':    {'cost': 100_000,      'requires': None},
    'win_echo':       {'cost': 75_000,       'requires': None},
    'resilience':     {'cost': 5_000_000,    'requires': None},
    'jackpot':        {'cost': 300_000,      'requires': None},
    # Legendary
    'singularity':    {'cost': int(1e67),    'requires': None},
}

ALL_ITEMS = {**FISH_SKINS, **SHOP_ITEMS}
VALID_FISH_IDS = set(FISH_SKINS.keys()) | {'default'}

# Season 3: currency classification for each item.
# 'wins'       — functional items; purchasing deducts from the player's win count.
# 'losses'     — cosmetic items; purchasing deducts from the player's loss count.
# 'fish_clicks'— singularity only (too legendary to change).
_COSMETIC_ITEM_IDS = {
    # Fish skins
    'fish_tropical', 'fish_puffer', 'fish_octopus', 'fish_shark',
    'fish_dolphin', 'fish_squid', 'fish_turtle', 'fish_crab',
    'fish_lobster', 'fish_whale',
    'fish_seal', 'fish_shrimp', 'fish_coral', 'fish_mermaid', 'fish_croc',
    # Fish size
    'fishsize_1', 'fishsize_2', 'fishsize_3',
    # Trails
    'trail_1', 'trail_2', 'trail_3', 'trail_4', 'trail_5', 'trail_6',
    # Wheel themes
    'theme_fire', 'theme_ice', 'theme_neon', 'theme_void', 'theme_gold',
    'golden_wheel',
    # Page themes
    'page_season1', 'page_season2', 'page_season3',
    # Party / confetti
    'party_mode', 'confetti_1', 'confetti_2', 'confetti_3',
    # Backgrounds
    'bg_ocean', 'bg_royal', 'bg_inferno', 'bg_forest', 'bg_abyss', 'bg_cosmic',
}

ITEM_CURRENCY = {}
for _id in ALL_ITEMS:
    if _id == 'singularity':
        ITEM_CURRENCY[_id] = 'fish_clicks'
    elif _id in _COSMETIC_ITEM_IDS:
        ITEM_CURRENCY[_id] = 'losses'
    else:
        ITEM_CURRENCY[_id] = 'wins'

# All infinite upgrades are functional → cost wins.
INFINITE_UPGRADE_CURRENCY = {
    'winmult_inf':   'wins',
    'bonusmult_inf': 'wins',
    'clickmult_inf': 'wins',
}

# Infinite repeatable upgrades — replace old fixed tier chains.
# tier_costs[N] = cost to go from level N → N+1 (for the first len(tier_costs) levels).
# Beyond that, cost = inf_base_cost * inf_scale ** (level - len(tier_costs)).
INFINITE_UPGRADES = {
    'winmult_inf': {
        'db_column':    'winmult_inf_level',
        'tier_costs':   [200, 800, 3200, 12800, 51200, 204800, 819200],
        'inf_base_cost': 1_000_000,
        'inf_scale':     1.4,
    },
    'bonusmult_inf': {
        'db_column':    'bonusmult_inf_level',
        'tier_costs':   [300, 1200, 4800, 20000, 80000, 300000],
        'inf_base_cost': 500_000,
        'inf_scale':     1.4,
    },
    'clickmult_inf': {
        'db_column':    'clickmult_inf_level',
        'tier_costs':   [100, 400, 900, 2000, 4500],
        'inf_base_cost': 10_000,
        'inf_scale':     1.5,
    },
}


def inf_upgrade_cost(item_id, current_level):
    """Cost to advance from current_level to current_level+1."""
    cfg = INFINITE_UPGRADES[item_id]
    tiers = cfg['tier_costs']
    if current_level < len(tiers):
        return tiers[current_level]
    excess = current_level - len(tiers)
    return int(cfg['inf_base_cost'] * cfg['inf_scale'] ** excess)


# Multiplier values at each level (level 0 = nothing owned)
def win_mult_from_level(level):
    if level <= 0: return 1
    if level <= 7: return 1 << level          # 2, 4, 8, 16, 32, 64, 128
    return 128 + (level - 7) * 16             # 144, 160, 176, …


def bonus_mult_from_level(level):
    _fixed = [1, 2, 5, 10, 20, 50, 100]
    if level <= 6: return _fixed[level]
    return 100 + (level - 6) * 10             # 110, 120, 130, …


def click_mult_from_level(level):
    if level <= 0: return 1
    return level + 1                           # 2, 3, 4, 5, 6, 7, 8, …

LOCKOUT_RULES = [
    (20, 3600),  # 20+ fails → 1 hour
    (10, 300),   # 10+ fails → 5 minutes
    (5,  60),    # 5+ fails  → 1 minute
]

REGEN_SHIELD_RECHARGE_WINS = 5

DEVICE_COOKIE = 'device_id'
DEVICE_COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year
