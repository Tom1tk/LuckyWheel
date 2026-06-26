"""T111: prestige threshold scales with the player's current prestige level.

The threshold to advance from level N to N+1 is:

    round(PRESTIGE_WIN_THRESHOLD * PRESTIGE_LEVEL_MULTIPLIER ** N)

Level 0 stays at 1,000,000 (unchanged from T86). Each subsequent level
multiplies the cost by 1.05 (preliminary value).
"""
import os
import sys
import types
import importlib.util
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_noop = lambda *a, **kw: (lambda f: f)


class _UserMixinStub:
    pass


sys.modules.setdefault('flask', _make_stub(
    'flask',
    Blueprint=lambda *a, **kw: types.SimpleNamespace(route=_noop),
    jsonify=lambda x: x,
    request=None,
))
sys.modules.setdefault('flask_login', _make_stub(
    'flask_login',
    current_user=None,
    login_required=lambda f: f,
    UserMixin=_UserMixinStub,
))
_psycopg2_extras_stub = _make_stub(
    'psycopg2.extras', RealDictCursor=type('RealDictCursor', (), {}))
_psycopg2_stub = _make_stub('psycopg2', extras=_psycopg2_extras_stub)
sys.modules.setdefault('psycopg2', _psycopg2_stub)
sys.modules.setdefault('psycopg2.extras', _psycopg2_extras_stub)
sys.modules.setdefault('extensions', _make_stub(
    'extensions',
    limiter=types.SimpleNamespace(limit=_noop),
    csrf=types.SimpleNamespace(exempt=lambda f: f),
))
sys.modules.setdefault('seasons', _make_stub('seasons',
    ensure_current_season=lambda c: None,
    get_season_info=lambda c: {},
    advance_season=lambda c: None,
))
sys.modules.setdefault('security', _make_stub('security', require_json=lambda: None))


# ── Fake DB plumbing ────────────────────────────────────────────────────────
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


sys.modules.setdefault('db', _make_stub('db', db_connection=_fake_db_connection))


# ── Load game.py with the stubs in place ────────────────────────────────────
_spec = importlib.util.spec_from_file_location(
    'game', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.py'),
)
_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_game)


# ════════════════════════════════════════════════════════════════════════════
# AC#1, AC#2, AC#3: threshold scales by PRESTIGE_LEVEL_MULTIPLIER per level
# ════════════════════════════════════════════════════════════════════════════
def test_prestige_threshold_scales_with_level():
    from prestige import get_prestige_threshold, PRESTIGE_LEVEL_MULTIPLIER, PRESTIGE_WIN_THRESHOLD

    # Level 0: unchanged from T86.
    assert get_prestige_threshold([], 0) == 1_000_000
    # Level 1: 1.05x.
    assert get_prestige_threshold([], 1) == 1_050_000
    # Level 5: round(1M * 1.05^5) = 1,276,282.
    assert get_prestige_threshold([], 5) == round(PRESTIGE_WIN_THRESHOLD * PRESTIGE_LEVEL_MULTIPLIER ** 5)
    assert get_prestige_threshold([], 5) == 1_276_282
    # Level 19: round(1M * 1.05^19) = 2,526,950.
    assert get_prestige_threshold([], 19) == round(PRESTIGE_WIN_THRESHOLD * PRESTIGE_LEVEL_MULTIPLIER ** 19)
    assert get_prestige_threshold([], 19) == 2_526_950

    # Formula holds for every level 0..MAX_PRESTIGE_LEVEL.
    for level in range(21):
        expected = round(PRESTIGE_WIN_THRESHOLD * PRESTIGE_LEVEL_MULTIPLIER ** level)
        assert get_prestige_threshold([], level) == expected, (
            f"level {level}: expected {expected}, "
            f"got {get_prestige_threshold([], level)}"
        )


def test_prestige_threshold_ignores_owned_items():
    """AC#1: only prestige_level matters. owned_items is accepted for
    signature compat with can_prestige but doesn't influence the value."""
    from prestige import get_prestige_threshold

    for level in (0, 1, 5, 19):
        baseline = get_prestige_threshold([], level)
        for owned in (
            ['prestige_unlock'],
            ['prestige_unlock', 'prestige_efficiency'] * 5,
            ['prestige_unlock', 'prestige_legacy'],
        ):
            assert get_prestige_threshold(owned, level) == baseline, (
                f"owned_items changed threshold at level {level}: {owned}"
            )


def test_prestige_threshold_default_level_is_zero():
    """The default keeps the old single-arg call sites working."""
    from prestige import get_prestige_threshold
    assert get_prestige_threshold(['prestige_unlock']) == 1_000_000
    assert get_prestige_threshold([]) == 1_000_000


# ════════════════════════════════════════════════════════════════════════════
# AC#4: can_prestige honours the scaled threshold
# ════════════════════════════════════════════════════════════════════════════
def test_can_prestige_uses_scaled_threshold():
    from prestige import can_prestige, get_prestige_threshold

    owned = ['prestige_unlock']

    # Level 0: 1,000,000 is the boundary, exactly enough.
    can, err = can_prestige(1_000_000, owned, 0)
    assert can is True
    assert err is None

    # Level 0: one win short.
    can, err = can_prestige(999_999, owned, 0)
    assert can is False
    assert '1,000,000' in err

    # Level 1: 1,000,000 is no longer enough.
    threshold_l1 = get_prestige_threshold([], 1)
    assert threshold_l1 == 1_050_000
    can, err = can_prestige(1_000_000, owned, 1)
    assert can is False
    assert '1,050,000' in err

    # Level 1: exactly at the scaled threshold.
    can, err = can_prestige(1_050_000, owned, 1)
    assert can is True
    assert err is None

    # Level 5: 1,000,000 is well short of the scaled threshold.
    can, err = can_prestige(1_000_000, owned, 5)
    assert can is False
    assert '1,276,282' in err


