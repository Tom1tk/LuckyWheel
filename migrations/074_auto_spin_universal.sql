-- Migration 074: RV-03 universal auto-spin (salvaged from S9 mig 076).
--
-- Auto-spin is free from spin 1 in Season 9. The 5,000-win gate is gone,
-- so every existing player is granted `auto_spin_unlock`. The grant is
-- idempotent: rows that already own the item are left untouched.
--
-- New registrations get the item in auth.py; the season reset re-grant
-- lives in seasons.py (handled by its own ticket).

UPDATE game_state SET owned_items = CASE WHEN 'auto_spin_unlock' = ANY(owned_items) THEN owned_items ELSE array_append(owned_items, 'auto_spin_unlock') END;
