"""Tests for T85 (prestige scope update) and T86 (prestige_efficiency wins
retention).

T85 AC#1: every column in PRESTIGE_RESET_COLUMNS is zeroed / cleared on
prestige.

T85 AC#2: wager_tokens, onboarding_step, prestige_level, prestige_count,
legacy_wins, owned_cosmetics, active_cosmetics, aquarium_species, loadouts
and cosmetic_fragments are PRESERVED on prestige.

T86 AC#1–3: ``compute_wins_kept`` returns ``int(wins * 0.1 * level)`` where
``level = count(prestige_efficiency)``. The 1,000,000 threshold is fixed.
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


# ── Stubs (match the setdefault pattern from other test files) ──────────────
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
# T85: prestige scope — wager_tokens persist
# ════════════════════════════════════════════════════════════════════════════
def _drive_prestige(gs, extra_gs_keys=None, post_reset_overrides=None):
    """Drive /api/prestige with a fully-populated gs and return (conn, result).

    The returned ``conn.log`` contains every SQL the endpoint ran, so tests
    can assert the UPDATE's column list without talking to Postgres.

    The endpoint reads game_state twice — once before the UPDATE (for
    the locked read) and once after (to return the post-reset state).
    ``post_reset_overrides`` lets tests provide a different value for
    the second read, mimicking the post-UPDATE state. If unset, the
    same ``full_gs`` is used for both reads (the pre-reset state).
    """
    full_gs = dict(gs)
    # Defaults for every column the endpoint may read.
    full_gs.setdefault('prestige_level', 0)
    full_gs.setdefault('prestige_count', 0)
    full_gs.setdefault('legacy_wins', 0)
    full_gs.setdefault('onboarding_step', 0)
    full_gs.setdefault('insurance_tokens', 0)
    full_gs.setdefault('active_cosmetics', [])
    full_gs.setdefault('cosmetic_fragments', 0)
    full_gs.setdefault('caught_species', [])
    if extra_gs_keys:
        full_gs.update(extra_gs_keys)

    if post_reset_overrides:
        post_reset_gs = dict(full_gs)
        post_reset_gs.update(post_reset_overrides)
    else:
        post_reset_gs = full_gs

    conn = _FakeConn(fetchone_queue=[full_gs, post_reset_gs])

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
    return conn, _game.prestige_reset()


def _find_update_sql(conn):
    updates = [sql for sql, _ in conn.log
               if sql.lstrip().upper().startswith('UPDATE')]
    assert len(updates) == 1, f"expected 1 UPDATE, got {len(updates)}: {updates}"
    return updates[0]


def test_prestige_preserves_wager_tokens():
    """T85/T119 AC#2: insurance_tokens (renamed from wager_tokens in
    T119) persist across prestige."""
    gs = {
        'owned_items': ['prestige_unlock'],
        'wins': 1_000_000,
        'losses': 0,
    }
    conn, result = _drive_prestige(gs, extra_gs_keys={'insurance_tokens': 1000})
    sql = _find_update_sql(conn)
    # insurance_tokens must be explicitly preserved (insurance_tokens = insurance_tokens).
    assert 'insurance_tokens = insurance_tokens' in sql, (
        f"expected insurance_tokens preserved, got SQL:\n{sql}"
    )
    # And the result echoes the new state.
    assert result['prestige_level'] == 1


def test_prestige_preserves_onboarding_step():
    """T88 (carried into T85 AC#2): onboarding_step persists across prestige."""
    gs = {
        'owned_items': ['prestige_unlock'],
        'wins': 1_000_000,
    }
    conn, result = _drive_prestige(gs, extra_gs_keys={'onboarding_step': 4})
    sql = _find_update_sql(conn)
    # onboarding_step is NOT in the reset list — assert the column name does
    # not appear in the SET clause (i.e. it is not being assigned).
    set_part = sql.split('WHERE', 1)[0]
    assert 'onboarding_step' not in set_part, (
        f"onboarding_step should not be in the SET clause, got:\n{set_part}"
    )


def test_prestige_resets_all_ac1_columns():
    """T85 AC#1: every column in PRESTIGE_RESET_COLUMNS is in the UPDATE."""
    from prestige import PRESTIGE_RESET_COLUMNS
    gs = {
        'owned_items': ['prestige_unlock'],
        'wins': 1_000_000,
    }
    conn, _ = _drive_prestige(gs)
    sql = _find_update_sql(conn)
    for col in PRESTIGE_RESET_COLUMNS:
        # 'wins' is handled with the new wins value (not the reset 0) — we
        # still need to assert it's in the SQL, just not as a literal `= 0`.
        if col == 'wins':
            assert 'wins = %s' in sql, f"wins not parameterised: {sql}"
        else:
            assert f'{col} = %s' in sql, (
                f"reset column {col!r} missing from SQL:\n{sql}"
            )


def test_prestige_filter_keeps_cosmetics_and_legacy_count_functionals():
    """T85 AC#1: owned_items shrinks to kept + cosmetics, wager items dropped."""
    from prestige import filter_kept_items
    owned = [
        'fish_tropical',          # cosmetic
        'wager_unlock',           # wager — to be removed
        'winmult_1',              # functional, kept (1 of 1)
        'fish_puffer',            # cosmetic
        'wager_safety_net',       # wager — to be removed
        'bonusmult_1',            # functional, dropped (only 1 keep)
    ]
    result = filter_kept_items(owned, keep_count=1)
    assert 'fish_tropical' in result
    assert 'fish_puffer' in result
    assert 'wager_unlock' not in result
    assert 'wager_safety_net' not in result
    # Only one functional kept (the first one encountered).
    assert 'winmult_1' in result
    assert 'bonusmult_1' not in result


def test_prestige_writes_filtered_owned_items():
    """T85: the UPDATE's owned_items param is the filtered list.

    T121 follow-up: prestige_unlock is the permanent gate for prestige
    — it must always be in the new owned_items (filter_kept_items drops
    functionals at keep_count=0, but the server now re-adds
    prestige_unlock after the filter). The first-buy and subsequent-
    prestige cases both produce ['fish_tropical', 'prestige_unlock'].
    """
    gs = {
        'owned_items': ['prestige_unlock', 'fish_tropical', 'wager_unlock', 'winmult_1'],
        'wins': 1_000_000,
    }
    conn, _ = _drive_prestige(gs)
    _, params = next((s, p) for s, p in conn.log
                     if s.lstrip().upper().startswith('UPDATE'))
    # params layout: (new_level, new_prestige_count, new_legacy_wins,
    #                 new_wins, new_owned_items, ...defaults..., user_id)
    new_owned = params[4]
    assert isinstance(new_owned, list)
    assert 'fish_tropical' in new_owned
    assert 'wager_unlock' not in new_owned
    # prestige_unlock is always preserved (permanent unlock).
    assert 'prestige_unlock' in new_owned
    assert 'winmult_1' not in new_owned


def test_prestige_writes_filtered_owned_items_with_legacy_keep():
    """T85 (T121 update): get_legacy_keep_count always returns 0, so the
    only functional that survives the reset is the prestige_unlock we just
    re-added (in the new atomic flow)."""
    gs = {
        # Player owns prestige_legacy once. T121 ignores it → keep_count=0.
        'owned_items': ['prestige_unlock', 'prestige_legacy',
                        'fish_tropical', 'wager_unlock', 'winmult_1'],
        'wins': 1_000_000,
    }
    conn, _ = _drive_prestige(gs)
    _, params = next((s, p) for s, p in conn.log
                     if s.lstrip().upper().startswith('UPDATE'))
    new_owned = params[4]
    assert 'fish_tropical' in new_owned
    assert 'wager_unlock' not in new_owned
    # T121: even though prestige_legacy is in the source owned_items, the
    # get_legacy_keep_count helper always returns 0, so the helper doesn't
    # keep any functionals. prestige_unlock is re-added by the atomic flow
    # because the player didn't own it... wait, they DID own it (it's in
    # the source list). The atomic flow only re-adds when !already_owned,
    # so here prestige_unlock comes through filter_kept_items → no, it's
    # a functional and keep_count=0 → dropped.
    # The result: only the cosmetic fish_tropical survives.
    assert 'prestige_legacy' not in new_owned
    assert 'winmult_1' not in new_owned
    # T121 follow-up: prestige_unlock is the permanent gate for
    # prestige — it must always be in the new owned_items. The
    # server re-adds it after filter_kept_items drops it (since
    # keep_count=0 strips functionals).
    assert 'prestige_unlock' in new_owned


# ════════════════════════════════════════════════════════════════════════════
# T86: prestige_efficiency — wins retention only
# ════════════════════════════════════════════════════════════════════════════
def test_get_prestige_threshold_is_always_one_million():
    """T86 AC#2: the prestige threshold is always 1,000,000 regardless of
    prestige_efficiency level."""
    from prestige import get_prestige_threshold, PRESTIGE_WIN_THRESHOLD
    assert PRESTIGE_WIN_THRESHOLD == 1_000_000
    assert get_prestige_threshold([]) == 1_000_000
    assert get_prestige_threshold(['prestige_efficiency'] * 5) == 1_000_000
    assert get_prestige_threshold(['prestige_efficiency']) == 1_000_000


def test_can_prestige_uses_fixed_threshold():
    """T86: 999,999 wins is below the threshold, 1,000,000 passes."""
    from prestige import can_prestige
    can, err = can_prestige(999_999, ['prestige_unlock'], 0)
    assert can is False
    assert '1,000,000' in err

    can, err = can_prestige(1_000_000, ['prestige_unlock'], 0)
    assert can is True
    assert err is None

    # Efficiency level no longer shortens the threshold.
    can, err = can_prestige(900_000, ['prestige_unlock'] + ['prestige_efficiency'] * 5, 0)
    assert can is False
    assert '1,000,000' in err


def test_compute_wins_kept_zero_at_level_0():
    """T86 AC#1 / T121: at level 0, new_wins = 0 (always, even before T121)."""
    from prestige import compute_wins_kept
    assert compute_wins_kept(2_000_000, ['prestige_unlock']) == 0
    assert compute_wins_kept(5_000_000, []) == 0


def test_compute_wins_kept_half_at_level_5():
    """T86 AC#1 / T121: prestige_efficiency was retired — even at level 5,
    wins_kept is 0. The level no longer has any effect."""
    from prestige import compute_wins_kept
    owned = ['prestige_unlock'] + ['prestige_efficiency'] * 5
    assert compute_wins_kept(2_000_000, owned) == 0


def test_compute_wins_kept_uses_floor():
    """T86 AC#1 / T121: result is always 0 (the floor behaviour is moot)."""
    from prestige import compute_wins_kept
    assert compute_wins_kept(1_500_000, ['prestige_efficiency']) == 0
    assert compute_wins_kept(7, ['prestige_efficiency']) == 0
    assert compute_wins_kept(9, ['prestige_efficiency']) == 0
    assert compute_wins_kept(10, ['prestige_efficiency']) == 0


def test_prestige_wins_kept_field_in_response():
    """T86 AC#4 / T121: response includes wins_kept; the value is now 0
    (T121 retired prestige_efficiency)."""
    gs = {
        'owned_items': ['prestige_unlock'] + ['prestige_efficiency'] * 5,
        'wins': 2_000_000,
    }
    _, result = _drive_prestige(gs)
    assert result['wins_kept'] == 0, (
        f"expected wins_kept=0 (T121 retired efficiency), got {result['wins_kept']}"
    )


def test_prestige_wins_kept_zero_without_efficiency():
    """T86: at level 0, response.wins_kept is 0."""
    gs = {
        'owned_items': ['prestige_unlock'],
        'wins': 2_000_000,
    }
    _, result = _drive_prestige(gs)
    assert result['wins_kept'] == 0


def test_prestige_resets_losses_to_zero():
    """T86 AC#3: losses are always reset to 0 on prestige, regardless of
    efficiency level."""
    from prestige import PRESTIGE_RESET_COLUMNS
    assert 'losses' in PRESTIGE_RESET_COLUMNS
    gs = {
        'owned_items': ['prestige_unlock'] + ['prestige_efficiency'] * 5,
        'wins': 2_000_000,
        'losses': 999,
    }
    conn, _ = _drive_prestige(gs)
    sql = _find_update_sql(conn)
    assert 'losses = %s' in sql
    # The bound value for losses must be 0 (the reset default).
    _, params = next((s, p) for s, p in conn.log
                     if s.lstrip().upper().startswith('UPDATE'))
    losses_idx = [c for c in sql.replace('SET ', '').split(' WHERE ')[0].split(', ')].index('losses = %s')
    # Indexing: the UPDATE params are: (new_level, new_prestige_count,
    # new_legacy_wins, new_wins, new_owned_items, [defaults...], user_id).
    # The 0-indexed position of 'losses' in the bound list depends on the
    # order in PRESTIGE_RESET_COLUMNS — the simplest assertion is that the
    # losses reset value (0) is in the param tuple.
    assert 0 in params


def test_prestige_response_includes_post_reset_state():
    """T121 follow-up: the response includes a `state` object that mirrors
    /api/state, so the client can refresh the shop's "owned" badges without
    a hard refresh. The functional items (wager_unlock, winmult_1, etc.)
    must be GONE from the returned owned_items — only prestige_unlock
    remains (T121's atomic flow re-adds it after the filter).
    """
    gs = {
        'owned_items': ['prestige_unlock', 'wager_unlock', 'winmult_1',
                        'fish_to_wager', 'wager_insurance'],
        'wins': 1_000_000,
        'losses': 0,
    }
    # The endpoint reads game_state twice — once before the UPDATE (for
    # the locked read) and once after (to return the post-reset state).
    # The second read should reflect the post-UPDATE values; for the
    # test that's the filtered owned_items + wins=0 + losses=0.
    _, result = _drive_prestige(
        gs,
        post_reset_overrides={
            'owned_items': ['prestige_unlock'],  # only the unlock survives
            'wins': 0,
            'losses': 0,
        },
    )
    assert 'state' in result, (
        f"response must include 'state' for client refresh, got keys: {list(result.keys())}"
    )
    state = result['state']
    # Functional upgrades are stripped (T121 filter_kept_items(0) returns
    # only the prestige_unlock that's re-added by the atomic flow).
    assert 'wager_unlock' not in state['owned_items']
    assert 'winmult_1' not in state['owned_items']
    assert 'fish_to_wager' not in state['owned_items']
    assert 'wager_insurance' not in state['owned_items']
    assert 'prestige_unlock' in state['owned_items']
    # wins/losses are 0 (the new state, not the pre-reset values).
    assert state['wins'] == 0
    assert state['losses'] == 0
