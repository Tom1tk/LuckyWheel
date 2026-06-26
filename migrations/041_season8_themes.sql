-- Season 8: auto-grant theme_tidal to all existing users
-- Idempotent: only grants to users who don't already own it.
UPDATE game_state
SET owned_items = owned_items || ARRAY['theme_tidal']
WHERE 'theme_tidal' <> ALL(owned_items);
