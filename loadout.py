"""Season 8 loadout subsystem (T245 + ARCH-06).

Extracted from ``game.py`` so that the route handlers in ``game.py``
stay thin. Mirrors the convention of ``fish.py`` / ``shop.py`` /
``wagers.py``: this module holds the *logic* and *DB helpers* of
the loadout subsystem; the *route handlers* stay in ``game.py`` on
the ``game_bp`` blueprint and call into here.

Scope of this module:
  * ``COSMETIC_SLOTS`` — the cosmetic-slot mapping used by the
    ``/api/equip-cosmetic`` route (and the buy flow's cosmetic
    auto-activation in ``shop.py``). Moved here from ``shop.py``
    (which in turn had moved it from ``game.py`` in T244) so the
    loadout subsystem owns the cosmetic-equip concern. ARCH-06.
  * The bodies of the four loadout route handlers:
        /api/loadout   GET    get_loadout
        /api/loadout   POST   save_loadout_core
        /api/equip           equip_fish_core
        /api/equip-class     equip_class_core
        /api/equip-cosmetic  equip_cosmetic_core

Out of scope:
  * ``/api/loadout/apply`` (``apply_loadout``) — left in ``game.py``
    per the ticket scope. The class-item reverse map
    (``_LOADOUT_CLASS_ITEMS``) used by it stays there too.
  * Any loadout balance change (move-only, no behaviour change).
  * The cosmetic auto-activation in the buy flow — that lives in
    ``shop.buy_core`` and re-imports ``COSMETIC_SLOTS`` from this
    module.
"""

import logging

import psycopg2.extras

from models import VALID_FISH_IDS

log = logging.getLogger("wheel")


# ── Cosmetic slots ────────────────────────────────────────────────────────
# Maps each cosmetic item id to the slot it occupies. Used by
# ``equip_cosmetic_core`` (toggle on/off and slot replacement) and
# re-imported by ``shop.py`` for the buy flow's cosmetic
# auto-activation. ARCH-06 — this dict is owned by the loadout
# subsystem because every mutation of ``active_cosmetics`` goes
# through it.
COSMETIC_SLOTS = {
    "bg_ocean": "bg",
    "bg_royal": "bg",
    "bg_inferno": "bg",
    "bg_forest": "bg",
    "bg_abyss": "bg",
    "bg_cosmic": "bg",
    "fishsize_small": "size",
    "fishsize_1": "size",
    "fishsize_2": "size",
    "fishsize_3": "size",
    "confetti_1": "confetti",
    "confetti_2": "confetti",
    "confetti_3": "confetti",
    "party_mode": "party",
    "trail_1": "trail",
    "trail_2": "trail",
    "trail_3": "trail",
    "trail_4": "trail",
    "trail_5": "trail",
    "trail_6": "trail",
    "theme_fire": "wheel",
    "theme_ice": "wheel",
    "theme_neon": "wheel",
    "theme_void": "wheel",
    "theme_gold": "wheel",
    "theme_tidal": "wheel",
    "theme_ember": "wheel",
    "theme_frost": "wheel",
    "theme_aurora": "wheel",
    "theme_vintage": "wheel",
    "golden_wheel": "golden",
    "page_season1": "page_theme",
    "page_season2": "page_theme",
    "page_season3": "page_theme",
    "page_season4": "page_theme",
    "page_season5": "page_theme",
    "page_season6": "page_theme",
    "page_season7": "page_theme",
    "page_season8": "page_theme",
    "auto_guard": "auto_guard",
}


# Class item → value stored in game_state.equipped_class. The
# equip-class route accepts any of these values plus ``None`` (to
# unequip).
_CLASS_MAP = {
    "class_earth": "earth",
    "class_moon": "moon",
    "class_star": "star",
    None: None,
}


# ── GET /api/loadout ──────────────────────────────────────────────────────


def get_loadout(cur, user_id: int) -> dict:
    """Return the player's saved build loadouts.

    Response body for the GET ``/api/loadout`` route:
        ``{"loadouts": {<slot>: <config>, ...}}``

    Returns an empty ``loadouts`` dict when the player has no
    saved loadouts (an empty query is the normal case for new
    players, not an error).
    """
    cur.execute(
        "SELECT slot, config FROM build_loadouts WHERE user_id = %s ORDER BY slot",
        (user_id,),
    )
    rows = cur.fetchall()
    return {"loadouts": {row["slot"]: row["config"] for row in rows}}


# ── POST /api/loadout ─────────────────────────────────────────────────────


