"""Tests for T99: wager panel UI doesn't reflect server-side mode-switch resets.

T76 makes the server reset wager_streak / wager_insurance_armed /
double_down_pending / gravity_drift on a mode change, and the response
already includes those four values. T99 ensures the frontend's
handleWheelModeChange reads them and updates the corresponding React state.
"""
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


def test_wheel_mode_response_includes_reset_fields():
    """T76 + T99 AC#1: the /api/wheel-mode response must include
    wager_streak, wager_insurance_armed, double_down_pending, gravity_drift
    when the mode actually changes (so the frontend can sync)."""
    src = _read_game_py()
    # The four reset fields should be set in the response dict inside the
    # `if mode != current_mode` branch.
    assert "response['wager_streak'] = 0" in src, (
        "T76/T99: wheel-mode response must include 'wager_streak = 0' "
        "on a real mode change"
    )
    assert "response['wager_insurance_armed'] = False" in src, (
        "T76/T99: wheel-mode response must include 'wager_insurance_armed = False' "
        "on a real mode change"
    )
    assert "response['double_down_pending'] = False" in src, (
        "T76/T99: wheel-mode response must include 'double_down_pending = False' "
        "on a real mode change"
    )
    assert "response['gravity_drift'] = 0" in src, (
        "T76/T99: wheel-mode response must include 'gravity_drift = 0' "
        "on a real mode change"
    )


def test_handleWheelModeChange_reads_all_four_reset_fields():
    """T99 AC#6: handleWheelModeChange must read the four reset fields from
    the /api/wheel-mode response and update the corresponding React state.
    Before the fix, the success branch only updated wheel_probabilities and
    gravity_drift, so the panel would show stale 'armed' indicators /
    hot-streak badge after a mode switch."""
    src = _read_jsx()
    # All four setter calls must be present in the handler.
    # We accept any spelling of the call as long as it appears in the file.
    assert "setWagerStreak(data.wager_streak)" in src, (
        "T99: handleWheelModeChange must call setWagerStreak(data.wager_streak) "
        "in its success branch"
    )
    assert "setWagerInsuranceArmed(data.wager_insurance_armed)" in src, (
        "T99: handleWheelModeChange must call setWagerInsuranceArmed(data.wager_insurance_armed) "
        "in its success branch"
    )
    assert "setDoubleDownPending(data.double_down_pending)" in src, (
        "T99: handleWheelModeChange must call setDoubleDownPending(data.double_down_pending) "
        "in its success branch"
    )
    assert "setGravityDrift(data.gravity_drift)" in src, (
        "T99: handleWheelModeChange must call setGravityDrift(data.gravity_drift) "
        "in its success branch (T80 already required this; we re-assert it here)"
    )


def test_handleWheelModeChange_restores_wager_state_on_failure():
    """T99 AC#5: if the /api/wheel-mode call fails, the wager panel must
    roll back to its pre-click state — the four captured values must be
    restored in the !ok branch."""
    src = _read_jsx()
    # The capture pattern (BEFORE the optimistic update) — all four prev*
    # variables.
    assert 'const prevStreak = wagerStreak' in src, (
        "T99: handleWheelModeChange must capture prevStreak = wagerStreak "
        "before the optimistic update"
    )
    assert 'const prevInsuranceArmed = wagerInsuranceArmed' in src, (
        "T99: handleWheelModeChange must capture prevInsuranceArmed before the optimistic update"
    )
    assert 'const prevDoubleDownPending = doubleDownPending' in src, (
        "T99: handleWheelModeChange must capture prevDoubleDownPending before the optimistic update"
    )
    assert 'const prevGravityDrift = gravityDrift' in src, (
        "T99: handleWheelModeChange must capture prevGravityDrift before the optimistic update"
    )
    # The restore pattern (in the !ok branch) — all four setters with the
    # prev* values.
    assert 'setWagerStreak(prevStreak)' in src, (
        "T99: on failure, handleWheelModeChange must restore "
        "setWagerStreak(prevStreak)"
    )
    assert 'setWagerInsuranceArmed(prevInsuranceArmed)' in src, (
        "T99: on failure, handleWheelModeChange must restore "
        "setWagerInsuranceArmed(prevInsuranceArmed)"
    )
    assert 'setDoubleDownPending(prevDoubleDownPending)' in src, (
        "T99: on failure, handleWheelModeChange must restore "
        "setDoubleDownPending(prevDoubleDownPending)"
    )
    assert 'setGravityDrift(prevGravityDrift)' in src, (
        "T99: on failure, handleWheelModeChange must restore "
        "setGravityDrift(prevGravityDrift)"
    )
