-- Season 9: make auto-spin universal by granting the `auto_spin_unlock`
-- upgrade to every existing player. The ownership gate in /api/auto-spin/
-- start and the client checkbox stay, but the upgrade is now included for
-- all accounts (new players get it at registration in auth.py, future
-- season resets re-grant it in seasons.py, and this migration backfills
-- every current row). Mirrors the migration 073 / 051 grant pattern.
--
-- Idempotent: array_append only fires when the item is not already owned.
UPDATE game_state
SET owned_items = CASE
    WHEN 'auto_spin_unlock' = ANY(owned_items) THEN owned_items
    ELSE array_append(owned_items, 'auto_spin_unlock')
END;
