-- 079: Charts levels (docs/SEASON_9_DEEP_SPEC.md §3.1).
--   chart_points_bought  Chart points bought with wins this tide; resets each tide.
-- Idempotent.
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS chart_points_bought INTEGER NOT NULL DEFAULT 0;
