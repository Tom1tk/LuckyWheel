"""Season 8 fishing subsystem (T240).

Extracted from ``game.py`` so that the route handlers in
``game.py`` stay thin. Mirrors the convention of ``wagers.py`` /
``prestige.py``: this module holds the *logic* and *DB helpers*
of the fishing minigame; the *route handlers* stay in
``game.py`` on the ``game_bp`` blueprint and call into here.

Scope of this module:
  * Constants for the reel window and EWMA telemetry.
  * Per-worker cache for the total fish_clicks aggregate.
  * Pure helpers that compute catch values / upgrade levels.
  * The bodies of the five fishing route handlers:
        /api/cast            cast_line
        /api/bite-poll       bite_poll
        /api/reel            reel_line
        /api/auto-fish-tick  auto_fish_tick
        /api/auto-fish-enabled  set_auto_fish_enabled
  * Bounty / community-goal / onboarding bookkeeping that
    follows a successful catch (it lives in the same transaction
    as the catch itself, so it belongs in the same module).

Out of scope:
  * The fishing-side AFK catch-up that runs inside ``_resolve_spin``
    (``game.py:1940-...``) — that one lives in the spin path and
    imports the upgrade-level helpers from here. The math is
    identical; the call site stays in ``game.py`` because spinning
    and fishing-catch-up share the same transaction there.
  * ``/api/fish-exchange`` (different subsystem — shop-style coin
    conversion; the audit doc notes dice/shop/loadout as separate
    follow-ups).
  * Fish skins / shop UI (not part of the fishing game logic).
"""

import datetime as dt
import logging
import random
import time
from datetime import timezone, timedelta

from models import (
    FISH_CATALOG,
    roll_fish,
    fish_value,
    lure_bite_delay_seconds,
    autofisher_catch_rate,
    lure_mastery_mult,
    CLASS_EARTH_FISH_BONUS,
    HAPPY_HOUR_START_UTC,
    HAPPY_HOUR_END_UTC,
)

# Post-catch bookkeeping — top-level so tests can monkeypatch
# individual helpers (bounties / community_goals / seasons / wheel_modes).
from bounties import increment_bounty
from community_goals import (
    get_active_goal,
    increment_goal,
    check_goal_completion,
)
from seasons import get_season_info
from wheel_modes import get_week_number

log = logging.getLogger("wheel")


# ── Reel-window constants ─────────────────────────────────────────────────
# Server-side reel window: client sees 1.5 s, server grants 0.3 s of
# network headroom so a tap at the last moment still registers.
REEL_WINDOW_SECONDS = 1.8
# Minimum elapsed seconds after bite_at before a reel is accepted.
# Sub-50ms reels are impossible for real players (poll cadence +
# network RTT floor).
REEL_MIN_DELTA_SECONDS = 0.05
# EWMA smoothing factor for precise_pct telemetry
# (lower = slower response).
_EWMA_ALPHA = 0.15


# ── SUM(fish_clicks) cache ─────────────────────────────────────────────────
# Full-table aggregate; cache per worker for 15 s to avoid scanning on
# every /api/state load and every 5-second /api/community-pot poll.
_fish_clicks_cache: dict = {"ts": 0.0, "total": 0}
_FISH_CLICKS_TTL = 15.0


def _aware(dt_val):
    """Ensure a datetime from psycopg2 has UTC tzinfo (psycopg2 returns
    naive datetimes by default)."""
    if dt_val is not None and dt_val.tzinfo is None:
        return dt_val.replace(tzinfo=timezone.utc)
    return dt_val


# ── Upgrade-level helpers ─────────────────────────────────────────────────


def lure_level(owned) -> int:
    """Return the lure upgrade level (0-5) based on owned items.

    The ``lure_5`` item is the highest tier; tiers 4, 3, 2, 1 are
    checked in descending order so the highest one wins.
    """
    for lvl, item in [
        (5, "lure_5"),
        (4, "lure_4"),
        (3, "lure_3"),
        (2, "lure_2"),
        (1, "lure_1"),
    ]:
        if item in owned:
            return lvl
    return 0


def autofisher_level(owned) -> int:
    """Return the autofisher upgrade level (0-4) based on owned items.

    ``autofisher_4`` is the Master tier (catches rare species).
    """
    for lvl, item in [
        (4, "autofisher_4"),
        (3, "autofisher_3"),
        (2, "autofisher_2"),
        (1, "autofisher_1"),
    ]:
        if item in owned:
            return lvl
    return 0


