"""Focused tests for T86: prestige_efficiency as win retention only.

T86 AC#1: ``compute_wins_kept(wins, owned_items)`` returns
``int(wins * 0.1 * level)`` where ``level = count(prestige_efficiency)``.

T86 AC#2: the 1,000,000 wins cost threshold is NOT reduced by efficiency.

T86 AC#3: prestige_efficiency retains wins only — losses are always reset.
"""
import os
import sys
import types
import importlib.util
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Stub install/teardown (T242) ────────────────────────────────────────────
_SENTINEL = object()
_STUB_PREV = {}
_GAME_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py')
_game = None


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


def _stub_specs():
    """Return (name, factory) pairs for every module this test stubs."""
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
    def __init__(self, log, fetchone_queue=None):
        self.log = log
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
    conn = _FakeConn()
    yield conn


def setup_module(module):
    """Install stubs and load game.py once before any test in this module."""
    global _game
    for name, factory in _stub_specs():
        _STUB_PREV[name] = sys.modules.get(name, _SENTINEL)
        sys.modules[name] = factory()
    _STUB_PREV['db'] = sys.modules.get('db', _SENTINEL)
    sys.modules['db'] = _make_stub('db', db_connection=_fake_db_connection)

    sys.modules.pop('game', None)
    spec = importlib.util.spec_from_file_location('game', _GAME_PATH)
    _game = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_game)


def teardown_module(module):
    """Restore sys.modules and drop the stub-loaded game so the next test
    file sees real modules (or whichever stubs it installs)."""
    global _game
    sys.modules.pop('game', None)
    _game = None
    for name, prev in _STUB_PREV.items():
        if prev is _SENTINEL:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prev
    _STUB_PREV.clear()


# ════════════════════════════════════════════════════════════════════════════
# T86 AC#1 (retired by T121): compute_wins_kept now always returns 0
# ════════════════════════════════════════════════════════════════════════════
def test_efficiency_level_0_keeps_zero_wins():
    from prestige import compute_wins_kept
    # T121: prestige_efficiency is retired — the helper is now a no-op.
    # 2,000,000 wins with no prestige_efficiency → 0 retained.
    assert compute_wins_kept(2_000_000, ['prestige_unlock']) == 0
    assert compute_wins_kept(2_000_000, []) == 0
    # 5,000,000 wins with no efficiency → 0 retained.
    assert compute_wins_kept(5_000_000, ['prestige_unlock']) == 0


def test_efficiency_level_5_keeps_zero_wins():
    """T121: even at level 5, wins are fully reset to 0 (operator removed
    the prestige_efficiency retention mechanic entirely)."""
    from prestige import compute_wins_kept
    owned = ['prestige_unlock'] + ['prestige_efficiency'] * 5
    assert compute_wins_kept(2_000_000, owned) == 0
    assert compute_wins_kept(4_000_000, owned) == 0
    assert compute_wins_kept(1_000_000, owned) == 0


def test_efficiency_intermediate_levels():
    """T121: every level returns 0 (operator removed the level scaling)."""
    from prestige import compute_wins_kept
    for level in (1, 2, 3, 4, 5):
        owned = ['prestige_unlock'] + ['prestige_efficiency'] * level
        result = compute_wins_kept(1_000_000, owned)
        assert result == 0, (
            f"level {level}: T121 retired retention, expected 0, got {result}"
        )


def test_efficiency_floor_behavior():
    """T121: floor behaviour is moot because the function always returns 0
    — but the regression guard stays so anyone re-introducing the formula
    notices immediately."""
    from prestige import compute_wins_kept
    assert compute_wins_kept(1_500_000, ['prestige_efficiency']) == 0
    assert compute_wins_kept(7, ['prestige_efficiency']) == 0
    assert compute_wins_kept(11, ['prestige_efficiency']) == 0


# ════════════════════════════════════════════════════════════════════════════
# T86 AC#2: 1,000,000 threshold is not reduced
# ════════════════════════════════════════════════════════════════════════════
def test_threshold_is_always_one_million():
    """T86 AC#2: get_prestige_threshold returns 1,000,000 for any owned set."""
    from prestige import get_prestige_threshold
    for owned in [
        [],
        ['prestige_unlock'],
        ['prestige_unlock', 'prestige_efficiency'],
        ['prestige_unlock'] + ['prestige_efficiency'] * 5,
        ['prestige_unlock', 'prestige_efficiency', 'prestige_legacy'],
    ]:
        assert get_prestige_threshold(owned) == 1_000_000, (
            f"threshold changed for owned={owned}"
        )


def test_can_prestige_below_threshold_always_rejected():
    """T86 AC#2: efficiency does not unlock prestige at < 1M wins."""
    from prestige import can_prestige
    # 999,999 wins is always below threshold, regardless of efficiency.
    for owned in [
        ['prestige_unlock'],
        ['prestige_unlock', 'prestige_efficiency'],
        ['prestige_unlock'] + ['prestige_efficiency'] * 5,
    ]:
        can, err = can_prestige(999_999, owned, 0)
        assert can is False, f"unexpectedly can prestige with {owned}"
        assert '1,000,000' in err


def test_can_prestige_at_exactly_one_million():
    """T86 AC#2: 1,000,000 wins is the boundary — exactly 1M passes."""
    from prestige import can_prestige
    can, err = can_prestige(1_000_000, ['prestige_unlock'], 0)
    assert can is True
    assert err is None


# ════════════════════════════════════════════════════════════════════════════
# T86 AC#3: losses are always reset, regardless of efficiency
# ════════════════════════════════════════════════════════════════════════════
def test_losses_column_in_prestige_reset_set():
    """T86 AC#3: the prestige UPDATE zeroes losses."""
    from prestige import PRESTIGE_RESET_COLUMNS
    assert 'losses' in PRESTIGE_RESET_COLUMNS


def test_losses_zeroed_at_efficiency_level_5():
    """T86 AC#3 + AC#4 (T121 update): even with the retired items in the
    owned list (staging legacy data), losses are reset to 0 and wins are
    reset to 0."""
    gs = {
        'owned_items': ['prestige_unlock'] + ['prestige_efficiency'] * 5,
        'wins': 2_000_000,
        'losses': 999,
    }
    conn = _FakeConn(fetchone_queue=[gs, gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.request = types.SimpleNamespace(method='POST', json={})
    _game.current_user = types.SimpleNamespace(id=1, username='tester')
    _game.post_system_message = lambda *a, **kw: None
    _game.increment_bounty = lambda *a, **kw: None
    _game.increment_goal = lambda *a, **kw: None
    _game.check_goal_completion = lambda *a, **kw: None
    _game.get_season_info = lambda c: {'season_number': 8}
    _game.get_active_goal = lambda c, s, w: (None, None)

    result = _game.prestige_reset()

    # T121: wins_kept is 0 regardless of prestige_efficiency level.
    assert result['wins_kept'] == 0
    # The UPDATE zeroes losses.
    sql, params = next((s, p) for s, p in conn.log
                       if s.lstrip().upper().startswith('UPDATE'))
    assert 'losses = %s' in sql
    # The UPDATE param tuple is: (new_level, new_prestige_count, new_legacy_wins,
    # new_wins, new_owned_items, *reset defaults in PRESTIGE_RESET_COLUMNS order*,
    # user_id). We can't index without the full param layout, so assert 0 is
    # somewhere in the params.
    assert 0 in params, f"expected 0 (losses reset) in params: {params}"
