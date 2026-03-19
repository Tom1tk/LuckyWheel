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
}

SHOP_ITEMS = {
    'speed_boost':    {'cost': 50,          'requires': None},
    'turbo_spin':     {'cost': 200,         'requires': 'speed_boost'},
    'autospeed_1':    {'cost': 75,          'requires': None},
    'autospeed_2':    {'cost': 300,         'requires': 'autospeed_1'},
    'autospeed_3':    {'cost': 1200,        'requires': 'autospeed_2'},
    'winmult_1':      {'cost': 200,         'requires': None},
    'winmult_2':      {'cost': 800,         'requires': 'winmult_1'},
    'winmult_3':      {'cost': 3200,        'requires': 'winmult_2'},
    'winmult_4':      {'cost': 12800,       'requires': 'winmult_3'},
    'bonusmult_1':    {'cost': 300,         'requires': None},
    'bonusmult_2':    {'cost': 1200,        'requires': 'bonusmult_1'},
    'bonusmult_3':    {'cost': 4800,        'requires': 'bonusmult_2'},
    'fishsize_1':     {'cost': 50,          'requires': None},
    'fishsize_2':     {'cost': 200,         'requires': 'fishsize_1'},
    'fishsize_3':     {'cost': 800,         'requires': 'fishsize_2'},
    'trail_1':        {'cost': 125,         'requires': None},
    'trail_2':        {'cost': 500,         'requires': 'trail_1'},
    'trail_3':        {'cost': 2000,        'requires': 'trail_2'},
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
    'shield_1':       {'cost': 250,         'requires': None},
    'iron_shield':    {'cost': 600,         'requires': None},
    'regen_shield':   {'cost': 800,         'requires': None},
    'theme_fire':     {'cost': 250,         'requires': None},
    'theme_ice':      {'cost': 1000,        'requires': 'theme_fire'},
    'theme_neon':     {'cost': 4000,        'requires': 'theme_ice'},
    'golden_wheel':   {'cost': 300,         'requires': None},
    'party_mode':     {'cost': 150,         'requires': None},
    'confetti_1':     {'cost': 75,          'requires': None},
    'confetti_2':     {'cost': 300,         'requires': 'confetti_1'},
    'confetti_3':     {'cost': 1200,        'requires': 'confetti_2'},
    'bg_ocean':       {'cost': 100,         'requires': None},
    'bg_royal':       {'cost': 400,         'requires': 'bg_ocean'},
    'bg_inferno':     {'cost': 1600,        'requires': 'bg_royal'},
    'singularity':    {'cost': 1000000000,  'requires': None},
}

ALL_ITEMS = {**FISH_SKINS, **SHOP_ITEMS}
VALID_FISH_IDS = set(FISH_SKINS.keys()) | {'default'}

LOCKOUT_RULES = [
    (20, 3600),  # 20+ fails → 1 hour
    (10, 300),   # 10+ fails → 5 minutes
    (5,  60),    # 5+ fails  → 1 minute
]

REGEN_SHIELD_RECHARGE_WINS = 3

DEVICE_COOKIE = 'device_id'
DEVICE_COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year