# ── Aggregates ────────────────────────────────────────────────────────────


def get_total_fish_clicks(cur) -> int:
    """Return SUM(fish_clicks) across all players, cached per worker
    for ``_FISH_CLICKS_TTL`` seconds. The cache is process-local (one
    entry per worker) and is intentionally simple — a short TTL keeps
    the number close to fresh while removing the load from a hot
    full-table scan.
    """
    now = time.monotonic()
    if now - _fish_clicks_cache["ts"] < _FISH_CLICKS_TTL:
        return _fish_clicks_cache["total"]
    cur.execute("SELECT COALESCE(SUM(fish_clicks), 0) AS total FROM game_state")
    total = int(cur.fetchone()["total"])
    _fish_clicks_cache["ts"] = now
    _fish_clicks_cache["total"] = total
    return total


def reset_total_fish_clicks_cache():
    """Test hook: drop the in-memory cache so the next read re-queries.

    Not used in production — the cache TTL is short enough that
    production code never needs to invalidate it.
    """
    _fish_clicks_cache["ts"] = 0.0
    _fish_clicks_cache["total"] = 0


# ── Cast ──────────────────────────────────────────────────────────────────


def cast_line(
    cur, user_id: int, now_utc: dt.datetime, *, rand=None
) -> dict | tuple[int, dict]:
    """Start a new fishing session for ``user_id``.

    Returns the response body on success (200), or a ``(status, body)``
    tuple on a rejection (the route handler renders that to JSON +
    status code).

    The ``rand`` argument is a test seam — pass a seeded random.Random
    instance for deterministic tests. ``None`` uses the module-level
    ``random`` module.
    """
    r = rand if rand is not None else random
    cur.execute(
        "SELECT owned_items, fishing_cast_at, fishing_bite_at "
        "FROM game_state WHERE user_id = %s FOR UPDATE",
        (user_id,),
    )
    gs = cur.fetchone()

    owned = list(gs["owned_items"])
    cast_at = gs["fishing_cast_at"]
    bite_at = gs["fishing_bite_at"]
    if cast_at and bite_at:
        bite_at = _aware(bite_at)
        if bite_at + timedelta(seconds=REEL_WINDOW_SECONDS) > now_utc:
            return 400, {"error": "Already fishing"}

    lure_lvl = lure_level(owned)
    min_delay, max_delay = lure_bite_delay_seconds(lure_lvl)
    delay = r.uniform(min_delay, max_delay)
    new_bite_at = now_utc + timedelta(seconds=delay)

    # 50% chance of a fake nibble partway through the wait (adds tension)
    nibble_at = None
    if r.random() < 0.5:
        nibble_frac = r.uniform(0.25, 0.70)
        nibble_at = (now_utc + timedelta(seconds=delay * nibble_frac)).isoformat()

    cur.execute(
        "UPDATE game_state SET fishing_cast_at = %s, fishing_bite_at = %s "
        "WHERE user_id = %s",
        (now_utc, new_bite_at, user_id),
    )
    # bite_at is intentionally omitted from this response — the client
    # must poll /api/bite-poll to detect the bite rather than pre-timing it.
    return {
        "cast_at": now_utc.isoformat(),
        "nibble_at": nibble_at,
    }


# ── Bite poll ─────────────────────────────────────────────────────────────


def bite_poll(cur, user_id: int, now_utc: dt.datetime) -> dict:
    """Report whether the player currently has a biting fish.

    The response shape mirrors the original /api/bite-poll handler:
        {'bite': False}                       if no cast is active
        {'expired': True}                     if the window has passed
        {'bite': False}                       if still waiting
        {'bite': True, 'remaining_ms': int}   if biting now
    """
    cur.execute(
        "SELECT fishing_bite_at FROM game_state WHERE user_id = %s",
        (user_id,),
    )
    gs = cur.fetchone()

    bite_at = gs["fishing_bite_at"]
    if bite_at is None:
        return {"bite": False}

    bite_at = _aware(bite_at)
    expires_at = bite_at + timedelta(seconds=REEL_WINDOW_SECONDS)

    if now_utc > expires_at:
        return {"expired": True}

    if now_utc < bite_at:
        return {"bite": False}

    remaining_ms = int((expires_at - now_utc).total_seconds() * 1000)
    return {"bite": True, "remaining_ms": max(0, remaining_ms)}


# ── Reel ──────────────────────────────────────────────────────────────────


