-- 046: Track whether wager insurance is armed for the player's next spin.
-- /api/wager/insurance previously only decremented wager_insurance_charges
-- with no flag to actually apply the protection on the next spin -- the
-- charge was consumed for zero gameplay effect.
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS wager_insurance_armed BOOLEAN NOT NULL DEFAULT FALSE;
