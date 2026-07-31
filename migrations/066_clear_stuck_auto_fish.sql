-- 066: T224 — Backfill stuck auto-fish state for players without the upgrade
--
-- Bug (operator, 2026-06-27): a player had auto-fish ON, then prestiged.
-- Prestige drops the autofisher_* upgrade from owned_items (T121: all
-- functional upgrades are cleared) but the auto_fish_enabled flag was
-- left intact, leaving the player "stuck on" auto-fish with no toggle
-- (the JSX only renders the toggle when autofisher_1 is owned). The
-- player also couldn't manually fish because the JSX hides the cast
-- button when autoFish=true.
--
-- T224 fixes the root cause by adding auto_fish_enabled and
-- auto_fish_last_tick to PRESTIGE_RESET_COLUMNS so future prestiges
-- clear them. This migration backfills any existing stuck players:
-- for every user who does NOT own any autofisher_* upgrade, force
-- auto_fish_enabled = FALSE and clear auto_fish_last_tick.
--
-- owned_items is text[] (Postgres ARRAY, not jsonb), so we use the
-- = ANY(...) operator rather than the jsonb `?` containment operator.
--
-- Idempotent: re-running finds no autofisher-less users with
-- auto_fish_enabled=true (already fixed by the first pass) and
-- updates nothing.

UPDATE game_state
   SET auto_fish_enabled   = FALSE,
       auto_fish_last_tick = NULL
 WHERE auto_fish_enabled = TRUE
   AND NOT ('autofisher_1' = ANY (owned_items)
            OR 'autofisher_2' = ANY (owned_items)
            OR 'autofisher_3' = ANY (owned_items)
            OR 'autofisher_4' = ANY (owned_items));