def reel_line(cur, conn, user_id: int, now_utc: dt.datetime) -> dict | tuple[int, dict]:
    """Resolve the player's reel attempt.

    Returns the response body on success/miss, or a ``(status, body)``
    tuple on a rejection. The thin route handler just renders the
    return value to JSON + status code.
    """
    cur.execute(
        """SELECT owned_items, fishing_cast_at, fishing_bite_at,
                  fishing_lucky_next, caught_species, fish_clicks,
                  fastest_catch_pct,
                  suspicious_catches, catch_count, catch_pct_ewma,
                  catch_of_the_day_date, onboarding_step
           FROM game_state WHERE user_id = %s FOR UPDATE""",
        (user_id,),
    )
    gs = cur.fetchone()

    cast_at = gs["fishing_cast_at"]
    bite_at = gs["fishing_bite_at"]
    fish_clicks = int(gs["fish_clicks"])

    if not cast_at or not bite_at:
        return {
            "result": "miss",
            "reason": "no_session",
            "fish_clicks": fish_clicks,
        }

    bite_at = _aware(bite_at)
    expires_at = bite_at + timedelta(seconds=REEL_WINDOW_SECONDS)

    # Always clear the session regardless of timing
    cur.execute(
        "UPDATE game_state SET fishing_cast_at = NULL, fishing_bite_at = NULL "
        "WHERE user_id = %s",
        (user_id,),
    )

    if now_utc < bite_at or now_utc > expires_at:
        return {
            "result": "miss",
            "reason": "bad_timing",
            "fish_clicks": fish_clicks,
        }

    elapsed_s = (now_utc - bite_at).total_seconds()
    if elapsed_s < REEL_MIN_DELTA_SECONDS:
        log.warning(
            "SUSPICIOUS_REEL_TOO_FAST user_id=%s delta_ms=%.1f",
            user_id,
            elapsed_s * 1000,
        )
        return {
            "result": "miss",
            "reason": "too_fast",
            "fish_clicks": fish_clicks,
        }

    # Successful catch!
    owned = list(gs["owned_items"])
    lure_lvl = lure_level(owned)
    happy_hour = _is_happy_hour(now_utc)
    species_id = roll_fish(
        auto_mode=False, master_lure=(lure_lvl >= 5), happy_hour=happy_hour
    )
    species = FISH_CATALOG[species_id]
    value = fish_value(species_id, lure_lvl)
    lucky_next = bool(gs["fishing_lucky_next"])
    caught_species = list(gs["caught_species"])
    was_doubled = False

    if lucky_next:
        value *= 2
        was_doubled = True

    # Precise Angler: tiered multiplier for early reels (exclusive —
    # highest gate wins).  elapsed_s already computed above (reused
    # from the too_fast check).
    precise_pct = round((elapsed_s / REEL_WINDOW_SECONDS) * 100, 1)
    precise_mult = 1.0
    if "precise_angler_3" in owned and precise_pct <= 15.0:
        precise_mult = 2.0
    elif "precise_angler_2" in owned and precise_pct <= 20.0:
        precise_mult = 1.5
    elif "precise_angler_1" in owned and precise_pct <= 50.0:
        precise_mult = 1.2
    precise_bonus = precise_mult > 1.0
    if precise_bonus:
        value = int(value * precise_mult)

    new_lucky_next = species_id == "lucky"
    first_catch = species_id not in caught_species
    if first_catch:
        caught_species = caught_species + [species_id]

    new_fish_clicks = fish_clicks + value

    # Track personal best (lowest = fastest) precise catch percentage
    old_best = gs["fastest_catch_pct"]
    new_best = precise_pct if (old_best is None or precise_pct < old_best) else old_best

    # Telemetry: EWMA of precise_pct and suspicious-catch counter.
    old_ewma = gs["catch_pct_ewma"]
    new_ewma = (
        precise_pct
        if old_ewma is None
        else (_EWMA_ALPHA * precise_pct + (1 - _EWMA_ALPHA) * old_ewma)
    )
    new_catch_count = int(gs["catch_count"]) + 1
    new_suspicious = int(gs["suspicious_catches"])
    if precise_pct < 12.0:
        new_suspicious += 1
        if new_suspicious % 10 == 0:
            log.warning(
                "SUSPICIOUS_REEL user_id=%s pct=%.1f ewma=%.1f "
                "catch_count=%d suspicious=%d",
                user_id,
                precise_pct,
                new_ewma,
                new_catch_count,
                new_suspicious,
            )

    # T119: fish catches no longer award insurance_tokens. The
    # tier-based FISH_TO_WAGER_RATES path is gone — tokens are earned
    # from the three new sources: 3 free/day claim, 1/2/3 per bounty
    # (T117), and +5 on the first purchase of fish_to_wager.
    # catch_of_the_day still tracks its date column (the upgrade
    # itself is unchanged) but it no longer multiplies any token
    # award since no tokens are awarded here in the first place.
    catch_of_day_bonus = False
    if "catch_of_the_day" in owned:
        today = now_utc.date().isoformat()
        last_cotd = gs.get("catch_of_the_day_date") or ""
        if last_cotd != today:
            catch_of_day_bonus = True

    if catch_of_day_bonus:
        cur.execute(
            """UPDATE game_state
               SET fish_clicks = %s, fishing_lucky_next = %s,
                   caught_species = %s, fastest_catch_pct = %s,
                   suspicious_catches = %s, catch_count = %s,
                   catch_pct_ewma = %s, catch_of_the_day_date = %s
               WHERE user_id = %s""",
            (
                new_fish_clicks,
                new_lucky_next,
                caught_species,
                new_best,
                new_suspicious,
                new_catch_count,
                new_ewma,
                now_utc.date(),
                user_id,
            ),
        )
    else:
        cur.execute(
            """UPDATE game_state
               SET fish_clicks = %s, fishing_lucky_next = %s,
                   caught_species = %s, fastest_catch_pct = %s,
                   suspicious_catches = %s, catch_count = %s,
                   catch_pct_ewma = %s
               WHERE user_id = %s""",
            (
                new_fish_clicks,
                new_lucky_next,
                caught_species,
                new_best,
                new_suspicious,
                new_catch_count,
                new_ewma,
                user_id,
            ),
        )

    # Bounty / community-goal / onboarding bookkeeping.  These are
    # all called on the open conn — they share this reel's
    # transaction, so any failure rolls the whole catch back.
    _post_catch_bookkeeping(conn, user_id, now_utc, first_catch)

    onboarding_advance = gs.get("onboarding_step", 0) == 2

    return {
        "result": "hit",
        "species": species_id,
        "species_emoji": species["emoji"],
        "species_name": species["name"],
        "value": value,
        "first_catch": first_catch,
        "was_doubled": was_doubled,
        "precise_bonus": precise_bonus,
        "precise_mult": precise_mult,
        "precise_pct": precise_pct,
        "lucky_next_active": new_lucky_next,
        "fish_clicks": new_fish_clicks,
        "catch_of_day_bonus": catch_of_day_bonus,
        "onboarding_advance": onboarding_advance,
    }


