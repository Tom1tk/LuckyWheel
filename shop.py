"""Season 8 shop subsystem (T244 + ARCH-04).

Extracted from ``game.py`` so that the route handlers in ``game.py``
stay thin. Mirrors the convention of ``fish.py`` / ``wagers.py`` /
``prestige.py``: this module holds the *logic* and *DB helpers* of
the shop; the *route handler* stays in ``game.py`` on the
``game_bp`` blueprint and calls into here.

Scope of this module:
  * ``COSMETIC_SLOTS`` — re-imported from ``loadout`` for the buy
    flow's cosmetic auto-activation. The map itself moved to
    ``loadout.py`` in T245 (ARCH-06 — loadout owns the cosmetic
    equip concern); ``shop.py`` keeps the import so the buy flow
    can still use the same mapping.
  * ``deduct_cost`` — the shared balance-check / cost-deduct
    helper called out by ARCH-04 in the audit. The same pattern
    was duplicated in the original ``buy()`` body and the dice
    recharge flow. A single helper replaces both; the dice flow
    will be folded in by a follow-up ticket (T245 / T243 dice
    follow-up). For T244 we only need the helper used by the
    buy flow itself.
  * ``buy_core`` — the body of the ``/api/buy`` route. Takes an
    open ``cur`` / ``conn`` and a loaded ``gs`` row from the
    caller; returns either a 200 response dict or a
    ``(status_code, body)`` tuple. No transaction management,
    no Flask request, no JSON rendering — the route handler
    owns those.

Out of scope:
  * Any item balance change (move-only, no behaviour change).
  * The dice recharge-dice call site in ``game.py`` — that uses
    the same pattern but lives on a different transaction; the
    helper is now available and a follow-up ticket can fold it
    in.
  * ``/api/equip-cosmetic`` — that route handler is in
    ``game.py``; the underlying logic lives in
    ``loadout.equip_cosmetic_core`` (T245). It imports
    ``COSMETIC_SLOTS`` from ``loadout`` directly.
"""

import logging

from loadout import COSMETIC_SLOTS
from models import (
    ALL_ITEMS,
    FISH_CATALOG,
    INFINITE_UPGRADES,
    ITEM_CURRENCY,
    RETIRED_ITEMS,
    UPGRADE_TIER_THRESHOLDS,
    inf_upgrade_cost,
    item_tier,
)

log = logging.getLogger("wheel")


# ── ARCH-04: shared balance / cost-deduct helper ─────────────────────────


def deduct_cost(
    gs: dict, cost: int, currency: str
) -> tuple[bool, int, int, int, str | None]:
    """Balance-check and cost-deduct for the buy flow.

    ``ARCH-04`` — this helper replaces the three-way if/elif/else
    block that was duplicated in the infinite-upgrade and ALL_ITEMS
    branches of the original ``buy()`` body. The dice recharge flow
    in ``game.py`` uses the same pattern and can call this helper
    once the dice flow moves to ``dice.py``.

    Args:
        gs: a game_state row (dict from a RealDictCursor). Only the
            ``wins``, ``losses``, and ``fish_clicks`` columns are
            read.
        cost: integer cost of the purchase.
        currency: one of ``"wins"``, ``"losses"``, or
            ``"fish_clicks"``. (The infinite-upgrade flow hardcodes
            ``"wins"`` per the Season 8 spec — the legacy
            ``"fish_clicks"`` branch is preserved here as a
            defence-in-depth measure.)

    Returns:
        ``(ok, new_wins, new_losses, new_fish_clicks, error_msg)``:

          * ``ok`` is True if the deduction succeeded, False if the
            balance was insufficient.
          * On success the three new balance values reflect the
            deduction (unchanged for the columns the currency
            didn't touch).
          * On failure the three balance values are 0 and
            ``error_msg`` is the human-readable reason
            (``"Insufficient wins"``, ``"Insufficient losses"``,
            or ``"Insufficient fish bucks"``).
    """
    if currency == "wins":
        if int(gs["wins"]) < cost:
            return False, 0, 0, 0, "Insufficient wins"
        return (
            True,
            int(gs["wins"]) - cost,
            gs["losses"],
            gs["fish_clicks"],
            None,
        )
    if currency == "losses":
        if gs["losses"] < cost:
            return False, 0, 0, 0, "Insufficient losses"
        return (
            True,
            gs["wins"],
            gs["losses"] - cost,
            gs["fish_clicks"],
            None,
        )
    # fish_clicks (singularity-only — kept here for any future
    # infinite-upgrade that re-enables fish_clicks currency).
    if int(gs["fish_clicks"]) < cost:
        return False, 0, 0, 0, "Insufficient fish bucks"
    return (
        True,
        gs["wins"],
        gs["losses"],
        int(gs["fish_clicks"]) - cost,
        None,
    )


