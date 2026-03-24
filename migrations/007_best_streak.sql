ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS best_streak INTEGER NOT NULL DEFAULT 0;

UPDATE game_state SET best_streak = streak WHERE streak > 0;
