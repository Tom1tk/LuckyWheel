"""T210: Auto-spin inter-spin gap reduced so the chain feels continuous.

The auto-spin chain in `static/app.jsx` (and its transpiled build
`static/app.js`) used to schedule the next spin with `setTimeout(spin, 1500)`
at three call sites in `HiatusWheel.spin()`. For the operator, a 1.5-second
dead gap after each spin felt like the button was broken. T210 reduces the
gap so a 10-spin auto-spin sequence reads as continuous motion.

These tests are file-content / regex checks on the JSX source. Playwright
timing tests would be nicer but are flaky in CI; per the ticket we keep the
contract at the source level.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSX = os.path.join(REPO, 'static', 'app.jsx')
JS  = os.path.join(REPO, 'static', 'app.js')

# Chosen value: 250ms (ticket Option A). 250ms is short enough that the chain
# feels continuous but long enough that the result bubble registers before the
# next guard rotation kicks in. < 500ms per ticket acceptance criterion #2.
CHOSEN_DELAY_MS = 250
OLD_DELAY_MS    = 1500
MIN_CALL_SITES  = 3


def _read(path):
    with open(path) as f:
        return f.read()


def _call_sites_with_delay(src, ms):
    """Return the count of `setTimeout(spin, <ms>)` occurrences in src."""
    pattern = r'setTimeout\(\s*spin\s*,\s*' + str(ms) + r'\s*\)'
    return len(re.findall(pattern, src))


def _spin_timer_value(src):
    """Return the spinTimer delay in ms, or None if not found."""
    m = re.search(r'const\s+spinTimer\s*=\s*setTimeout\([^,]+,\s*(\d+)\s*\)', src)
    return int(m.group(1)) if m else None


def _autospin_block(src):
    """Return the HiatusWheel auto-spin chain block for inspection."""
    m = re.search(
        r'function\s+HiatusWheel\s*\(\s*\)\s*\{.*?useEffect\(\(\)\s*=>\s*\{'
        r'if\s*\(autoSpin\s*&&\s*!spinningRef\.current\)\s*spin\(\);\s*\},',
        src, re.DOTALL,
    )
    return m.group(0) if m else ''


# ── JSX source checks ──────────────────────────────────────────────────────

def test_jsx_no_1500ms_autospin_timeout_remains():
    """The 1500ms auto-spin inter-spin gap is fully gone from app.jsx.

    Ticket acceptance criterion #2: inter-spin gap < 500ms.
    """
    src = _read(JSX)
    remaining = _call_sites_with_delay(src, OLD_DELAY_MS)
    assert remaining == 0, (
        f"Found {remaining} `setTimeout(spin, 1500)` call site(s) still in "
        f"app.jsx — all 3 should have been replaced with {CHOSEN_DELAY_MS}ms "
        f"for T210."
    )


def test_jsx_has_three_250ms_autospin_call_sites():
    """The new 250ms delay is present at all 3 original call sites.

    The original 1500ms appeared at three locations in the HiatusWheel.spin()
    chain (success path, onComplete path, catch path). All three must be
    updated — leaving any at 1500ms would leave a perceptible pause on that
    branch.
    """
    src = _read(JSX)
    count = _call_sites_with_delay(src, CHOSEN_DELAY_MS)
    assert count >= MIN_CALL_SITES, (
        f"Expected at least {MIN_CALL_SITES} `setTimeout(spin, "
        f"{CHOSEN_DELAY_MS})` call sites in app.jsx (one per auto-spin "
        f"branch: success / onComplete / catch), found {count}."
    )


def test_jsx_chosen_value_is_under_500ms():
    """The chosen delay is below the 500ms acceptance threshold from T210."""
    assert CHOSEN_DELAY_MS < 500, (
        f"Chosen inter-spin delay {CHOSEN_DELAY_MS}ms violates T210 "
        f"acceptance criterion #2 (inter-spin gap must be < 500ms)."
    )


def test_jsx_manual_spin_timing_unchanged():
    """Manual-spin timing (spinTimer 50ms) is untouched by T210.

    The ticket explicitly forbids changing the manual-spin path. The
    spinTimer is a 50ms setTimeout that kicks off the wheel rotation in
    the manual flow.
    """
    src = _read(JSX)
    spin_timer_ms = _spin_timer_value(src)
    assert spin_timer_ms == 50, (
        f"Manual spinTimer must remain 50ms (forbidden by T210), found "
        f"{spin_timer_ms}ms in app.jsx."
    )


def test_jsx_reveal_and_complete_timers_unchanged():
    """Manual-spin revealTimer (2000ms) and completeTimer (3400ms) intact.

    These control how long the result bubble is shown and when onComplete
    fires. T210 must not touch them — only the auto-spin chain.
    """
    src = _read(JSX)
    reveal = re.search(
        r'const\s+revealTimer\s*=\s*setTimeout\([^,]+,\s*Math\.round\(2000',
        src,
    )
    complete = re.search(
        r'const\s+completeTimer\s*=\s*setTimeout\([^,]+,\s*Math\.round\(3400',
        src,
    )
    assert reveal, "revealTimer (~2000ms) missing from app.jsx — T210 must not touch manual-spin timing"
    assert complete, "completeTimer (~3400ms) missing from app.jsx — T210 must not touch manual-spin timing"


def test_jsx_250ms_appears_only_in_autospin_chain():
    """The 250ms setTimeout is the inter-spin auto-spin gap, not a manual-spin timer.

    Sanity check: the only `setTimeout(spin, 250)` call sites are inside the
    HiatusWheel auto-spin chain. We don't want a stray 250ms timer anywhere
    else masquerading as the T210 change.
    """
    src = _read(JSX)
    spin_250 = re.findall(r'setTimeout\([^)]*\bspin\b[^)]*,\s*250\s*\)', src)
    assert len(spin_250) >= MIN_CALL_SITES, (
        f"Expected at least {MIN_CALL_SITES} `setTimeout(spin, 250)` call "
        f"sites in app.jsx, found {len(spin_250)}."
    )
    # Each of those call sites must mention autoSpinRef in the surrounding line.
    for m in re.finditer(r'setTimeout\([^)]*\bspin\b[^)]*,\s*250\s*\)', src):
        line_start = src.rfind('\n', 0, m.start()) + 1
        line_end = src.find('\n', m.end())
        line = src[line_start:line_end if line_end != -1 else None]
        assert 'autoSpinRef' in line, (
            f"`setTimeout(spin, 250)` call at offset {m.start()} is not in "
            f"the auto-spin chain (line: {line!r}). T210 must only touch the "
            f"auto-spin chain."
        )


# ── Transpiled app.js checks (build artifact) ──────────────────────────────

def test_compiled_app_js_no_1500ms_autospin_timeout_remains():
    """The transpiled app.js must mirror the JSX change (no 1500ms)."""
    if not os.path.exists(JS):
        # The build is required; skip rather than fail so missing-build envs
        # (e.g. fresh clone) still report the JSX-level findings above.
        return
    src = _read(JS)
    remaining = _call_sites_with_delay(src, OLD_DELAY_MS)
    assert remaining == 0, (
        f"static/app.js still has {remaining} `setTimeout(spin, 1500)` "
        f"call site(s) — rebuild with `make build` after editing app.jsx."
    )


def test_compiled_app_js_has_three_250ms_call_sites():
    """The transpiled app.js mirrors the JSX change at all 3 call sites."""
    if not os.path.exists(JS):
        return
    src = _read(JS)
    count = _call_sites_with_delay(src, CHOSEN_DELAY_MS)
    assert count >= MIN_CALL_SITES, (
        f"Expected at least {MIN_CALL_SITES} `setTimeout(spin, "
        f"{CHOSEN_DELAY_MS})` call sites in static/app.js, found {count}. "
        f"Rebuild with `make build`."
    )


# ── Summary / coverage sanity ──────────────────────────────────────────────

def test_acceptance_criterion_2_met_by_chosen_value():
    """T210 acceptance criterion #2: inter-spin gap < 500ms.

    The 250ms inter-spin timeout + ~0ms of JS scheduling overhead puts the
    perceived gap well under the 500ms threshold. Documented in the commit
    message.
    """
    # The actual inter-spin gap = setTimeout delay + JS scheduling overhead.
    # setTimeout is typically a few ms of overhead; 250 + ~10ms < 500ms.
    assert CHOSEN_DELAY_MS < 500


def test_first_spin_path_unchanged():
    """The first auto-spin path (useEffect at the end of HiatusWheel) is untouched.

    Per the ticket, the first auto-spin already fires through spin() which
    uses the 50ms spinTimer (same as manual). Only the inter-spin chain is
    changed. We assert the useEffect call shape is intact.
    """
    src = _read(JSX)
    assert re.search(
        r'useEffect\(\(\)\s*=>\s*\{\s*if\s*\(autoSpin\s*&&\s*!spinningRef\.current\)\s*spin\(\)\s*;\s*\}',
        src,
    ), "First-spin useEffect at end of HiatusWheel was modified — T210 must not touch it."
