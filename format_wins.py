"""Python port of static/js/format.js format_wins().

T229: server-side win-number formatting for chat messages. Used by
chat_triggers.py to format win counts in system messages so that
chat output uses the same tier ladder as the rest of the app (T227).

The tier ladder is identical to static/js/format.js:

  < 1e3            "999"          (integer)
  1e3 .. 1e6       "1.2K"         (1 decimal, drop trailing .0)
  1e6 .. 1e9       "1.23M"        (2 decimals)
  1e9 .. 1e12      "1.23B"        (2 decimals)
  1e12 .. 1e15     "1.23T"        (2 decimals)
  1e15+            "1.23e+15"     (scientific, 2 decimals)

Inputs may be int, float, str (NUMERIC serialised by psycopg2), or
Decimal. We coerce via float() which handles all four. Values above
Number.MAX_SAFE_INTEGER (~9e15) lose precision in float64 — this is
a pre-existing condition for the JS formatter too; display rounding
to 2 decimal places masks the loss.

Negative numbers are handled (prefix '-' only, no parens).
null / undefined / NaN return '0'; ±Infinity return '∞' / '-∞'.
"""

import math


def _trim_zeros(s: str) -> str:
    """Drop trailing zeros after a decimal point.

    "1.50" -> "1.5", "1.00" -> "1", "1500.00" -> "1500", "0.50" -> "0.5".
    Mirrors static/js/format.js _trimZeros().
    """
    if "." not in s:
        return s
    return s.rstrip("0").rstrip(".")


def format_wins(n) -> str:
    """Format a win count using the same tier ladder as format.js.

    See module docstring for tier definitions. Behaviour must match
    static/js/format.js format_wins() exactly — see
    tests/test_format_wins_python.py for the parity table.
    """
    if n is None:
        return "0"
    try:
        num = float(n)
    except (TypeError, ValueError):
        return "0"
    if math.isnan(num):
        return "0"
    if num == math.inf:
        return "\u221e"
    if num == -math.inf:
        return "-\u221e"

    neg = num < 0
    abs_val = abs(num)

    if abs_val < 1e3:
        s = str(round(abs_val))
    elif abs_val < 1e6:
        s = _trim_zeros(f"{abs_val / 1e3:.1f}") + "K"
    elif abs_val < 1e9:
        s = _trim_zeros(f"{abs_val / 1e6:.2f}") + "M"
    elif abs_val < 1e12:
        s = _trim_zeros(f"{abs_val / 1e9:.2f}") + "B"
    elif abs_val < 1e15:
        s = _trim_zeros(f"{abs_val / 1e12:.2f}") + "T"
    else:
        s = f"{abs_val:.2e}"

    return ("-" + s) if neg else s
