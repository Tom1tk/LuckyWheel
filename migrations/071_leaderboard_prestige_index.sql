-- T237: composite index for the leaderboard ORDER BY prestige_level DESC, wins DESC
CREATE INDEX IF NOT EXISTS idx_game_state_prestige_wins
  ON game_state (prestige_level DESC, wins DESC)
  WHERE wins > 0 OR prestige_level > 0;