# ── Auto-fish tick ────────────────────────────────────────────────────────


def auto_fish_tick(
    cur, conn, user_id: int, now_utc: dt.datetime, *, rand=None
) -> dict | tuple[int, dict]:
    """Resolve one auto-fish tick for ``user_id``.

    Returns the response body on success/miss, or a ``(status, body)``
    tuple on a rejection (e.g. 403 if the player doesn't own an
    autofisher).
    """
    r = rand if rand is not None else random
    cur.execute(
        """SELECT owned_items, fish_clicks, caught_species,
                  auto_fish_last_tick, lure_mastery_level, equipped_class
           FROM game_state WHERE user_id = %s FOR UPDATE""",
        (user_id,),
    )
    gs = cur.fetchone()

    owned = list(gs["owned_items"])
    autofisher_lvl = autofisher_level(owned)

    if autofisher_lvl < 1:
        return 403, {"error": "Auto-Fisher not owned"}

    last_tick = gs["auto_fish_last_tick"]
    if last_tick is not None:
        last_tick = _aware(last_tick)
        if (now_utc - last_tick).total_seconds() < 5.0:
            return {
                "result": "miss",
                "fish_clicks": int(gs["fish_clicks"]),
            }

    if r.random() >= autofisher_catch_rate(autofisher_lvl):
        cur.execute(
            "UPDATE game_state SET auto_fish_last_tick = %s, "
            "auto_fish_enabled = TRUE WHERE user_id = %s",
            (now_utc, user_id),
        )
        return {
            "result": "miss",
            "fish_clicks": int(gs["fish_clicks"]),
        }

    lure_lvl = lure_level(owned)
    species_id = roll_fish(auto_mode=True, allow_rare=(autofisher_lvl >= 4))
    species = FISH_CATALOG[species_id]
    base_value = fish_value(species_id, lure_lvl)
    lm_mult = lure_mastery_mult(gs["lure_mastery_level"])
    earth_mult = (
        1.0 + CLASS_EARTH_FISH_BONUS if gs["equipped_class"] == "earth" else 1.0
    )
    value = max(1, int(base_value * lm_mult * earth_mult))
    caught_species = list(gs["caught_species"])
    first_catch = species_id not in caught_species
    if first_catch:
        caught_species = caught_species + [species_id]

    new_fish_clicks = int(gs["fish_clicks"]) + value

    cur.execute(
        "UPDATE game_state SET fish_clicks = %s, caught_species = %s, "
        "auto_fish_last_tick = %s, auto_fish_enabled = TRUE "
        "WHERE user_id = %s",
        (new_fish_clicks, caught_species, now_utc, user_id),
    )

    return {
        "result": "hit",
        "species": species_id,
        "species_emoji": species["emoji"],
        "species_name": species["name"],
        "value": value,
        "first_catch": first_catch,
        "fish_clicks": new_fish_clicks,
    }


