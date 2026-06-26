"""Tests for T97 (wheel canvas redraw on wheel-mode change).

T97 ACs covered:
  1-3. Manual / UI verification (covered by MANUAL_TEST_RESULTS.md and the
       Playwright check described in the ticket).
  4. The redraw useEffect's deps no longer include wheelProbabilities, so
       React 18's batching no longer causes stale-state redraws.
  5. The spin handler now calls drawWheel explicitly after setting
       wheelProbabilities, so the gravity drift is visualized immediately.
"""
import os

import pytest

JSX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'static', 'app.jsx',
)


def _read_src():
    with open(JSX_PATH, 'r') as f:
        return f.read()


def test_redraw_effect_uses_trimmed_deps():
    """T97 AC#4: the redraw useEffect's deps are [wheelTheme, activeWheelMode]
    and must NOT include wheelProbabilities. The fix removes the stale-closure
    window that caused the canvas to keep showing the previous mode."""
    src = _read_src()
    marker = 'drawWheel(canvas, wheelTheme, activeWheelMode'
    assert marker in src, "redraw useEffect must call drawWheel"
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if marker in line:
            window = '\n'.join(lines[i:i + 5])
            assert 'wheelTheme' in window, (
                "T97 AC#4: wheelTheme must be in the redraw effect deps"
            )
            assert 'activeWheelMode' in window, (
                "T97 AC#4: activeWheelMode must be in the redraw effect deps"
            )
            assert 'wheelProbabilities' not in window, (
                "T97 AC#4: wheelProbabilities must NOT be in the redraw "
                "effect deps (its inclusion caused the React 18 closure bug)"
            )
            return
    pytest.fail("Could not find the redraw useEffect")


def test_active_wheel_mode_ref_defined():
    """T97: activeWheelModeRef is defined near wheelProbabilitiesRef and has
    a useEffect mirroring it. The ref lets the spin handler read the latest
    activeWheelMode from a closure that has stale state."""
    src = _read_src()
    assert 'activeWheelModeRef' in src, (
        "T97: activeWheelModeRef must be defined in GameApp"
    )
    assert 'const activeWheelModeRef' in src, (
        "T97: activeWheelModeRef must be declared with useRef"
    )
    assert (
        "useEffect(() => { activeWheelModeRef.current = activeWheelMode; }, "
        "[activeWheelMode]);"
    ) in src, (
        "T97: activeWheelModeRef must be mirrored by a useEffect on "
        "activeWheelMode"
    )


def test_spin_handler_calls_drawWheel_after_setWheelProbabilities():
    """T97 AC#5: after the spin handler sets wheelProbabilities, it must
    call drawWheel explicitly with the fresh distribution so the gravity
    drift (or any new per-mode distribution) is visualized.

    T102 added a few more state syncs (stakePct, wagerLastStake, maxStakePct)
    between setWheelProbabilities and the drawWheel call. Window widened
    from 8 to 20 lines to accommodate.
    """
    src = _read_src()
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if 'setWheelProbabilities(data.wheel_probabilities)' in line:
            window = '\n'.join(lines[i:i + 20])
            assert 'drawWheel(' in window, (
                "T97 AC#5: the spin handler must call drawWheel(...) "
                "explicitly after setWheelProbabilities(data.wheel_probabilities) "
                "so gravity drift is visualized. None found within 20 lines."
            )
            assert 'activeWheelModeRef.current' in window, (
                "T97 AC#5: the explicit drawWheel call should use "
                "activeWheelModeRef.current for the mode arg (mirrors the "
                "handleWheelModeChange pattern)."
            )
            assert 'wheelThemeRef.current' in window, (
                "T97 AC#5: the explicit drawWheel call should use "
                "wheelThemeRef.current || 'default' for the theme arg."
            )
            return
    pytest.fail("Could not find setWheelProbabilities(data.wheel_probabilities)")


def test_handleWheelModeChange_clears_wheelProbabilities_and_calls_drawWheel_synchronously():
    """T97 R2: handleWheelModeChange must clear wheelProbabilities AND call
    drawWheel synchronously to force an immediate redraw. The redraw useEffect
    is not firing reliably for activeWheelMode changes in this React 18 build,
    so the handler must do the redraw itself. On failure (API error) the
    handler must restore the previous mode and re-draw it."""
    src = _read_src()
    lines = src.splitlines()
    start = None
    for i, line in enumerate(lines):
        if 'const handleWheelModeChange = useCallback(async (mode)' in line:
            start = i
            break
    assert start is not None, "handleWheelModeChange not found"
    body = '\n'.join(lines[start:start + 70])
    assert 'setActiveWheelMode(mode)' in body, (
        "handleWheelModeChange must set the new active mode"
    )
    assert 'setWheelProbabilities(null)' in body, (
        "T97: handleWheelModeChange must still call setWheelProbabilities(null) "
        "to drop the previous mode's distribution"
    )
    # T97 R2: the handler must call drawWheel synchronously with the new
    # mode, then again with the previous mode in the !ok branch. The
    # redraw useEffect does not fire reliably here, so the handler is the
    # source of truth for the visible wheel change.
    assert 'drawWheel(canvasRef.current' in body, (
        "T97 R2: handleWheelModeChange must call drawWheel(canvasRef.current, "
        "...mode..., null) synchronously after setActiveWheelMode, and again "
        "with the previous mode in the !ok branch."
    )
    assert 'wheelThemeRef.current || \'default\'' in body, (
        "T97 R2: the synchronous drawWheel calls must use "
        "wheelThemeRef.current || 'default' for the theme arg"
    )
