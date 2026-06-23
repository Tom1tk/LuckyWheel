"""Tests for T80 (dynamic wheel graphic — server-provided probabilities).

T80 ACs covered:
  1-2. Server includes wheel_probabilities in /api/state + spin response
       (covered in test_gravity_mode.py via _current_wheel_probabilities).
  3. Store wheelProbabilities in state (app.jsx).
  4. Add wheelProbabilities to the redraw effect dependency array.
  5. drawWheel() uses wheelProbabilities if provided, falls back to
       WHEEL_MODE_DRAW for backward compat.
  6. For inverted mode, wheel labels swap.
  7. Wheel redraws whenever probabilities change (verified by checking
       the redraw effect includes wheelProbabilities).
"""
import os
import sys

import pytest

JSX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'static', 'app.jsx',
)


def _read_src():
    with open(JSX_PATH, 'r') as f:
        return f.read()


def test_app_jsx_has_wheelProbabilities_state():
    """T80 AC#3: wheelProbabilities state is declared in the GameApp component."""
    src = _read_src()
    # The useState declaration must include 'wheelProbabilities'.
    assert 'setWheelProbabilities' in src, (
        "T80 AC#3: wheelProbabilities state setter must be defined"
    )
    # The state must be initialized from the server-provided value.
    assert 'gameState.wheel_probabilities' in src, (
        "T80 AC#3: wheelProbabilities should be initialized from /api/state"
    )


def test_app_jsx_wheelProbabilities_NOT_in_redraw_effect():
    """T97 reversed T80 AC#4: wheelProbabilities is no longer in the redraw
    useEffect's deps array. Including it caused a React 18 closure/batching
    bug where the canvas kept showing the previous mode's distribution after
    a mode change. The spin handler now calls drawWheel explicitly with the
    fresh distribution (see test_wheel_redraw.py)."""
    src = _read_src()
    marker = 'drawWheel(canvas, wheelTheme, activeWheelMode'
    assert marker in src, "redraw useEffect must call drawWheel"
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if marker in line:
            window = '\n'.join(lines[i:i + 5])
            assert 'wheelProbabilities' not in window, (
                "T97: wheelProbabilities must NOT be in the redraw effect's "
                "dependency array — its inclusion caused the React 18 "
                "stale-closure bug fixed by T97"
            )
            return
    pytest.fail("Could not find the redraw useEffect")


def test_app_jsx_drawWheel_signature_accepts_wheelProbabilities():
    """T80 AC#5: drawWheel() must accept wheelProbabilities as a parameter."""
    src = _read_src()
    assert 'function drawWheel(canvas' in src, "drawWheel signature not found"
    # The signature must include the wheelProbabilities parameter.
    # Find the function signature and check it ends with the new arg.
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if 'function drawWheel(canvas' in line:
            # Concatenate the signature (may span multiple lines).
            sig = line
            for j in range(i + 1, min(i + 5, len(lines))):
                sig += '\n' + lines[j]
                if ')' in lines[j]:
                    break
            assert 'wheelProbabilities' in sig, (
                f"T80 AC#5: drawWheel() must accept wheelProbabilities. "
                f"Signature:\n{sig}"
            )
            return
    pytest.fail("Could not find drawWheel signature")


def test_app_jsx_drawWheel_uses_wheelProbabilities_when_provided():
    """T80 AC#5: drawWheel() must use wheelProbabilities over WHEEL_MODE_DRAW
    when supplied, falling back otherwise."""
    src = _read_src()
    # The fallback table must still be present.
    assert 'WHEEL_MODE_DRAW' in src, "WHEEL_MODE_DRAW fallback table missing"
    # The function must use wheelProbabilities in the modeConfig selection.
    # Find the drawWheel body and check for the wheelProbabilities || fallback pattern.
    assert 'wheelProbabilities || fallback' in src or \
           'wheelProbabilities || WHEEL_MODE_DRAW' in src, (
        "T80 AC#5: drawWheel must use wheelProbabilities when provided"
    )


def test_app_jsx_inverted_mode_swaps_labels():
    """T80 AC#6: in inverted mode the wheel labels swap (LOSE becomes the
    large/green segment, WIN becomes the smaller/red segment)."""
    src = _read_src()
    # The drawWheel function must contain a label-swap for inverted mode.
    assert "isInverted" in src or "'inverted'" in src, (
        "inverted-mode handling missing from drawWheel"
    )
    # The label swap: WIN ↔ LOSE in inverted mode.
    # We check for the conditional label assignments.
    assert "winLabel" in src and "loseLabel" in src, (
        "T80 AC#6: drawWheel must define swapped winLabel/loseLabel vars"
    )


def test_app_jsx_spin_response_syncs_wheelProbabilities():
    """T80 AC#1: the spin response handler must sync wheelProbabilities
    from data.wheel_probabilities."""
    src = _read_src()
    assert 'data.wheel_probabilities' in src, (
        "T80 AC#1: spin response must expose data.wheel_probabilities"
    )


def test_app_jsx_inverted_profile_in_static_table():
    """T80 AC#6: the static WHEEL_MODE_DRAW table for inverted mode must
    reflect the loss-farming profile (35% win / 60% lose / 5% jackpot)."""
    src = _read_src()
    # Find the inverted entry in WHEEL_MODE_DRAW.
    import re
    m = re.search(r"inverted:\s*\{\s*win_pct:\s*(\d+),\s*lose_pct:\s*(\d+),\s*jackpot_pct:\s*(\d+)", src)
    assert m, "inverted entry missing from WHEEL_MODE_DRAW"
    win, lose, jp = int(m.group(1)), int(m.group(2)), int(m.group(3))
    assert win == 35, f"inverted win_pct should be 35, got {win}"
    assert lose == 60, f"inverted lose_pct should be 60, got {lose}"
    assert jp == 5, f"inverted jackpot_pct should be 5, got {jp}"


def test_static_js_wheel_modes_loaded():
    """The shared static/js/wheel-modes.js exists and exposes WHEEL_MODES."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'js', 'wheel-modes.js',
    )
    assert os.path.exists(path), (
        f"static/js/wheel-modes.js must exist for cross-component sharing"
    )
    with open(path, 'r') as f:
        content = f.read()
    assert 'window.WHEEL_MODES' in content, (
        "static/js/wheel-modes.js must expose window.WHEEL_MODES"
    )
    assert 'compute_gravity_probabilities' in content, (
        "static/js/wheel-modes.js must expose compute_gravity_probabilities"
    )
    # The inverted profile must match.
    assert 'loss_pct: 60' in content and 'win_pct: 35' in content, (
        "static/js/wheel-modes.js inverted profile must be 35% win / 60% lose"
    )
