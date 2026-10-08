-- 078: Season 9 "Charts" rework (docs/SEASON_9_DEEP_SPEC.md).
--   talent_alloc         {talent_id: rank} — the player's Chart for this tide.
--   talent_rechart_date  London date of the last re-chart (one refund per day).
--   surge_spins          banked Surge spins from catches; each spin spends one.
--   fish_records         {species_id: best kg} — personal records, persist across tides.
--   fishing_species / fishing_hooked_at — the fish on the line during a fight;
--                        the server picks it at hook time so the client can't.
-- Idempotent.
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS talent_alloc        JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS talent_rechart_date DATE,
    ADD COLUMN IF NOT EXISTS surge_spins         INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS fish_records        JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS fishing_species     TEXT,
    ADD COLUMN IF NOT EXISTS fishing_hooked_at   TIMESTAMPTZ;
