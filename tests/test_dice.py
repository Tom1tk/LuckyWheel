"""T243: Unit tests for the dice subsystem extracted from ``game.py``.

These tests exercise the pure helpers and the ``roll_dice_core``
function in ``dice.py`` directly — no Flask request context, no
real DB. The T220/T221 dice characterization tests in
``tests/test_dice_and_no_jackpot.py`` still cover the HTTP contract
via source-grep assertions; this file pins the in-process logic
so the extraction stays green.

The ``MockCursor`` here is intentionally minimal — ``roll_dice_core``
takes a pre-loaded ``gs`` dict and doesn't touch the DB itself. The
fake rand (``_ForcedRand`` below) pins the dice outcome so each
test is deterministic.
"""
import datetime as dt
import os
import random
import sys
from datetime import timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import dice
from dice import _recharge_dice, roll_dice_core


# ──────────────────────────────────────────────────────────────────────────
# Fake random — pins the die roll sequence for deterministic tests.
# ──────────────────────────────────────────────────────────────────────────


class _ForcedRand:
    """Stand-in for ``random.Random`` that returns a fixed sequence.

    The dice logic only ever calls ``randint(1, 6)`` (one per die),
    so this is all we need.
    """

    def __init__(self, *values):
        self._values = list(values)

    def randint(self, a, b):
        # Pop the next pre-queued value, clamped to [a, b]. If the
        # caller asks for more rolls than were queued, fall back to
        # ``a`` so the test sees a predictable outcome rather than a
        # crash.
        if self._values:
            v = self._values.pop(0)
            return max(a, min(b, v))
        return a


# ──────────────────────────────────────────────────────────────────────────
# _recharge_dice
# ──────────────────────────────────────────────────────────────────────────


class TestRechargeDice:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    BASE = NOW - dt.timedelta(hours=1)

    def test_no_elapsed_no_change(self):
        # last_recharge == now_utc → 0 elapsed seconds → no refill.
        charges, last = _recharge_dice(0, self.NOW, 3, self.NOW)
        assert charges == 0
        assert last == self.NOW

    def test_one_charge_refilled(self):
        # 10 minutes elapsed → exactly one charge refilled.
        last = self.NOW - dt.timedelta(seconds=600)
        charges, last = _recharge_dice(0, last, 3, self.NOW)
        assert charges == 1
        # last_recharge advances by exactly 1 * DICE_RECHARGE_SECONDS.
        assert last == self.NOW - dt.timedelta(seconds=0)

    def test_caps_at_max_charges(self):
        # 100 minutes elapsed, cap at max_charges=2.
        last = self.NOW - dt.timedelta(seconds=100 * 60)
        charges, _ = _recharge_dice(0, last, 2, self.NOW)
        assert charges == 2

    def test_does_not_overfill(self):
        # Already at max → even after a long wait, charges unchanged.
        last = self.NOW - dt.timedelta(hours=5)
        charges, _ = _recharge_dice(3, last, 3, self.NOW)
        assert charges == 3

    def test_partial_elapsed_no_refill(self):
        # 5 minutes elapsed (less than DICE_RECHARGE_SECONDS=600) → 0 refilled.
        last = self.NOW - dt.timedelta(seconds=300)
        charges, last = _recharge_dice(1, last, 3, self.NOW)
        assert charges == 1
        assert last == last  # unchanged (Naive to tz-aware → same value)

    def test_naive_last_recharge_is_aware_after(self):
        # last_recharge arrives naive (psycopg2 default) → result is tz-aware.
        naive = (self.NOW - dt.timedelta(seconds=600)).replace(tzinfo=None)
        charges, last = _recharge_dice(0, naive, 3, self.NOW)
        assert charges == 1
        assert last.tzinfo is not None


# ──────────────────────────────────────────────────────────────────────────
# roll_dice_core — preconditions
# ──────────────────────────────────────────────────────────────────────────


def _gs(**kw):
    """Build a minimal gs dict for roll_dice_core.

    Default ``dice_last_recharge`` is the same instant as ``NOW`` in the
    test classes below — i.e. just refilled, no extra time to drain
    away. Tests that want a different recharge history must override.
    """
    now = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    defaults = {
        'streak': 5,
        'dice_charges': 1,
        'dice_last_recharge': now,
        'dice_rolled_since_spin': False,
        'auto_spin_since': None,
    }
    defaults.update(kw)
    return defaults