# ── Top-level buy entrypoint ─────────────────────────────────────────────


def buy_core(
    cur, conn, item_id: str, user_id: int, gs: dict
) -> dict | tuple[int, dict]:
    """Process a buy request. Returns the response body dict (200)
    on success, or a ``(status_code, body)`` tuple for rejections.

    Args:
        cur: an open ``RealDictCursor`` on the active transaction.
        conn: the connection the cursor belongs to.
        item_id: the id from the request body.
        user_id: the buyer's id (the route passes
            ``current_user.id``).
        gs: the game_state row already loaded for the buyer
            (the route uses ``_load_game_state`` with
            ``for_update=True`` so the row is locked).

    The caller is responsible for transaction boundaries (opening
    ``conn``, committing on success, rolling back on exception).
    The thin route handler in ``game.py`` does that and converts
    the return value to ``jsonify(...)`` + a status code.
    """
    # T121: items retired from the shop (prestige_efficiency,
    # prestige_legacy) return 403. They're no longer in ALL_ITEMS,
    # so the 400 "Unknown item" branch below would also catch them
    # — this guard produces a clearer error and is documented as
    # defence-in-depth for any client that still references the
    # old item IDs.
    if item_id in RETIRED_ITEMS:
        return 403, {"error": "Item retired"}

    # Infinite repeatable upgrades — handled separately (no
    # "already owned" restriction).
    if item_id in INFINITE_UPGRADES:
        return _buy_infinite(cur, conn, item_id, user_id, gs)

    if item_id not in ALL_ITEMS:
        return 400, {"error": "Unknown item"}

    return _buy_item(cur, conn, item_id, user_id, gs)


# ── Infinite-upgrade branch ──────────────────────────────────────────────


def _buy_infinite(cur, conn, item_id: str, user_id: int, gs: dict) -> dict:
    """Advance an infinite-upgrade by one level.

    The Season 8 spec (``models.S5``) freezes every infinite
    upgrade at level 0 except ``clickmult_inf``; the other IDs in
    ``INFINITE_UPGRADES`` from earlier seasons are still listed
    for backwards compatibility but their columns are dead.
    Per-upgrade requirement checks are preserved for any future
    re-enable.
    """
    inf = INFINITE_UPGRADES[item_id]
    col = inf["db_column"]
    # ponytail: only clickmult_inf survives Season 8 (spec S5)
    currency = "wins"

    owned = list(gs["owned_items"])
    cur_level = gs[col]

    # Generic max_level check (not used in S8 — kept for any
    # future re-enable that adds a hard cap).
    max_level = inf.get("max_level")
    if max_level is not None and cur_level >= max_level:
        return 400, {"error": "Maximum level reached"}

    # Per-upgrade requirement checks. These mirror the
    # pre-T244 inline logic exactly — only the items named here
    # survived in INFINITE_UPGRADES after S8.
    if item_id == "streak_armor_inf":
        if "resilience" not in owned:
            return 400, {"error": "Requires Resilience"}
    elif item_id == "jackpot_resonance_inf":
        if "jackpot" not in owned:
            return 400, {"error": "Requires Jackpot upgrade"}
    elif item_id == "echo_amp_inf":
        if "win_echo" not in owned:
            return 400, {"error": "Requires Win Echo upgrade"}
    elif item_id == "proc_streak_inf":
        if not any(x in owned for x in ("jackpot", "win_echo", "fortune_charm")):
            return 400, {"error": "Requires Jackpot, Win Echo, or Fortune Charm"}

    cost = inf_upgrade_cost(item_id, cur_level)
    ok, new_wins, _new_losses, new_fish, err = deduct_cost(gs, cost, currency)
    if not ok:
        return 402, {"error": err}

    new_level = cur_level + 1
    cur.execute(
        f"UPDATE game_state SET wins = %s, fish_clicks = %s, {col} = %s "
        "WHERE user_id = %s",
        (new_wins, new_fish, new_level, user_id),
    )

    def _lvl(field):
        return new_level if col == field else gs[field]

    return {
        "wins": new_wins,
        "losses": gs["losses"],
        "fish_clicks": new_fish,
        "owned_items": owned,
        "regen_recharge_wins": gs["regen_recharge_wins"],
        "active_cosmetics": list(gs["active_cosmetics"]),
        "winmult_inf_level": _lvl("winmult_inf_level"),
        "bonusmult_inf_level": _lvl("bonusmult_inf_level"),
        "streak_armor_level": _lvl("streak_armor_level"),
        "lure_mastery_level": _lvl("lure_mastery_level"),
        "jackpot_resonance_level": _lvl("jackpot_resonance_level"),
        "echo_amp_level": _lvl("echo_amp_level"),
        "proc_streak_level": _lvl("proc_streak_level"),
    }


