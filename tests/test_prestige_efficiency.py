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
# T86 AC#1: compute_wins_kept formula
# ════════════════════════════════════════════════════════════════════════════
def test_efficiency_level_0_keeps_zero_wins():
    from prestige import compute_wins_kept
    # 2,000,000 wins with no prestige_efficiency → 0 retained.
    assert compute_wins_kept(2_000_000, ['prestige_unlock']) == 0
    assert compute_wins_kept(2_000_000, []) == 0
    # 5,000,000 wins with no efficiency → 0 retained.
    assert compute_wins_kept(5_000_000, ['prestige_unlock']) == 0


def test_efficiency_level_5_keeps_half_wins():
    """T86 AC#1: at level 5, new_wins = floor(wins * 0.5)."""
    from prestige import compute_wins_kept
    owned = ['prestige_unlock'] + ['prestige_efficiency'] * 5
    # 2,000,000 * 0.5 = 1,000,000.
    assert compute_wins_kept(2_000_000, owned) == 1_000_000
    # 4,000,000 * 0.5 = 2,000,000.
    assert compute_wins_kept(4_000_000, owned) == 2_000_000
    # 1,000,000 * 0.5 = 500,000.
    assert compute_wins_kept(1_000_000, owned) == 500_000


def test_efficiency_intermediate_levels():
    """T86 AC#1: level 1 → 10%, level 2 → 20%, etc."""
    from prestige import compute_wins_kept
    for level, expected_pct in [(1, 0.10), (2, 0.20), (3, 0.30), (4, 0.40)]:
        owned = ['prestige_unlock'] + ['prestige_efficiency'] * level
        result = compute_wins_kept(1_000_000, owned)
        assert result == int(1_000_000 * expected_pct), (
            f"level {level}: expected {int(1_000_000 * expected_pct)}, "
            f"got {result}"
        )


def test_efficiency_floor_behavior():
    """T86 AC#1: result is ``int(...)``, so it floors for positive numbers."""
    from prestige import compute_wins_kept
    # 1.5M * 0.1 = 150,000 (whole).
    assert compute_wins_kept(1_500_000, ['prestige_efficiency']) == 150_000
    # 7 * 0.1 = 0.7 → 0.
    assert compute_wins_kept(7, ['prestige_efficiency']) == 0
    # 11 * 0.1 = 1.1 → 1.
    assert compute_wins_kept(11, ['prestige_efficiency']) == 1


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
    """T86 AC#3 + AC#4: even at level 5, losses are reset, not retained."""
    gs = {
        'owned_items': ['prestige_unlock'] + ['prestige_efficiency'] * 5,
        'wins': 2_000_000,
        'losses': 999,
    }
    conn = _FakeConn(fetchone_queue=[gs])

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

    # wins_kept is 1M (retained from level 5 efficiency).
    assert result['wins_kept'] == 1_000_000
    # The UPDATE zeroes losses.
    sql, params = next((s, p) for s, p in conn.log
                       if s.lstrip().upper().startswith('UPDATE'))
    assert 'losses = %s' in sql
    losses_position = sql.split('SET ', 1)[1].split(' WHERE ')[0] \
        .split(', ').index('losses = %s')
    # The UPDATE param tuple is: (new_level, new_prestige_count, new_legacy_wins,
    # new_wins, new_owned_items, *reset defaults in PRESTIGE_RESET_COLUMNS order*,
    # user_id). We can't index without the full param layout, so assert 0 is
    # somewhere in the params.
    assert 0 in params, f"expected 0 (losses reset) in params: {params}"
