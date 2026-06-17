// Season 8: shared number formatting module.
// Used everywhere wins/losses/costs are displayed.
(function () {
    'use strict';

    function format_wins(n) {
        if (n === null || n === undefined) return '0';
        var num = Number(n);
        if (isNaN(num)) return '0';
        var neg = num < 0;
        var abs = Math.abs(num);

        var str;
        if (abs < 1000) {
            str = String(abs);
        } else if (abs < 1_000_000) {
            // comma-grouped
            str = abs.toLocaleString('en-US', { maximumFractionDigits: 0 });
        } else if (abs < 1_000_000_000) {
            // compact: 8.42M
            str = (abs / 1_000_000).toFixed(2) + 'M';
        } else {
            // compact: 8.42B
            str = (abs / 1_000_000_000).toFixed(2) + 'B';
        }
        return neg ? '-' + str : str;
    }

    // Export for use by app.jsx (global, since no module system)
    window.format_wins = format_wins;
})();
