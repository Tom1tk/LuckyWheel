"""Tests for T70 (effective_stake on spin response) and the wager-stale
React 18 closure fix (stakeRef mirrors stake so handleManualSpin reads
the latest value, not a stale closure)."""
import os

import pytest

JSX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'static', 'app.jsx',
)
GAME_PY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'game.py',
)


def _read_jsx():
    with open(JSX_PATH, 'r') as f:
        return f.read()


def _read_game_py():
    with open(GAME_PY_PATH, 'r') as f:
        return f.read()


def test_spin_response_includes_effective_stake():
    """T70 AC: POST /api/spin with stake=N returns effective_stake=N.

    The fix added two new keys to the resp dict in the spin handler:
    resp['effective_stake'] and resp['wager_last_stake'].

    T102: defaults are now 0.0 / 0 (stake_pct=0 is the safe position).
    """
    src = _read_game_py()
    # Find the resp['stake'] = ... line in the spin handler and verify the
    # two new keys appear right after it.
    assert "resp['stake'] = new_state.get('wager_last_stake', 0)" in src, (
        "T70/T102: resp['stake'] assignment not found in spin handler"
    )
    assert "resp['effective_stake'] = events.get('effective_stake', 0.0)" in src, (
        "T70/T102: spin response must include 'effective_stake' "
        "(sourced from events.get('effective_stake', 0.0))"
    )
    assert "resp['wager_last_stake'] = new_state.get('wager_last_stake', 0)" in src, (
        "T70/T102: spin response must include 'wager_last_stake' "
        "(sourced from new_state.get('wager_last_stake', 0))"
    )


def test_handleManualSpin_reads_stakeRef_not_stake():
    """Wager-stale fix: the manual spin handler must read the stake from
    stakeRef.current, NOT from the React `stakePct` state in the closure.
    Reading from the closure produced stale values (e.g. slider=6 → spin
    used stake=5) because React 18 useCallback in this build is not
    reliably re-creating when `stakePct` changes.

    T102: variable renamed from `stake` to `stakePct` and the default is
    now 0 (the safe position) instead of 1 (the old "1× = safe" hack).
    """
    src = _read_jsx()
    # The handleManualSpin function should pass `stake: stakeRef.current`
    # to the spin API.
    assert 'stake: stakeRef.current' in src, (
        "Wager-stale fix: handleManualSpin must send 'stake: stakeRef.current' "
        "instead of 'stake: stake' so the latest value is used."
    )
    # And the handleStakeChange must update stakeRef.current.
    assert 'stakeRef.current = newStakePct' in src, (
        "Wager-stale fix: handleStakeChange must set stakeRef.current = newStakePct "
        "(T102 renamed the param from newStake) before the React setState so the ref is in sync."
    )


def test_stakeRef_is_defined_and_mirrored():
    """The stakeRef must be defined with useRef near the other refs, and a
    useEffect must mirror the React stakePct state into it.

    T102: default is now `?? 0` (the safe position) instead of `|| 1`.
    """
    src = _read_jsx()
    assert 'const stakeRef' in src, (
        "Wager-stale fix: stakeRef must be declared with useRef"
    )
    assert "useRef(gameState.wager_last_stake ?? 0)" in src, (
        "T102: stakeRef must be initialized from "
        "gameState.wager_last_stake ?? 0 (0% is the safe position)"
    )
    # Mirror effect
    assert "stakeRef.current = stakePct" in src, (
        "T102: a useEffect must mirror stakePct into stakeRef.current"
    )
