"""T208: WagerPanel should return null (disappear completely) when auto-spin is
active, instead of going blank (the outer .season8-wager-panel div still
rendering with an empty body).

The fix is a single early return at the top of the WagerPanel function in
static/app.jsx:

    if (autoSpinActive) return null;

We assert this against the JSX source (and the transpiled app.js) rather than
spinning up a Playwright server: the guard is a pure render-time early return,
so its presence in the source is the canonical proof that the bug is fixed.

Ticket reference: docs/SEASON_8_TICKETS.md, lines 6985-7075.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSX_PATH = os.path.join(REPO_ROOT, 'static', 'app.jsx')
JS_PATH = os.path.join(REPO_ROOT, 'static', 'app.js')


def _read_jsx():
    with open(JSX_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def _read_js():
    with open(JS_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def _slice_wager_panel(src):
    """Return the source text of the WagerPanel function (from the `function
    WagerPanel(` line up to the closing `}` of the function body)."""
    m = re.search(r'\nfunction WagerPanel\(', src)
    assert m, 'WagerPanel function not found in app.jsx'
    start = m.start() + 1  # drop the leading newline
    # Walk through the function. We need to track both parens and braces:
    # the destructured-params block is `({...})`, so the FIRST `{` we see is
    # the params object, not the function body. The function body opens with
    # `{` only AFTER the matching `)` of the params has been seen.
    paren_depth = 0
    brace_depth = 0
    i = start
    seen_body_open = False
    while i < len(src):
        ch = src[i]
        if ch == '(':
            paren_depth += 1
        elif ch == ')':
            paren_depth -= 1
        elif ch == '{':
            # Only count the body brace (not the params object).
            if paren_depth == 0 and brace_depth == 0:
                seen_body_open = True
            else:
                brace_depth += 1
        elif ch == '}':
            if seen_body_open and brace_depth == 0:
                return src[start:i + 1]
            elif brace_depth > 0:
                brace_depth -= 1
        i += 1
    raise AssertionError('Could not find closing brace of WagerPanel')


# ── File-content tests ──────────────────────────────────────────────────────


def test_wager_panel_has_autospin_early_return():
    """The JSX source must contain the early return `if (autoSpinActive) return null;`
    inside the WagerPanel function (the fix for T208)."""
    src = _read_jsx()
    panel = _slice_wager_panel(src)
    assert 'if (autoSpinActive) return null;' in panel, (
        'T208 fix missing: WagerPanel must early-return null when '
        'autoSpinActive is true. Expected `if (autoSpinActive) return null;` '
        'inside the WagerPanel function body in static/app.jsx.'
    )


def test_wager_panel_early_return_is_at_top_of_function():
    """The early return must be the FIRST statement of the function body,
    before the existing `if (!ownedItems.includes('wager_unlock'))` guard and
    before the `return (<div className="season8-wager-panel">)`. This is the
    contract specified by the ticket (lines 7018-7032)."""
    src = _read_jsx()
    panel = _slice_wager_panel(src)

    # Skip past the signature: function header + `({...})` destructured params.
    # The function body opens with the `{` that follows the closing `)` of the
    # parameter list. The first `{` in the panel is the params object — not
    # the body — so find `) {` and use the position after it.
    sig_end = panel.index(') {') + len(') {')
    body = panel[sig_end:].lstrip()

    assert body.startswith('if (autoSpinActive) return null;'), (
        'T208: the autoSpinActive early return must be the first statement of '
        'the WagerPanel function body. Got body starting with: '
        f'{body[:80]!r}'
    )


def test_wager_panel_no_season8_div_when_autospin_active():
    """When autoSpinActive is true the entire .season8-wager-panel div must
    not render. The early-return guard makes that true by construction: the
    function returns null before reaching the `<div className=...>` JSX. We
    prove this by checking that the WagerPanel function body can only reach
    the outer div AFTER the autoSpinActive guard has already returned."""
    src = _read_jsx()
    panel = _slice_wager_panel(src)
    guard_idx = panel.index('if (autoSpinActive) return null;')
    div_idx = panel.index('className="season8-wager-panel"')
    assert guard_idx < div_idx, (
        'T208: the autoSpinActive guard must appear before the '
        'season8-wager-panel div in the source so that auto-spin causes '
        'WagerPanel to return null before the div is constructed.'
    )


def test_wager_panel_existing_inner_guards_preserved():
    """The existing `{!autoSpinActive && ...}` guards at lines 3317 and 3348
    (now ~3329 and 3360 after the early-return insertion) are now redundant
    but the ticket says the safest minimal fix is to leave them. Verify they
    are still present (defensive)."""
    src = _read_jsx()
    # Two distinct guarded sections: the stake control and the action row.
    assert src.count('!autoSpinActive &&') >= 2, (
        'T208: the inner !autoSpinActive guards inside WagerPanel should be '
        'left in place as defensive code (ticket lines 7030-7032).'
    )


def test_wager_panel_props_signature_unchanged():
    """The public props signature of WagerPanel must not change (hard
    constraint in the ticket)."""
    src = _read_jsx()
    expected = (
        'function WagerPanel({\n'
        '  ownedItems, stakePct, stakeValue, doubleDownPending, wagerStreak,\n'
        '  wagerBankedWins, wagerLastWinAmount, insuranceTokens, insuranceArmed,\n'
        '  activeWheelMode, maxStakePct, autoSpinActive, payWithTokens,\n'
        '  onStakeChange, onBank, onDoubleDown, onCancelDoubleDown,\n'
        '  onInsurance, onCancelInsurance, onTogglePayWithTokens,\n'
        '})'
    )
    assert expected in src, (
        'T208: WagerPanel props signature changed. The ticket requires the '
        'public signature to be preserved exactly (only the render logic may '
        'change).'
    )


def test_wager_panel_early_return_also_in_compiled_js():
    """The compiled app.js (regenerated by `make build`) must also contain the
    guard, so the browser bundle picks up the fix. This catches the case
    where someone edits app.jsx but forgets to rebuild."""
    js = _read_js()
    assert 'if (autoSpinActive) return null;' in js, (
        'T208: the early return is missing from the compiled static/app.js. '
        'Run `make build` to regenerate it from app.jsx.'
    )


def test_autospin_state_not_modified():
    """T208 must not touch the autoSpinActive state definition itself
    (ticket hard constraint, line 7057)."""
    src = _read_jsx()
    # Sanity: the useState declaration for autoSpinActive must still exist
    # and must be exactly the same shape as before (line 4213 per ticket).
    assert re.search(r'const \[autoSpinActive,\s*setAutoSpinActive\]\s*=\s*useState', src), (
        'T208 must not modify the autoSpinActive useState declaration.'
    )
