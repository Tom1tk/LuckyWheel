from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


FISH_SKINS = {
    'fish_tropical': {'cost': 25},
    'fish_puffer':   {'cost': 50},
    'fish_octopus':  {'cost': 75},
    'fish_shark':    {'cost': 100},
    'fish_dolphin':  {'cost': 150},
    'fish_squid':    {'cost': 200},
    'fish_turtle':   {'cost': 350},
    'fish_crab':     {'cost': 600},
    'fish_lobster':  {'cost': 1000},
    'fish_whale':    {'cost': 2000},
}

SHOP_ITEMS = {
    # Spin speed
    'speed_boost':    {'cost': 50,          'requires': None},
    'turbo_spin':     {'cost': 200,         'requires': 'speed_boost'},
    'hyperspin':      {'cost': 600,         'requires': 'turbo_spin'},
    'ultraspin':      {'cost': 2000,        'requires': 'hyperspin'},
    'maxspin':        {'cost': 6000,        'requires': 'ultraspin'},
    # Auto speed
    'autospeed_1':    {'cost': 75,          'requires': None},
    'autospeed_2':    {'cost': 300,         'requires': 'autospeed_1'},
    'autospeed_3':    {'cost': 1200,        'requires': 'autospeed_2'},
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
    'fishsize_1':     {'cost': 50,          'requires': None},
    'fishsize_2':     {'cost': 200,         'requires': 'fishsize_1'},
    'fishsize_3':     {'cost': 800,         'requires': 'fishsize_2'},
    # Trails (cosmetic)
    'trail_1':        {'cost': 125,         'requires': None},
    'trail_2':        {'cost': 500,         'requires': 'trail_1'},
    'trail_3':        {'cost': 2000,        'requires': 'trail_2'},
    'trail_4':        {'cost': 7000,        'requires': 'trail_3'},
    'trail_5':        {'cost': 22000,       'requires': 'trail_4'},
    'trail_6':        {'cost': 70000,       'requires': 'trail_5'},
    # Click power
    'double_click':   {'cost': 100,         'requires': None},
    'double_click_2': {'cost': 400,         'requires': 'double_click'},
    'double_click_3': {'cost': 900,         'requires': 'double_click_2'},
    'double_click_4': {'cost': 2000,        'requires': 'double_click_3'},
    'double_click_5': {'cost': 4500,        'requires': 'double_click_4'},
    'clickfrenzy_1':  {'cost': 150,         'requires': None},
    'clickfrenzy_2':  {'cost': 600,         'requires': 'clickfrenzy_1'},
    'clickfrenzy_3':  {'cost': 2400,        'requires': 'clickfrenzy_2'},
    'clickfrenzy_4':  {'cost': 9600,        'requires': 'clickfrenzy_3'},
    'clickfrenzy_5':  {'cost': 38400,       'requires': 'clickfrenzy_4'},
    'final_frenzy':   {'cost': 100000,      'requires': 'clickfrenzy_5'},
    # Protection
    'guard':          {'cost': 300,         'requires': None},
    'regen_shield':   {'cost': 800,         'requires': None},
    # Wheel themes (cosmetic)
    'theme_fire':     {'cost': 250,         'requires': None},
    'theme_ice':      {'cost': 1000,        'requires': 'theme_fire'},
    'theme_neon':     {'cost': 4000,        'requires': 'theme_ice'},
    'theme_void':     {'cost': 12000,       'requires': 'theme_neon'},
    'theme_gold':     {'cost': 40000,       'requires': 'theme_void'},
    # Misc cosmetics
    'golden_wheel':   {'cost': 300,         'requires': None},
    'page_season1':   {'cost': 1000,        'requires': None},
    'party_mode':     {'cost': 150,         'requires': None},
    'confetti_1':     {'cost': 75,          'requires': None},
    'confetti_2':     {'cost': 300,         'requires': 'confetti_1'},
    'confetti_3':     {'cost': 1200,        'requires': 'confetti_2'},
    # Backgrounds (cosmetic)
    'bg_ocean':       {'cost': 100,         'requires': None},
    'bg_royal':       {'cost': 400,         'requires': 'bg_ocean'},
    'bg_inferno':     {'cost': 1600,        'requires': 'bg_royal'},
    'bg_forest':      {'cost': 5000,        'requires': 'bg_inferno'},
    'bg_abyss':       {'cost': 15000,       'requires': 'bg_forest'},
    'bg_cosmic':      {'cost': 50000,       'requires': 'bg_abyss'},
    # Bonus functional upgrades
    'fortune_charm':  {'cost': 500,         'requires': None},
    'lucky_seven':    {'cost': 1000,        'requires': None},
    'win_echo':       {'cost': 750,         'requires': None},
    'resilience':     {'cost': 500000,      'requires': None},
    'jackpot':        {'cost': 3000,        'requires': None},
    # Legendary
    'singularity':    {'cost': 1000000000,  'requires': None},
}

ALL_ITEMS = {**FISH_SKINS, **SHOP_ITEMS}
VALID_FISH_IDS = set(FISH_SKINS.keys()) | {'default'}

# Infinite repeatable upgrades — purchasable unlimited times after prereq tier
INFINITE_UPGRADES = {
    'winmult_inf': {
        'requires':   'winmult_7',
        'base_cost':  1_000_000,
        'cost_scale': 1.4,
        'db_column':  'winmult_inf_level',
    },
    'bonusmult_inf': {
        'requires':   'bonusmult_6',
        'base_cost':  500_000,
        'cost_scale': 1.4,
        'db_column':  'bonusmult_inf_level',
    },
    'clickmult_inf': {
        'requires':   'double_click_5',
        'base_cost':  10_000,
        'cost_scale': 1.5,
        'db_column':  'clickmult_inf_level',
    },
}


def inf_upgrade_cost(item_id, current_level):
    """Cost for the next purchase of an infinite upgrade (at current_level → current_level+1)."""
    cfg = INFINITE_UPGRADES[item_id]
    return int(cfg['base_cost'] * cfg['cost_scale'] ** current_level)

LOCKOUT_RULES = [
    (20, 3600),  # 20+ fails → 1 hour
    (10, 300),   # 10+ fails → 5 minutes
    (5,  60),    # 5+ fails  → 1 minute
]

REGEN_SHIELD_RECHARGE_WINS = 5

DEVICE_COOKIE = 'device_id'
DEVICE_COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year
