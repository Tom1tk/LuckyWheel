-- Partial index for the catch-up bonus query in /api/tick:
--   SELECT MIN(wins), COUNT(*) FROM game_state
--   WHERE wins > 0 AND last_spin_at > NOW() - INTERVAL '24 hours'
-- Without this, every tick triggers a seq-scan on game_state.
CREATE INDEX IF NOT EXISTS idx_game_state_last_spin
    ON game_state(last_spin_at)
    WHERE wins > 0;
