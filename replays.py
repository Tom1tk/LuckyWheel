"""Season 8 replay string generation for big wins.

A replay is a compact base64-encoded JSON string. When a jackpot,
double-down win at 5x+, or hot-streak of 10 is achieved, a replay
string is generated and included in the spin response. Players can
share it to chat via ``POST /api/replay/share``.
"""

import base64
import json
import time


def generate_replay(username, mode, stake, result, wins_delta, timestamp=None, double_down=False):
    """Generate a base64-encoded replay string.

    Args:
        username: Player username.
        mode: Active wheel mode (e.g. 'volatile').
        stake: Wager stake (1-10).
        result: 'win', 'lose', or 'jackpot'.
        wins_delta: Net wins change from this spin.
        timestamp: Unix timestamp (defaults to now).
        double_down: Whether this was a double-down spin.

    Returns:
        str: Replay string prefixed with 'r:' for chat display.
    """
    if timestamp is None:
        timestamp = int(time.time())

    replay = {
        'u': username,
        'm': mode,
        's': stake,
        'r': result,
        'w': wins_delta,
        't': timestamp,
        'd': double_down,
    }
    payload = json.dumps(replay, separators=(',', ':')).encode('utf-8')
    encoded = base64.b64encode(payload).decode('ascii')
    return f'r:{encoded}'


def decode_replay(replay_string):
    """Decode a replay string back to a dict.

    Returns None if the string is not a valid replay.
    """
    if not replay_string or not replay_string.startswith('r:'):
        return None
    try:
        payload = base64.b64decode(replay_string[2:])
        return json.loads(payload)
    except (ValueError, json.JSONDecodeError):
        return None


def should_generate_replay(jackpot_hit, stake, result, double_down, wager_streak):
    """Check whether a replay should be generated for this spin.

    Trigger conditions (from spec S12):
    - Jackpot hit (any stake)
    - Double-down win at 5x+ stake
    - Hot-streak reaches 10 (max)
    """
    if jackpot_hit:
        return True
    if double_down and result == 'win' and stake >= 5:
        return True
    if wager_streak == 10:
        return True
    return False
