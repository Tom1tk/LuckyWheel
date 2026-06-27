"""Tests for the Python port of format_wins (format_wins.py).

Pins the Python output to the same tier ladder as static/js/format.js
(T227). If a JS tier changes without a corresponding Python port update,
these tests will catch the divergence.

Mirrors the case table in tests/test_format_wins.py but runs against
format_wins.format_wins (Python) instead of evaluating the JS module.
"""

import math
import unittest

from format_wins import format_wins


class TestFormatWinsTierLadder(unittest.TestCase):
    """Tier ladder must match static/js/format.js format_wins()."""

    def test_below_1k(self):
        self.assertEqual(format_wins(0), "0")
        self.assertEqual(format_wins(1), "1")
        self.assertEqual(format_wins(999), "999")

    def test_k_tier_one_decimal(self):
        # 1e3..1e6: 1 decimal, drop trailing .0
        self.assertEqual(format_wins(1000), "1K")
        self.assertEqual(format_wins(1500), "1.5K")
        self.assertEqual(format_wins(1234), "1.23K" if False else "1.2K")  # .1f: "1.2"
        self.assertEqual(format_wins(9999), "10K")
        self.assertEqual(format_wins(10000), "10K")
        self.assertEqual(format_wins(999999), "1000K")  # edge: still K tier

    def test_k_tier_live_data(self):
        # The values currently in chat_messages (pre-T229).
        self.assertEqual(format_wins(10329), "10.3K")
        self.assertEqual(format_wins(76907), "76.9K")
        self.assertEqual(format_wins(101399), "101.4K")
        self.assertEqual(format_wins(450560), "450.6K")
        self.assertEqual(format_wins(460311), "460.3K")
        self.assertEqual(format_wins(833958), "834K")  # .0 dropped

    def test_m_tier_two_decimals(self):
        self.assertEqual(format_wins(1000000), "1M")
        self.assertEqual(format_wins(1500000), "1.5M")
        self.assertEqual(format_wins(2618217), "2.62M")  # dylan S8 live
        self.assertEqual(format_wins(999999999), "1000M")  # edge: still M tier

    def test_b_tier_two_decimals(self):
        self.assertEqual(format_wins(1000000000), "1B")
        self.assertEqual(format_wins(10000000000), "10B")

    def test_t_tier_two_decimals(self):
        self.assertEqual(format_wins(1000000000000), "1T")
        self.assertEqual(format_wins(3405169339238), "3.41T")  # dylan S8 live
        self.assertEqual(format_wins(140463137867975), "140.46T")  # dylan S8 live

    def test_scientific_above_1e15(self):
        self.assertEqual(format_wins(1e15), "1.00e+15")
        self.assertEqual(format_wins(1e50), "1.00e+50")

    def test_scientific_no_leading_space(self):
        # Regression: the SQL '9.99EEEE' format (in migration 069)
        # always prepends a single space (sign-placeholder). The
        # Python port must not. (Postgres bug: btrim is required on
        # the SQL side, see migrations/069_reformat_chat_win_numbers.sql
        # for the rationale.)
        for n in [1e15, 1.5e15, 1.5e16, 1.5e17, 1.5e18, 1.5e19, 1.5e20, 1e50, 1e100]:
            result = format_wins(n)
            self.assertFalse(result.startswith(" "), f"leading space in {result!r} for {n}")
            self.assertFalse(result.endswith(" "), f"trailing space in {result!r} for {n}")


class TestFormatWinsEdgeCases(unittest.TestCase):
    def test_negative(self):
        self.assertEqual(format_wins(-1234), "-1.2K")
        self.assertEqual(format_wins(-140463137867975), "-140.46T")

    def test_null_and_undefined(self):
        # Python: None is our analogue to JS null/undefined.
        self.assertEqual(format_wins(None), "0")

    def test_nan(self):
        self.assertEqual(format_wins(float("nan")), "0")

    def test_infinity(self):
        self.assertEqual(format_wins(float("inf")), "\u221e")
        self.assertEqual(format_wins(float("-inf")), "-\u221e")

    def test_string_input(self):
        # psycopg2 returns NUMERIC columns as str; coerce via float().
        self.assertEqual(format_wins("140463137867975"), "140.46T")
        self.assertEqual(format_wins("2618217"), "2.62M")
        self.assertEqual(format_wins("999"), "999")

    def test_bad_input(self):
        # Unparseable string -> "0", never raise.
        self.assertEqual(format_wins("not a number"), "0")
        self.assertEqual(format_wins(""), "0")
        self.assertEqual(format_wins([]), "0")  # not coercible

    def test_decimal_input(self):
        # Decimal from psycopg2 NUMERIC column.
        from decimal import Decimal
        self.assertEqual(format_wins(Decimal("140463137867975")), "140.46T")
        self.assertEqual(format_wins(Decimal("2618217.5")), "2.62M")  # .5 rounds up

    def test_huge_value_keeps_scientific(self):
        # 1e100 is well past 1e15 — must stay in scientific.
        self.assertEqual(format_wins(1e100), "1.00e+100")


class TestFormatWinsChatTriggersIntegration(unittest.TestCase):
    """big_win_msg and double_down_win_msg must use format_wins.

    Pins T229: any future regression that drops format_wins from these
    templates will fail these tests.
    """

    def test_big_win_msg_uses_format_wins(self):
        from chat_triggers import big_win_msg
        self.assertEqual(
            big_win_msg("dylan", 140463137867975, "steady"),
            "💰 dylan won 140.46T wins in steady mode!",
        )
        self.assertEqual(
            big_win_msg("worm67", 2618217, "steady"),
            "💰 worm67 won 2.62M wins in steady mode!",
        )
        self.assertEqual(
            big_win_msg("chudwigvanbetahoven", 450560, "steady"),
            "💰 chudwigvanbetahoven won 450.6K wins in steady mode!",
        )

    def test_double_down_msg_uses_format_wins(self):
        from chat_triggers import double_down_win_msg
        self.assertEqual(
            double_down_win_msg("dylan", 45, 3405169339238),
            "🔥 dylan won a 45x double-down for 3.41T wins!",
        )
        self.assertEqual(
            double_down_win_msg("chudwigvanbetahoven", 30, 76907),
            "🔥 chudwigvanbetahoven won a 30x double-down for 76.9K wins!",
        )

    def test_double_down_stake_not_reformatted(self):
        # The "30x" stake must not be passed through format_wins.
        # Regression guard: the regex in migration 069 relies on the
        # stake being "Nx" (not "N.xK" or "NK").
        from chat_triggers import double_down_win_msg
        msg = double_down_win_msg("dylan", 45, 100)
        self.assertIn("45x", msg)
        self.assertIn("for 100 wins", msg)


if __name__ == "__main__":
    unittest.main()
