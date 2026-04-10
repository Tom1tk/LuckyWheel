-- Season 5: Require one spin between dice rolls to prevent streak farming
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS dice_rolled_since_spin BOOLEAN NOT NULL DEFAULT FALSE;
