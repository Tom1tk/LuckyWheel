-- 044: Track which UTC day a player last claimed bounty rewards, so
-- /api/bounties/claim can't be called repeatedly for infinite rewards.
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS bounty_claimed_date DATE;
