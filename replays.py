"""Season 8 replay string generation for big wins.

A replay is a compact base64-encoded JSON string, HMAC-signed with
WHEEL_SECRET_KEY. When a jackpot, double-down win at 5x+, or hot-streak of
10 is achieved, a replay string is generated and included in the spin
response. Players can share it to chat via ``POST /api/replay/share``.

The signature exists because the server-generated string and a
player-forged one would otherwise be indistinguishable -- decode_replay()
would happily decode and return any well-formed base64 JSON a client sent,
letting a player fabricate a fake jackpot/win announcement the moment this
gets wired to post into chat. Signing it now means that path stays safe.
"""

import base64
import hashlib
import hmac
import json
import os
import time


def _signing_key() -> bytes:
    key = os.environ.get('WHEEL_SECRET_KEY', '')
    return key.encode('utf-8')


def _sign(payload: bytes) -> str:
    return hmac.new(_signing_key(), payload, hashlib.sha256).hexdigest()[:16]


def generate_replay(username, mode, stake, result, wins_delta, timestamp=None, double_down=False):
    """Generate an HMAC-signed, base64-encoded replay string.

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
    body = json.dumps(replay, separators=(',', ':')).encode('utf-8')
    replay['h'] = _sign(body)
    payload = json.dumps(replay, separators=(',', ':')).encode('utf-8')
    encoded = base64.b64encode(payload).decode('ascii')
    return f'r:{encoded}'


def decode_replay(replay_string):
    """Decode and verify a replay string back to a dict.

    Returns None if the string is not a valid, correctly-signed replay --
    including one a client constructed by hand rather than one this module
    generated.
    """
    if not replay_string or not replay_string.startswith('r:'):
        return None
    try:
        payload = base64.b64decode(replay_string[2:])
        replay = json.loads(payload)
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(replay, dict) or 'h' not in replay:
        return None
    claimed_sig = replay['h']
    body = {k: v for k, v in replay.items() if k != 'h'}
    expected_sig = _sign(json.dumps(body, separators=(',', ':')).encode('utf-8'))
    if not hmac.compare_digest(claimed_sig, expected_sig):
        return None
    return replay


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