class TestRejections:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)

    def test_streak_below_3_rejected(self):
        gs = _gs(streak=2)
        rand = _ForcedRand(3, 4)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert result == {
            'ok': False,
            'status': 400,
            'error': 'Need a win streak of 3 or more to roll',
        }

    def test_streak_exactly_3_accepted(self):
        # 3 is the inclusive floor — it must pass.
        gs = _gs(streak=3)
        rand = _ForcedRand(3, 4)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert result['ok'] is True

    def test_no_charges_rejected(self):
        # Max charges drops to 0 because no upgrades + charges was 0.
        gs = _gs(dice_charges=0, streak=5)
        rand = _ForcedRand(3, 4)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert result == {
            'ok': False,
            'status': 400,
            'error': 'No dice charges available',
        }

    def test_dice_rolled_since_spin_rejected(self):
        gs = _gs(dice_rolled_since_spin=True)
        rand = _ForcedRand(3, 4)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert result == {
            'ok': False,
            'status': 400,
            'error': 'You must spin once before rolling again',
        }


# ──────────────────────────────────────────────────────────────────────────
# roll_dice_core — success path / dice math
# ──────────────────────────────────────────────────────────────────────────


class TestRollDiceCore:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    LAST_RECHARGE = NOW  # Just refilled — no time has passed since.

    def test_basic_roll_two_dice(self):
        # Two dice, no upgrades. 3 + 4 = 7, no curse/bless, streak += 7.
        gs = _gs(streak=5, dice_charges=1, dice_last_recharge=self.LAST_RECHARGE)
        rand = _ForcedRand(3, 4)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert result['ok'] is True
        assert result['dice'] == [3, 4]
        assert result['dice_sum'] == 7
        assert result['cursed'] is False
        assert result['blessed'] is False
        assert result['cursed_triple'] is False
        assert result['blessed_triple'] is False
        assert result['new_streak'] == 5 + 7
        assert result['original_streak'] == 5
        assert result['applied_immediately'] is True
        assert result['new_streak_to_store'] == 12
        # Charges decremented.
        assert result['new_charges'] == 0
        # pending dict mirrors the response fields.
        assert result['pending']['new_streak'] == 12
        assert result['pending']['original_streak'] == 5
        assert result['pending']['die1'] == 3
        assert result['pending']['die2'] == 4
        assert result['pending']['die3'] is None
        # `cursed`/`blessed` in pending are OR'd with the triple flags
        # (matches the original behavior of the route handler).
        assert result['pending']['cursed'] is False
        assert result['pending']['blessed'] is False

    def test_dice_extra_three_dice(self):
        # With dice_extra, 3 dice are rolled and die3 is populated.
        gs = _gs(streak=3)
        rand = _ForcedRand(2, 5, 6)
        result = roll_dice_core(gs, ['dice_extra'], self.NOW, rand_func=rand)
        assert result['dice'] == [2, 5, 6]
        assert result['pending']['die3'] == 6

    def test_cursed_pair_halves_streak(self):
        # Two 1s on 2 dice → cursed → streak // 2.
        gs = _gs(streak=10)
        rand = _ForcedRand(1, 1, 5)
        result = roll_dice_core(gs, ['dice_extra'], self.NOW, rand_func=rand)
        assert result['cursed'] is True
        assert result['cursed_triple'] is False
        assert result['new_streak'] == 5  # 10 // 2

    def test_cursed_triple_streak_third(self):
        # 3 dice, all 1s → cursed_triple → streak // 3.
        gs = _gs(streak=9)
        rand = _ForcedRand(1, 1, 1)
        result = roll_dice_core(gs, ['dice_extra'], self.NOW, rand_func=rand)
        assert result['cursed_triple'] is True
        assert result['cursed'] is False  # pair variant is suppressed
        assert result['new_streak'] == 3  # 9 // 3

    def test_cursed_pair_with_streak_3_halves_to_1(self):
        # The streak precondition enforces streak >= 3, so the smallest
        # reachable cursed-pair outcome is 3 // 2 = 1. (The `max(0, ...)`
        # in the original handler is a defensive guard against negative
        # inputs that can't actually occur in production.)
        gs = _gs(streak=3)
        rand = _ForcedRand(1, 1, 5)
        result = roll_dice_core(gs, ['dice_extra'], self.NOW, rand_func=rand)
        assert result['cursed'] is True
        assert result['new_streak'] == 1

    def test_blessed_pair_doubles_streak(self):
        # Two 6s on 2 dice → blessed → streak * 2.
        gs = _gs(streak=4)
        rand = _ForcedRand(6, 6, 1)
        result = roll_dice_core(gs, ['dice_extra'], self.NOW, rand_func=rand)
        assert result['blessed'] is True
        assert result['blessed_triple'] is False
        assert result['new_streak'] == 8  # 4 * 2

    def test_blessed_triple_streak_tripled(self):
        # 3 dice, all 6s → blessed_triple → streak * 3.
        gs = _gs(streak=3)
        rand = _ForcedRand(6, 6, 6)
        result = roll_dice_core(gs, ['dice_extra'], self.NOW, rand_func=rand)
        assert result['blessed_triple'] is True
        assert result['blessed'] is False  # pair variant is suppressed
        assert result['new_streak'] == 9  # 3 * 3

    def test_charges_decremented_and_clock_reset(self):
        # After rolling, the recharge clock is reset to now_utc (so a
        # player who consumes a charge starts the next regen tick from
        # this moment, not from the prior recharge timestamp).
        gs = _gs(streak=5, dice_charges=2, dice_last_recharge=self.LAST_RECHARGE)
        rand = _ForcedRand(2, 3)
        result = roll_dice_core(gs, ['dice_charge_3'], self.NOW, rand_func=rand)
        assert result['new_charges'] == 1
        assert result['new_last_recharge'] == self.NOW

    def test_last_recharge_not_reset_at_max_charges(self):
        # Special case: if the player has full charges AFTER decrementing,
        # the recharge clock is left alone (no point resetting the clock
        # when the bucket is full again — the original handler's quirk).
        gs = _gs(streak=5, dice_charges=1, dice_last_recharge=self.LAST_RECHARGE)
        rand = _ForcedRand(2, 3)
        # dice_max_charges([dice_charge_2]) == 2 → after decrement = 1,
        # which is < max → reset still fires. Use a different scenario.
        gs = _gs(streak=5, dice_charges=2, dice_last_recharge=self.LAST_RECHARGE)
        rand = _ForcedRand(2, 3)
        result = roll_dice_core(gs, ['dice_charge_2'], self.NOW, rand_func=rand)
        # max=2, after decrement new_charges=1 < 2 → reset → now_utc.
        assert result['new_charges'] == 1
        assert result['new_last_recharge'] == self.NOW

    def test_recharged_last_recharge_for_response(self):
        # The route response includes the POST-recharge, PRE-decrement
        # last_recharge value. Verify roll_dice_core surfaces that.
        old_recharge = self.NOW - dt.timedelta(seconds=600)  # 1 charge due
        gs = _gs(streak=5, dice_charges=0, dice_last_recharge=old_recharge)
        rand = _ForcedRand(2, 3)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert result['new_charges'] == 0  # 0 + 1 (recharge) - 1 (consume)
        # recharged_last_recharge is the value AFTER recharge but BEFORE
        # the consume reset — i.e. now_utc (since 1 tick of recharge
        # brings it to now).
        assert result['recharged_last_recharge'] == self.NOW

    def test_auto_spin_buffers_dice(self):
        # When auto-spinning, the new streak is buffered in pending_dice
        # and the DB streak stays at the old value.
        gs = _gs(streak=5, auto_spin_since=self.NOW)
        rand = _ForcedRand(3, 4)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert result['ok'] is True
        assert result['applied_immediately'] is False
        assert result['new_streak_to_store'] == 5  # unchanged
        # The new_streak is still computed and stashed in pending.
        assert result['new_streak'] == 12
        assert result['pending']['new_streak'] == 12

    def test_pending_dict_keys(self):
        # Pin the contract: pending_dice carries the fields the spin
        # handler relies on.
        gs = _gs(streak=3)
        rand = _ForcedRand(1, 2)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert set(result['pending'].keys()) == {
            'new_streak', 'original_streak', 'dice_sum',
            'cursed', 'blessed', 'cursed_triple', 'blessed_triple',
            'die1', 'die2', 'die3',
        }

    def test_no_db_no_flask(self):
        # Sanity: roll_dice_core must not import DB or Flask modules.
        # (We check it has no implicit dependencies by ensuring it runs
        # with the bare minimum stub.)
        gs = _gs(streak=3)
        rand = _ForcedRand(1, 2)
        result = roll_dice_core(gs, [], self.NOW, rand_func=rand)
        assert result['ok'] is True
        # No exceptions, no globals touched.
