-- 089: keep last tide's Chart so the player can restore it after the turn.
-- Idempotent.
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS last_talent_alloc JSONB NOT NULL DEFAULT '{}'::jsonb;