# ── Auto-fish toggle ──────────────────────────────────────────────────────


def set_auto_fish_enabled(
    cur, conn, user_id: int, requested: bool, now_utc: dt.datetime
) -> dict:
    """Set the player's auto_fish_enabled flag.

    T224: defensive — if the player doesn't own an autofisher upgrade,
    the flag is forced off regardless of what the client requested.
    This un-sticks players who lost the upgrade on prestige (or any
    other case where the upgrade is missing while the flag is true).

    Returns the response body (always 200).
    """
    cur.execute(
        "SELECT owned_items, auto_fish_enabled FROM game_state "
        "WHERE user_id = %s FOR UPDATE",
        (user_id,),
    )
    gs = cur.fetchone()
    autofisher_lvl = autofisher_level(list(gs["owned_items"]))
    enabled = bool(requested and autofisher_lvl >= 1)

    cur.execute(
        """UPDATE game_state
           SET auto_fish_enabled = %s,
               auto_fish_last_tick = CASE WHEN %s THEN auto_fish_last_tick
                                          ELSE NULL END
           WHERE user_id = %s""",
        (enabled, enabled, user_id),
    )
    return {"ok": True, "auto_fish_enabled": enabled}


# ── Internal helpers ──────────────────────────────────────────────────────


def _is_happy_hour(now_utc: dt.datetime) -> bool:
    """Return True if the current UTC hour is inside the configured
    happy-hour window (20:00–20:59 UTC = 9–10pm BST).
    """
    return HAPPY_HOUR_START_UTC <= now_utc.hour < HAPPY_HOUR_END_UTC


def _post_catch_bookkeeping(
    conn, user_id: int, now_utc: dt.datetime, first_catch: bool
) -> None:
    """Side effects that must follow every successful catch:

      * ``bounty_fish10`` — bounty for daily catch count
      * community-goal increment (if a ``fish_caught`` goal is active
        this week, +1 per catch; if it's a ``unique_species`` goal,
        +1 only on the first catch of a new species)
      * Onboarding: advance step 2→3 on the first successful catch
        and grant ``fish_tropical`` (the starter skin)

    These are run on the same open transaction as the catch so any
    failure rolls everything back.
    """
    bounty_date = now_utc.date()
    increment_bounty(conn, user_id, "bounty_fish10", bounty_date)

    season_info = get_season_info(conn)
    season_num = season_info.get("season_number", 8) if season_info else 8
    week_num = get_week_number(now_utc)
    _, goal_def = get_active_goal(conn, season_num, week_num)
    if goal_def:
        if goal_def["metric"] == "fish_caught":
            increment_goal(conn, goal_def["goal_id"], user_id, 1)
            check_goal_completion(conn, goal_def["goal_id"])
        elif goal_def["metric"] == "unique_species" and first_catch:
            increment_goal(conn, goal_def["goal_id"], user_id, 1)
            check_goal_completion(conn, goal_def["goal_id"])

    # Onboarding: advance step 2→3 on first successful catch
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE game_state
               SET onboarding_step = 3,
                   owned_items = CASE WHEN NOT (owned_items @> ARRAY['fish_tropical'])
                       THEN array_append(owned_items, 'fish_tropical')
                       ELSE owned_items END
               WHERE user_id = %s AND onboarding_step = 2""",
            (user_id,),
        )