# ── ALL_ITEMS branch ─────────────────────────────────────────────────────


def _buy_item(cur, conn, item_id: str, user_id: int, gs: dict) -> dict:
    """Buy a normal shop item (every id in ``ALL_ITEMS`` that's not
    in ``INFINITE_UPGRADES``).
    """
    item = ALL_ITEMS[item_id]
    cost = item["cost"]
    requires = item.get("requires")
    currency = ITEM_CURRENCY[item_id]

    owned = list(gs["owned_items"])

    if item_id in owned:
        return 409, {"error": "Already owned"}
    if requires and requires not in owned:
        return 400, {"error": "Prerequisite not met"}

    # Master upgrades require all species caught (complete
    # Encyclopaedia). The hard-coded set matches the pre-T244
    # inline check.
    if item_id in ("lure_5", "autofisher_4", "precise_angler_3"):
        caught = set(gs["caught_species"])
        all_species = set(FISH_CATALOG.keys())
        if caught < all_species:
            missing = len(all_species) - len(caught & all_species)
            return 403, {
                "error": f"Complete your Encyclopaedia first — "
                f"{missing} species still to catch"
            }

    # T106: tier gating — check cumulative_wins threshold
    # (lifetime wins gained).  Tier 1 items are always available.
    tier = item_tier(item_id)
    if tier > 1:
        threshold = UPGRADE_TIER_THRESHOLDS[tier]
        cumulative = int(gs.get("cumulative_wins", 0))
        if cumulative < threshold:
            return 403, {
                "error": f"Unlocks at {threshold:,} total wins gained "
                f"(you have {cumulative:,})"
            }

    ok, new_wins, new_losses, new_clicks, err = deduct_cost(gs, cost, currency)
    if not ok:
        return 402, {"error": err}

    new_owned = owned + [item_id]
    new_regen_recharge = 0 if item_id == "regen_shield" else gs["regen_recharge_wins"]

    # Auto-activate cosmetic items when purchased — clear the
    # same slot first so a newly-bought cosmetic replaces a
    # previously-active one.
    new_active_cosmetics = list(gs["active_cosmetics"])
    if item_id in COSMETIC_SLOTS:
        slot = COSMETIC_SLOTS[item_id]
        new_active_cosmetics = [
            c for c in new_active_cosmetics if COSMETIC_SLOTS.get(c) != slot
        ]
        new_active_cosmetics.append(item_id)

    cur.execute(
        """UPDATE game_state
           SET wins = %s, losses = %s, fish_clicks = %s,
               owned_items = %s, regen_recharge_wins = %s, active_cosmetics = %s
           WHERE user_id = %s""",
        (
            new_wins,
            new_losses,
            new_clicks,
            new_owned,
            new_regen_recharge,
            new_active_cosmetics,
            user_id,
        ),
    )

    # wager_insurance: grant 3 insurance charges on purchase.
    if item_id == "wager_insurance":
        cur.execute(
            "UPDATE game_state SET insurance_charges = insurance_charges + 3 "
            "WHERE user_id = %s",
            (user_id,),
        )

    # T119: the very first purchase of fish_to_wager grants 5
    # insurance_tokens. The insurance_unlock_grant_given column
    # gates the one-time grant — after the first buy the player
    # has 5 tokens to spend; further buys cost the same 5,000 wins
    # but grant no further tokens.
    if item_id == "fish_to_wager" and not bool(
        gs.get("insurance_unlock_grant_given", False)
    ):
        cur.execute(
            """UPDATE game_state
               SET insurance_tokens = insurance_tokens + 5,
                   insurance_unlock_grant_given = TRUE
               WHERE user_id = %s""",
            (user_id,),
        )

    return {
        "wins": new_wins,
        "losses": new_losses,
        "fish_clicks": new_clicks,
        "owned_items": new_owned,
        "regen_recharge_wins": new_regen_recharge,
        "active_cosmetics": new_active_cosmetics,
        "winmult_inf_level": gs["winmult_inf_level"],
        "bonusmult_inf_level": gs["bonusmult_inf_level"],
    }
