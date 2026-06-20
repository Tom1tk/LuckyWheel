"""Season 8 wheel mode definitions and weekly rotation.

Each mode defines win_pct, loss_pct, jackpot_pct as percentages (0-100).
The mode probabilities replace the old ``secrets.choice(['win', 'lose'])``
50/50 outcome in ``_resolve_spin()``.

Steady and volatile are always available. One rotating mode (inverted,
gravity, or mirror) is available each week based on ISO week number.
"""

from datetime import datetime, timezone


WHEEL_MODES = {
    'steady': {
        'win_pct': 70,
        'loss_pct': 28,
        'jackpot_pct': 2,
        'description': 'Default. Small wins, rare losses, standard jackpot.',
        'jackpot_multiplier': 25,
    },
    'volatile': {
        'win_pct': 45,
        'loss_pct': 50,
        'jackpot_pct': 5,
        'description': 'High variance. Big wins, frequent losses, double jackpot.',
        'jackpot_multiplier': 50,
    },
    'inverted': {
        'win_pct': 60,
        'loss_pct': 35,
        'jackpot_pct': 5,
        'description': 'Losses become small wins — loss streaks still build bonus.',
        'jackpot_multiplier': 25,
    },
    'gravity': {
        'win_pct': 55,
        'loss_pct': 40,
        'jackpot_pct': 5,
        'description': 'Outcomes drift toward the last result — streaks amplify both ways.',
        'jackpot_multiplier': 25,
    },
    'mirror': {
        'win_pct': 65,
        'loss_pct': 30,
        'jackpot_pct': 5,
        'description': 'Two spins resolve simultaneously; player takes the better result.',
        'jackpot_multiplier': 25,
    },
    'singularity': {
        'win_pct': 75,
        'loss_pct': 10,
        'jackpot_pct': 15,
        'description': 'The ultimate mode. Unlocked when the Singularity meter fills.',
        'jackpot_multiplier': 50,
    },
}

# Modes that rotate weekly (index by week_number % 3)
_ROTATING_MODES = ['inverted', 'gravity', 'mirror']


def get_week_number(now=None):
    """Return the ISO week number for the current time (or a given datetime)."""
    now = now or datetime.now(timezone.utc)
    return now.isocalendar().week


def get_rotating_mode(week_number=None):
    """Return the rotating mode name for the given (or current) week."""
    if week_number is None:
        week_number = get_week_number()
    return _ROTATING_MODES[week_number % 3]


def get_available_modes(week_number=None):
    """Return the list of selectable modes for the given (or current) week.

    Always includes 'steady' and 'volatile', plus the weekly rotating mode.
    If the Singularity meter has filled, 'singularity' is also included
    (the caller checks the filled flag and appends it separately).
    """
    return ['steady', 'volatile', get_rotating_mode(week_number)]
