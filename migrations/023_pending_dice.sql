-- Buffer for dice rolls: store result without immediately mutating streak.
-- Consumed and cleared by the next /api/tick spin batch.
ALTER TABLE game_state
  ADD COLUMN IF NOT EXISTS pending_dice JSONB DEFAULT NULL;
