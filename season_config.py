"""Season 9 "Tides" config. seasons.py reads these instead of hardcoded values."""

SEASON_CONFIG = {
    'name': 'Tides',
    'player_facing_number': 9,
    'theme_item': 'page_season9',
    'community_pot_target': 40000,
    'rollover_weekday': 4,  # Friday, as in datetime.weekday() (Monday = 0)
    'rollover_hour': 21,
    'rollover_tz': 'Europe/London',
}
