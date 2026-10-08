"""Tests for the Season 9 vault payout cap in _resolve_spin.

When a player holds >= 1M wins, a winning spin's wins_delta is capped at
max(1M, pre_spin_wins * 2) and the overflow is moved to wager_banked_wins
(the vault). Below 1M the cap does not apply.
"""
import os
import sys
import types
import importlib.util
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_SENTINEL = object()
_STUB_PREV = {}
_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
_GAME_PATH = os.path.join(_REPO_ROOT, 'game.py')
_game = None
_resolve_spin = None


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


def _noop(*a, **kw):
    return lambda f: f


class _UserMixinStub:
    pass


def _stub_specs():
    _psycopg2_extras_stub = _make_stub(
        'psycopg2.extras', RealDictCursor=type('RealDictCursor', (), {}))
    return [
        ('flask', lambda: _make_stub(
            'flask',
            Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
            jsonify=lambda x: x,
            request=None,
        )),
        ('flask_login', lambda: _make_stub(
            'flask_login',
            current_user=None,
            login_required=lambda f: f,
            UserMixin=_UserMixinStub,
        )),
        ('psycopg2', lambda: _make_stub('psycopg2', extras=_psycopg2_extras_stub)),
        ('psycopg2.extras', lambda: _psycopg2_extras_stub),
        ('extensions', lambda: _make_stub(
            'extensions',
            limiter=types.SimpleNamespace(limit=_noop),
            csrf=types.SimpleNamespace(exempt=lambda f: f),
        )),
        ('seasons', lambda: _make_stub('seasons',
            ensure_current_season=lambda c: None,
            get_season_info=lambda c: {},
            get_latest_winners=lambda c, n: [],
            advance_season=lambda c: None,
        )),
        ('security', lambda: _make_stub('security', require_json=lambda: None)),
    ]


class _FakeCursor:
    def __init__(self, log=None, fetchone_queue=None):
        self.log = log if log is not None else []
        self._fetchone_queue = fetchone_queue or []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql, params))

    def fetchone(self):
        if not self._fetchone_queue:
            return None
        return self._fetchone_queue.pop(0)

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, fetchone_queue=None):
        self.log = []
        self._fetchone_queue = fetchone_queue or []
        self._cursors = [_FakeCursor(self.log, self._fetchone_queue)]

    def cursor(self, cursor_factory=None):
        return self._cursors[0]

    def commit(self):
        pass


@contextmanager
def _fake_db_connection():
    yield _FakeConn()


def setup_module(module):
    global _game, _resolve_spin
    for name, factory in _stub_specs():
        _STUB_PREV[name] = sys.modules.get(name, _SENTINEL)
        sys.modules[name] = factory()
    _STUB_PREV['db'] = sys.modules.get('db', _SENTINEL)
    sys.modules['db'] = _make_stub('db', db_connection=_fake_db_connection)

    # Other test modules stub these app modules at collection time; make sure
    # game.py's real dependency chain re-imports from disk instead of picking
    # up a leftover stub (the same "whichever file was collected first wins
    # the race" fragility T242 describes in conftest.py).
    for name in ('models', 'wagers', 'wheel_modes', 'prestige', 'bounties',
                 'community_goals', 'chat', 'chat_triggers', 'dice', 'fish',
                 'shop', 'loadout'):
        _STUB_PREV[name] = sys.modules.get(name, _SENTINEL)
        sys.modules.pop(name, None)

    sys.modules.pop('game', None)
    spec = importlib.util.spec_from_file_location('game', _GAME_PATH)
    _game = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_game)
    _resolve_spin = _game._resolve_spin


def teardown_module(module):
    sys.modules.pop('game', None)
    _game = _resolve_spin = None
    for name, prev in _STUB_PREV.items():
        if prev is _SENTINEL:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prev
    _STUB_PREV.clear()


def _spin_state(wins, owned=None):
    return {
        'owned': owned or ['wager_unlock'], 'streak': 0, 'best_streak': 0,
        'regen_recharge_wins': 0, 'wins': wins, 'losses': 1000,
        'jackpot_echo_next': False, 'spin_count': 1, 'active_cosmetics': [],
        'proc_streak': 0,
    }


def _spin_ctx(mode='steady'):
    return {
        'effective_win_mult': 2.0, 'bonus_mult': 1, 'jackpot_chance': 0.0,
        'echo_chance': 0.0, 'charm_chance': 0.0, 'resilience_chance': 0.5,
        'proc_streak_level': 0, 'pot_active': False, 'pot_win_pct': 0.505,
        'active_wheel_mode': mode, 'stake_pct': 45,
    }


def _force_win(events):
    """Resolve a spin repeatedly until it is a win (deterministic enough
    with a fixed seed for a bounded number of tries)."""
    return events


def test_win_below_1m_is_uncapped():
    import random
    random.seed(20260731)
    for _ in range(200):
        ns, events = _resolve_spin(**_spin_state(900_000), **_spin_ctx())
        if events['result'] in ('win', 'jackpot'):
            assert events.get('vaulted', 0) == 0, (
                "spins below 1M wins must never vault"
            )
            assert events['wins_delta'] > 0
            return
    raise AssertionError("no win rolled in 200 tries")


def _roll_jackpot(wins, owned, mode='steady', max_tries=500):
    """Resolve spins until a wheel-mode jackpot outcome lands; return events."""
    import random
    random.seed(20260731)
    for _ in range(max_tries):
        ns, events = _resolve_spin(** _spin_state(wins, owned=owned), **_spin_ctx(mode))
        if events['result'] == 'jackpot':
            return events
    raise AssertionError(f"no jackpot rolled in {max_tries} tries")


def test_win_above_1m_caps_and_vaults_overflow():
    """At 2M wins with 45% stake, a steady jackpot (×25) pays ~23M raw; the
    wins_delta must be capped at max(1M, 2M*2) = 4M and the overflow vaulted."""
    owned = ['wager_unlock', 'wager_stake_extend_1', 'wager_stake_extend_2',
             'wager_stake_extend_3']
    events = _roll_jackpot(2_000_000, owned)
    delta = events['wins_delta']
    vaulted = events.get('vaulted', 0)
    assert delta <= 4_000_000, f"wins_delta {delta} exceeded the 4M cap"
    assert vaulted > 0, "a ~23M jackpot at 2M wins must vault overflow"
    # the vault holds at least the overflow that was trimmed
    assert events['wager_banked_wins_delta'] >= vaulted


def test_zealot_win_caps_at_2x():
    """A zealot jackpot (×100) at 10M wins caps at max(1M, 20M) = 20M."""
    owned = ['wager_unlock', 'wager_stake_extend_1', 'wager_stake_extend_2',
             'wager_stake_extend_3']
    events = _roll_jackpot(10_000_000, owned, mode='zealot')
    delta = events['wins_delta']
    assert delta <= 20_000_000, f"zealot jackpot wins_delta {delta} exceeded the 20M cap"