def test_can_prestige_at_max_level_blocked():
    """MAX_PRESTIGE_LEVEL is still the hard cap, regardless of wins."""
    from prestige import can_prestige, MAX_PRESTIGE_LEVEL
    owned = ['prestige_unlock']
    can, err = can_prestige(99_999_999, owned, MAX_PRESTIGE_LEVEL)
    assert can is False
    assert 'Maximum' in err


# ════════════════════════════════════════════════════════════════════════════
# AC#5 (server side): /api/prestige GET and POST use the scaled threshold
# ════════════════════════════════════════════════════════════════════════════
def test_prestige_info_endpoint_returns_scaled_threshold():
    """GET /api/prestige (prestige_info) reflects the player's level."""
    gs = {
        'wins': 1_200_000,
        'owned_items': ['prestige_unlock'],
        'prestige_level': 5,
        'prestige_count': 5,
        'legacy_wins': 0,
    }
    conn = _FakeConn(fetchone_queue=[gs, gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.current_user = types.SimpleNamespace(id=1, username='tester')

    result = _game.prestige_info()
    assert result['prestige_level'] == 5
    assert result['next_threshold'] == 1_276_282
    # 1.2M wins is below the level-5 threshold of 1.28M.
    assert result['can_prestige'] == (False, 'Requires 1,276,282 wins to prestige')


def test_prestige_info_endpoint_at_max_level_no_threshold():
    """At MAX_PRESTIGE_LEVEL, next_threshold is None (no further level)."""
    gs = {
        'wins': 5_000_000,
        'owned_items': ['prestige_unlock'],
        'prestige_level': 20,
        'prestige_count': 20,
        'legacy_wins': 0,
    }
    conn = _FakeConn(fetchone_queue=[gs, gs])

    @contextmanager
    def cm():
        yield conn
    _game.db_connection = cm
    _game.current_user = types.SimpleNamespace(id=1, username='tester')

    result = _game.prestige_info()
    assert result['prestige_level'] == 20
    assert result['next_threshold'] is None


def test_prestige_reset_rejects_when_below_scaled_threshold():
    """POST /api/prestige (prestige_reset) enforces the scaled threshold."""
    from prestige import PRESTIGE_LEVEL_MULTIPLIER

    gs = {
        'wins': 1_000_000,
        'owned_items': ['prestige_unlock'],
        'prestige_level': 1,
        'prestige_count': 1,
        'legacy_wins': 0,
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

    response, status = _game.prestige_reset()
    assert status == 403
    scaled = round(1_000_000 * PRESTIGE_LEVEL_MULTIPLIER ** 1)
    assert str(scaled) in response['error']


def test_prestige_reset_advances_level_uses_new_threshold_for_next():
    """After advancing, the next threshold uses the new level."""
    from prestige import PRESTIGE_LEVEL_MULTIPLIER

    gs = {
        'wins': 1_050_000,
        'owned_items': ['prestige_unlock'],
        'prestige_level': 1,
        'prestige_count': 1,
        'legacy_wins': 0,
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

    response = _game.prestige_reset()
    assert response['prestige_level'] == 2
    # The UPDATE bound new_level to the post-prestige value (2).
    update_params = [p for s, p in conn.log if s.lstrip().upper().startswith('UPDATE')][0]
    assert update_params[0] == 2
    # The level-2 threshold is what the player now has to grind toward.
    assert round(1_000_000 * PRESTIGE_LEVEL_MULTIPLIER ** 2) == 1_102_500


# ════════════════════════════════════════════════════════════════════════════
# AC#6: get_prestige_bonus is unchanged (still +2% per level, +40% cap)
# ════════════════════════════════════════════════════════════════════════════
def test_prestige_bonus_unchanged():
    from prestige import get_prestige_bonus, MAX_PRESTIGE_LEVEL

    assert get_prestige_bonus(0) == 0.0
    assert get_prestige_bonus(1) == 0.02
    assert get_prestige_bonus(5) == 0.10
    assert get_prestige_bonus(10) == 0.20
    assert get_prestige_bonus(19) == 0.38
    # Level 20 (the cap) is +40% win multiplier.
    assert get_prestige_bonus(MAX_PRESTIGE_LEVEL) == 0.40

    # Linear, no compounding.
    for level in range(0, 21):
        assert get_prestige_bonus(level) == level * 0.02


# ════════════════════════════════════════════════════════════════════════════
# Regression: T86 invariants still hold
# ════════════════════════════════════════════════════════════════════════════
def test_efficiency_does_not_shorten_threshold():
    """T86 AC#2: prestige_efficiency never shortens the threshold. T111 keeps
    that property — efficiency only affects win retention, not the cost."""
    from prestige import get_prestige_threshold

    bare = ['prestige_unlock']
    with_eff = ['prestige_unlock'] + ['prestige_efficiency'] * 5
    for level in (0, 1, 5, 19):
        assert get_prestige_threshold(bare, level) == get_prestige_threshold(with_eff, level)


def test_can_prestige_still_requires_unlock_item():
    """The level scaling didn't relax any other gate."""
    from prestige import can_prestige
    can, err = can_prestige(10_000_000, [], 0)
    assert can is False
    assert 'Prestige Unlock' in err
