-- Season 8: protection rework
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS guard_charges           INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS guard_last_regen_spin   BIGINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS resilience_last_use_spin BIGINT NOT NULL DEFAULT 0;