def save_loadout_core(
    cur, conn, user_id: int, slot: int, raw_loadout: dict
) -> dict | tuple[int, dict]:
    """Save a build loadout to a slot (1-3).

    Returns the response body on success, or a ``(status, body)``
    tuple on a rejection. The thin route handler renders that
    to ``jsonify(...)`` + status code.

    A loadout is ``equipped_class`` + ``active_wheel_mode`` only
    (spec S11). Client-supplied ``owned_items`` / ``active_cosmetics``
    are NEVER persisted — that path used to write those straight to
    ``game_state`` with no validation, letting any player grant
    themselves every item in the shop for free.
    """
    if not (1 <= slot <= 3):
        return 400, {"error": "Slot must be 1-3"}
    loadout_data = {
        "equipped_class": raw_loadout.get("equipped_class"),
        "active_wheel_mode": raw_loadout.get("active_wheel_mode", "steady"),
    }
    cur.execute(
        """INSERT INTO build_loadouts (user_id, slot, config)
           VALUES (%s, %s, %s)
           ON CONFLICT (user_id, slot) DO UPDATE SET config = EXCLUDED.config""",
        (user_id, slot, psycopg2.extras.Json(loadout_data)),
    )
    return {"ok": True, "slot": slot}


# ── POST /api/equip (fish) ────────────────────────────────────────────────


def equip_fish_core(cur, conn, user_id: int, fish_id: str) -> dict | tuple[int, dict]:
    """Set the player's equipped fish.

    Returns the response body on success, or a ``(status, body)``
    tuple on a rejection. ``fish_id == 'default'`` is always
    allowed (the off-skin) — every other id must be in the
    player's ``owned_items``.
    """
    if fish_id not in VALID_FISH_IDS:
        return 400, {"error": "Invalid fish"}

    cur.execute(
        "SELECT owned_items FROM game_state WHERE user_id = %s FOR UPDATE",
        (user_id,),
    )
    gs = cur.fetchone()
    owned = list(gs["owned_items"])
    if fish_id != "default" and fish_id not in owned:
        return 403, {"error": "Fish not owned"}

    cur.execute(
        "UPDATE game_state SET equipped_fish = %s WHERE user_id = %s",
        (fish_id, user_id),
    )
    return {"equipped_fish": fish_id}


# ── POST /api/equip-class ─────────────────────────────────────────────────


def equip_class_core(
    cur, conn, user_id: int, class_id: object
) -> dict | tuple[int, dict]:
    """Set the player's equipped class.

    ``class_id`` is the request-body key from the React client
    (``'class_earth'`` / ``'class_moon'`` / ``'class_star'`` /
    ``None`` to unequip). It is mapped to the value stored in
    ``game_state.equipped_class`` (``'earth'`` / ``'moon'`` /
    ``'star'`` / ``NULL``).
    """
    if class_id not in _CLASS_MAP:
        return 400, {"error": "Invalid class"}
    equipped_value = _CLASS_MAP[class_id]

    cur.execute(
        "SELECT owned_items FROM game_state WHERE user_id = %s",
        (user_id,),
    )
    gs = cur.fetchone()
    if class_id and class_id not in list(gs["owned_items"]):
        return 400, {"error": "Class not owned"}

    cur.execute(
        "UPDATE game_state SET equipped_class = %s WHERE user_id = %s",
        (equipped_value, user_id),
    )
    return {"ok": True, "equipped_class": equipped_value}


# ── POST /api/equip-cosmetic ──────────────────────────────────────────────


def equip_cosmetic_core(
    cur, conn, user_id: int, item_id: str
) -> dict | tuple[int, dict]:
    """Set / toggle the player's active cosmetic.

    Re-uses the existing toggle UX: equipping an already-active
    cosmetic in the same slot UN-equips it; equipping a new
    cosmetic in a slot replaces whatever was already in that
    slot (and leaves other slots untouched).
    """
    if item_id not in COSMETIC_SLOTS:
        return 400, {"error": "Invalid cosmetic item"}

    cur.execute(
        "SELECT owned_items, active_cosmetics FROM game_state "
        "WHERE user_id = %s FOR UPDATE",
        (user_id,),
    )
    gs = cur.fetchone()
    owned = list(gs["owned_items"])
    active_cosmetics = list(gs["active_cosmetics"])

    if item_id not in owned:
        return 400, {"error": "Not owned"}

    if item_id in active_cosmetics:
        # Unequip (toggle off).
        active_cosmetics = [c for c in active_cosmetics if c != item_id]
    else:
        # Remove all items in the same slot, then equip.
        slot = COSMETIC_SLOTS[item_id]
        active_cosmetics = [
            c for c in active_cosmetics if COSMETIC_SLOTS.get(c) != slot
        ]
        active_cosmetics.append(item_id)

    cur.execute(
        "UPDATE game_state SET active_cosmetics = %s WHERE user_id = %s",
        (active_cosmetics, user_id),
    )
    return {"active_cosmetics": active_cosmetics}
