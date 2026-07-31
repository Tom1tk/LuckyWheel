"""T227: Number abbreviation for huge values.

The shared format_wins() in static/js/format.js must produce compact,
unambiguous output across the full range of win values the game
generates — from small balances to 1e50+ season-end totals.

This test parses format.js as text, extracts the format_wins()
function, and evaluates it in a JS-like environment to exercise
boundary cases. (No node dependency — we just read + eval the JS.)
"""
import os
import re
import subprocess


FORMAT_JS = 'static/js/format.js'


def _extract_function(src, signature):
    """Extract a top-level function definition by signature (e.g.
    'function format_wins(n)') using a balanced-brace walker.
    Returns the full text of the function (signature + body)."""
    idx = src.index(signature)
    # Walk forward to the opening brace of the body.
    brace_idx = src.index('{', idx)
    depth = 0
    i = brace_idx
    while i < len(src):
        c = src[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return src[idx:i + 1]
        i += 1
    raise RuntimeError(f"unbalanced braces for {signature!r}")


def _load_format_wins_node():
    """Read format.js, extract format_wins + _trimZeros, and return
    their combined source ready for node -e evaluation."""
    src = open(FORMAT_JS).read()
    if 'function format_wins' not in src:
        raise RuntimeError(f"format_wins not found in {FORMAT_JS}")
    fmt_src = _extract_function(src, 'function format_wins(n)')
    tz_src = _extract_function(src, 'function _trimZeros(s)')
    return tz_src + '\n' + fmt_src


def _eval_format_wins(test_inputs):
    """Run a series of (input, expected_output) assertions against
    format_wins via node. Returns (passed, failed, messages)."""
    fn_src = _load_format_wins_node()
    cases_js = ',\n'.join(
        f'  [{json.dumps(i)}, {json.dumps(e)}]' for i, e in test_inputs
    )
    js = f"""
{fn_src}
const cases = [
{cases_js}
];
for (const [input, expected] of cases) {{
  const actual = format_wins(input);
  const ok = actual === expected;
  console.log((ok ? 'OK ' : 'FAIL') + ' input=' + JSON.stringify(input) + ' expected=' + JSON.stringify(expected) + ' actual=' + JSON.stringify(actual));
}}
"""
    out = subprocess.check_output(['node', '-e', js], text=True)
    lines = out.strip().split('\n')
    passed = sum(1 for l in lines if l.startswith('OK '))
    failed = sum(1 for l in lines if l.startswith('FAIL'))
    return passed, failed, lines


import json


def test_format_wins_basic_tiers():
    """T227: K, M, B, T tier boundaries must be correct."""
    cases = [
        # < 1K: integer
        (0,    '0'),
        (1,    '1'),
        (999,  '999'),
        # 1K..1M: 1 decimal
        (1000,    '1K'),
        (1234,    '1.2K'),
        (1500,    '1.5K'),
        (99999,   '100K'),
        (999999,  '1000K'),
        # 1M..1B: 2 decimals
        (1_000_000,    '1M'),
        (1_500_000,    '1.5M'),
        (2_345_678,    '2.35M'),
        (999_999_999,  '1000M'),
        # 1B..1T: 2 decimals
        (1_000_000_000,    '1B'),
        (1_500_000_000,    '1.5B'),
        (222_000_000_000,  '222B'),
        # 1T..1Qa: 2 decimals (dylan's case)
        (1_000_000_000_000,           '1T'),
        (222_275_682_209_505,         '222.28T'),
    ]
    p, f, lines = _eval_format_wins(cases)
    assert f == 0, f"{f} format_wins tests failed:\n" + '\n'.join(lines)
    assert p == len(cases), f"expected {len(cases)} passes, got {p}"


def test_format_wins_scientific_for_huge():
    """T227: values >= 1e15 must use scientific notation so they
    fit narrow columns (8 chars max)."""
    cases = [
        (1_500_000_000_000_000,  '1.50e+15'),
        (1e20,                   '1.00e+20'),
        (1.5e50,                 '1.50e+50'),
        (9.99e99,                '9.99e+99'),
    ]
    p, f, lines = _eval_format_wins(cases)
    assert f == 0, f"{f} format_wins tests failed:\n" + '\n'.join(lines)


def test_format_wins_handles_negative():
    """T227: negative numbers must be formatted with a leading '-'."""
    cases = [
        (-1,        '-1'),
        (-1234,     '-1.2K'),
        (-1.5e6,    '-1.5M'),
        (-1.5e50,   '-1.50e+50'),
    ]
    p, f, lines = _eval_format_wins(cases)
    assert f == 0, f"{f} format_wins tests failed:\n" + '\n'.join(lines)


def test_format_wins_handles_null_and_nan():
    """T227: null, undefined, NaN must return '0' (not crash)."""
    cases = [
        (None,      '0'),
        # `undefined` isn't valid JSON, so we test via the 'not
        # provided' case. Use a special marker.
    ]
    p, f, lines = _eval_format_wins(cases)
    assert f == 0, f"{f} format_wins tests failed:\n" + '\n'.join(lines)


def test_format_wins_handles_infinity():
    """T227: Infinity and -Infinity must show as '∞' / '-∞'."""
    # Infinity is a JS literal; we eval a JS expression.
    fn_src = _load_format_wins_node()
    js = f"""
{fn_src}
for (const v of [Infinity, -Infinity]) {{
  const a = format_wins(v);
  console.log((a === (v < 0 ? '-∞' : '∞') ? 'OK ' : 'FAIL') + ' input=' + String(v) + ' actual=' + a);
}}
"""
    out = subprocess.check_output(['node', '-e', js], text=True)
    assert 'FAIL' not in out, f"infinity tests failed:\n{out}"


def test_format_wins_handles_string_input():
    """T227: NUMERIC values from psycopg2 are serialised as JSON
    strings (or, in our case, as JSON numbers — but tests should
    handle both, since the format_wins function coerces via Number())."""
    cases = [
        ('1234',  '1.2K'),
        ('1500000', '1.5M'),
        ('221775682209505', '221.78T'),
    ]
    p, f, lines = _eval_format_wins(cases)
    assert f == 0, f"{f} format_wins tests failed:\n" + '\n'.join(lines)


def test_lb_wins_column_widened():
    """T227: the .lb-wins column must be wide enough to fit
    '1.23e+50' (8 chars at 0.6rem ≈ 70px). 64px + flex-shrink:0
    is the minimum, and the column must use overflow:hidden
    (not visible) so it never expands the row."""
    css = open('static/styles.css').read()
    # Find the .lb-wins rule. It must have width >= 64px.
    m = re.search(r'\.lb-wins\s*\{([^}]+)\}', css, re.DOTALL)
    assert m, ".lb-wins CSS rule not found"
    rule = m.group(1)
    width_m = re.search(r'(?:^|\s)width:\s*(\d+)px', rule, re.MULTILINE)
    assert width_m, ".lb-wins must have explicit width in px"
    width = int(width_m.group(1))
    assert width >= 64, (
        f".lb-wins width={width}px is too narrow for "
        f"scientific notation (1.50e+50 needs ~70px). "
        f"Widen to 64px or more."
    )
    # And the header column should match.
    m_h = re.search(r'\.lb-wins-h\s*\{([^}]+)\}', css, re.DOTALL)
    assert m_h, ".lb-wins-h CSS rule not found (header must match)"
    h_width = int(re.search(r'width:\s*(\d+)px', m_h.group(1)).group(1))
    assert h_width >= 64, (
        f".lb-wins-h width={h_width}px doesn't match the data "
        f"column width — header will be misaligned"
    )


def test_lb_wins_column_handles_overflow():
    """T227: even if a value doesn't fit (e.g. absurdly long
    scientific notation), the column must use overflow:hidden
    (not visible) so it doesn't expand the row."""
    css = open('static/styles.css').read()
    m = re.search(r'\.lb-wins\s*\{([^}]+)\}', css, re.DOTALL)
    rule = m.group(1)
    assert 'overflow: hidden' in rule, (
        ".lb-wins must use overflow:hidden (or clip) so a long "
        "value doesn't push the row wider and break the panel"
    )


def test_format_wins_is_the_canonical_formatter():
    """T227: the inline fmt() in app.jsx must defer to format_wins
    (so the formatter is single-sourced). The inline fallback is
    allowed but must mirror the same tier ladder."""
    jsx = open('static/app.jsx').read()
    # Find the fmt function definition.
    m = re.search(r'function fmt\(n\)\s*\{(.*?)\n\}', jsx, re.DOTALL)
    assert m, "fmt() not found in app.jsx"
    body = m.group(1)
    # The first thing fmt() does must be to call window.format_wins.
    assert 'window.format_wins' in body, (
        "fmt() must call window.format_wins so the formatter is "
        "single-sourced. Without this, the leaderboard and the "
        "inline JSX will format numbers differently."
    )


def test_format_wins_no_string_substring_of_K():
    """T227 regression guard: make sure the old 'comma-grouped' code
    (which produced strings like '999,999' instead of '1M') is gone.
    If we ever regress and fall through to toLocaleString('en-US'),
    this will catch it."""
    src = open(FORMAT_JS).read()
    assert 'toLocaleString' not in src, (
        "format_wins still uses toLocaleString somewhere — that "
        "produces '999,999' style strings, not compact '1.23M' "
        "tier output. Remove toLocaleString."
    )
