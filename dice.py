"""Season 8 dice subsystem (T243).

Extracted from ``game.py`` so the ``/api/roll-dice`` route handler
stays thin. Mirrors the convention of ``fish.py`` / ``wagers.py`` /
``prestige.py``: this module holds the *logic* of the dice
minigame; the *route handler* stays in ``game.py`` on the
``game_bp`` blueprint and calls into here.

Scope of this module:
  * ``_recharge_dice`` — refill the dice-charge bucket from
    elapsed wall-clock time (moved from ``game.py:80``).
  * ``roll_dice_core`` — the pure dice-roll core: recharge,
    precondition checks, dice generation, streak math
    (cursed / blessed / triple variants), pending_dice
    construction, charge decrement, recharge clock reset.
  * The ``/api/roll-dice`` thin handler reads game_state, calls
    ``roll_dice_core``, writes the UPDATE, builds the response.

The three other call sites that only needed the recharge
helper (``/api/state``, ``/api/spin``, ``/api/tick``) now
import ``_recharge_dice`` from here.
"""
import datetime as dt
import logging
import random
from datetime import timezone, timedelta

from models import DICE_RECHARGE_SECONDS, dice_max_charges

log = logging.getLogger('wheel')


def _aware(dt_val):
    """Ensure a datetime from psycopg2 has UTC tzinfo (psycopg2 returns
    naive datetimes by default)."""
    if dt_val is not None and dt_val.tzinfo is None:
        return dt_val.replace(tzinfo=timezone.utc)
    return dt_val


def _recharge_dice(charges, last_recharge, max_charges, now_utc):
    """Recharge dice charges based on elapsed time. Returns
    ``(charges, last_recharge)``.

    Mirrors the behavior of the original ``game.py:80`` helper.
    """
    last_recharge = _aware(last_recharge)
    elapsed = int((now_utc - last_recharge).total_seconds() // DICE_RECHARGE_SECONDS)
    if elapsed > 0 and charges < max_charges:
        charges = min(charges + elapsed, max_charges)
        last_recharge = last_recharge + timedelta(seconds=DICE_RECHARGE_SECONDS * elapsed)
    return charges, last_recharge


def roll_dice_core(
    gs: dict,
    owned: list,
    now_utc: dt.datetime,
    *,
    rand_func=None,
) -> dict:
    """Resolve a dice roll. Pure function — no Flask, no DB, no
    module-level state.

    Args:
        gs: a dict-like carrying the game_state fields the dice
            logic needs:
              - ``streak`` (int)
              - ``dice_charges`` (int)
              - ``dice_last_recharge`` (datetime, may be naive)
              - ``dice_rolled_since_spin`` (bool)
              - ``auto_spin_since`` (datetime or None)
        owned: list of owned item ids (used for ``dice_extra``
            and for ``dice_max_charges``).
        now_utc: current UTC time (tz-aware datetime).
        rand_func: optional random-like with ``.randint(a, b)``
            for tests to force outcomes. ``None`` uses the
            module-level ``random`` module.

    Returns:
        On rejection: ``{'ok': False, 'status': 400, 'error': str}``.
        On success: a dict with everything the route handler
        needs to build the response + the UPDATE — see below.
    """
    r = rand_func if rand_func is not None else random

    streak = int(gs['streak'])
    auto_spin_active = gs.get('auto_spin_since') is not None

    # Recharge first so a player who waited long enough can roll.
    max_charges = dice_max_charges(owned)
    dice_charges = min(int(gs['dice_charges']), max_charges)  # cap stale over-limit
    last_recharge = _aware(gs['dice_last_recharge'])
    dice_charges, last_recharge = _recharge_dice(
        dice_charges, last_recharge, max_charges, now_utc
    )

    # Precondition checks (unchanged from the original handler).
    if streak < 3:
        return {
            'ok': False,
            'status': 400,
            'error': 'Need a win streak of 3 or more to roll',
        }
    if dice_charges < 1:
        return {
            'ok': False,
            'status': 400,
            'error': 'No dice charges available',
        }
    if gs.get('dice_rolled_since_spin'):
        return {
            'ok': False,
            'status': 400,
            'error': 'You must spin once before rolling again',
        }

    # Roll the dice.
    num_dice = 3 if 'dice_extra' in owned else 2
    dice = [r.randint(1, 6) for _ in range(num_dice)]
    dice_sum = sum(dice)

    ones = dice.count(1)
    sixes = dice.count(6)
    # Triple outcomes (3-die only) take priority over the pair outcomes.
    cursed_triple = (num_dice == 3 and ones == 3)
    blessed_triple = (num_dice == 3 and sixes == 3)
    cursed = (not cursed_triple) and ones >= 2
    blessed = (not blessed_triple) and sixes >= 2

    # Streak math — independent of the money math in _resolve_spin.
    original_streak = streak
    if cursed_triple:
        new_streak = max(0, streak // 3)
    elif blessed_triple:
        new_streak = streak * 3
    elif cursed:
        new_streak = max(0, streak // 2)
    elif blessed:
        new_streak = streak * 2
    else:
        new_streak = streak + dice_sum

    new_charges = dice_charges - 1
    # Reset the recharge clock from now whenever a charge is consumed.
    new_last_recharge = now_utc if new_charges < max_charges else last_recharge

    pending = {
        'new_streak':      new_streak,
        'original_streak': original_streak,
        'dice_sum':        dice_sum,
        'cursed':          cursed or cursed_triple,
        'blessed':         blessed or blessed_triple,
        'cursed_triple':   cursed_triple,
        'blessed_triple':  blessed_triple,
        'die1':            dice[0],
        'die2':            dice[1],
        'die3':            dice[2] if len(dice) > 2 else None,
    }

    # T220: auto-spinning buffers the dice as pending_dice; otherwise
    # the new streak is applied to the DB right away and the next
    # spin's loss handler reverts + refunds on a loss.
    if auto_spin_active:
        new_streak_to_store = streak
        applied_immediately = False
    else:
        new_streak_to_store = new_streak
        applied_immediately = True

    return {
        'ok': True,
        'dice':               dice,
        'dice_sum':           dice_sum,
        'cursed':             cursed,
        'blessed':            blessed,
        'cursed_triple':      cursed_triple,
        'blessed_triple':     blessed_triple,
        'new_streak':         new_streak,
        'original_streak':    original_streak,
        'pending':            pending,
        'new_charges':        new_charges,
        'new_last_recharge':  new_last_recharge,
        # Post-recharge, pre-decrement value — used in the response
        # body (the DB write uses new_last_recharge instead).
        'recharged_last_recharge': last_recharge,
        'new_streak_to_store': new_streak_to_store,
        'applied_immediately': applied_immediately,
    }
