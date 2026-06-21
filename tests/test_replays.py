"""Unit tests for replays.py — pure functions, no DB or Flask needed."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('WHEEL_SECRET_KEY', 'test-only-key')

import base64
import json

from replays import generate_replay, decode_replay, should_generate_replay


def test_round_trip():
    r = generate_replay('alice', 'volatile', 5, 'jackpot', 12345, timestamp=1700000000)
    decoded = decode_replay(r)
    assert decoded is not None
    assert decoded['u'] == 'alice'
    assert decoded['w'] == 12345


def test_forged_replay_rejected():
    forged = {'u': 'alice', 'm': 'volatile', 's': 5, 'r': 'jackpot',
              'w': 99999999, 't': 1700000000, 'd': False, 'h': 'deadbeefdeadbeef'}
    forged_str = 'r:' + base64.b64encode(json.dumps(forged).encode()).decode()
    assert decode_replay(forged_str) is None


def test_tampered_replay_rejected():
    real = generate_replay('bob', 'steady', 1, 'win', 10, timestamp=1700000001)
    payload = json.loads(base64.b64decode(real[2:]))
    payload['w'] = 999999  # tamper with the win amount, signature now stale
    tampered = 'r:' + base64.b64encode(json.dumps(payload).encode()).decode()
    assert decode_replay(tampered) is None


def test_malformed_input_returns_none():
    assert decode_replay(None) is None
    assert decode_replay('') is None
    assert decode_replay('not-a-replay') is None
    assert decode_replay('r:not-valid-base64!!!') is None


def test_should_generate_replay_triggers():
    assert should_generate_replay(jackpot_hit=True, stake=1, result='win', double_down=False, wager_streak=0)
    assert should_generate_replay(jackpot_hit=False, stake=5, result='win', double_down=True, wager_streak=0)
    assert should_generate_replay(jackpot_hit=False, stake=1, result='win', double_down=False, wager_streak=10)
    assert not should_generate_replay(jackpot_hit=False, stake=1, result='win', double_down=False, wager_streak=5)
