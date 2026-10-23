-- 087: Tide 9.4 stakes come out of today's haul (wins earned since London midnight).
-- Idempotent.
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS haul BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS haul_date DATE;
