// Season 8: shared number formatting module.
// Used everywhere wins/losses/costs are displayed.
//
// T227: extended tier support and scientific notation for huge values.
// Old version only handled <1B; players can now legitimately have
// wins > 1e15 (dylan: 2.2e14 cumulative; previous seasons: 1e50+).
// New tier ladder:
//
//   < 1e3            "999"          (integer)
//   1e3 .. 1e6       "1.2K"         (1 decimal, drop trailing .0)
//   1e6 .. 1e9       "1.23M"        (2 decimals)
//   1e9 .. 1e12      "1.23B"        (2 decimals)
//   1e12 .. 1e15     "1.23T"        (2 decimals)
//   1e15+            "1.23e+15"     (scientific, 2 decimals)
//
// Inputs may be Number, string (NUMERIC serialised by psycopg2), or
// Decimal-like. We coerce to Number via Number() which handles all
// three. Values above Number.MAX_SAFE_INTEGER (~9e15) lose precision
// in JavaScript's float representation; this is a pre-existing
// condition for `wins` and `legacy_wins` (already NUMERIC) and is
// acceptable since the display is rounded to 2 decimal places
// anyway. (Postgres NUMERIC values round-trip through JSON as
// numbers — at the cost of precision above 9e15 — and the display
// rounding masks the loss.)
//
// Negative numbers are handled (prefix '-' only, no parens).
// null / undefined / NaN / Infinity return '0' or '∞' as appropriate.
(function () {
    'use strict';

    // Strip trailing zeros from a decimal-formatted string.
    // "1.50" → "1.5", "1.00" → "1", "1500.00" → "1500", "0.50" → "0.5".
    function _trimZeros(s) {
        if (s.indexOf('.') === -1) return s;
        return s.replace(/0+$/, '').replace(/\.$/, '');
    }

    function format_wins(n) {
        if (n === null || n === undefined) return '0';
        var num = Number(n);
        if (isNaN(num)) return '0';
        if (num === Infinity)  return '∞';
        if (num === -Infinity) return '-∞';

        var neg = num < 0;
        var abs = Math.abs(num);

        var str;
        if (abs < 1e3) {
            // Integer for small values, no decimals.
            str = String(Math.round(abs));
        } else if (abs < 1e6) {
            // K tier: 1 decimal (the user-facing style "1.2K")
            str = _trimZeros((abs / 1e3).toFixed(1)) + 'K';
        } else if (abs < 1e9) {
            // M tier: 2 decimals
            str = _trimZeros((abs / 1e6).toFixed(2)) + 'M';
        } else if (abs < 1e12) {
            // B tier: 2 decimals
            str = _trimZeros((abs / 1e9).toFixed(2)) + 'B';
        } else if (abs < 1e15) {
            // T tier: 2 decimals
            str = _trimZeros((abs / 1e12).toFixed(2)) + 'T';
        } else {
            // Scientific notation for 1e15+. toExponential(2) gives
            // "1.23e+15" style which is unambiguous and fits the
            // narrowest columns (8 chars).
            str = abs.toExponential(2);
        }
        return neg ? '-' + str : str;
    }

    // Export for use by app.jsx (global, since no module system)
    window.format_wins = format_wins;
})();
