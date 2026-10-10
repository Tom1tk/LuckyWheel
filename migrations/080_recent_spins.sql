-- 080: the player's last spins, newest first, for the leaderboard's Recent Spins tab.
--   recent_spins  [{result, wins_delta}, ...], capped at RECENT_SPINS_KEPT (game.py).
-- Idempotent.
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS recent_spins JSONB NOT NULL DEFAULT '[]'::jsonb;
