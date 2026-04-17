-- Track last auto-fish tick server-side so the 5-second cooldown is
-- enforced at the row level rather than relying solely on Flask-Limiter's
-- per-worker in-memory counter.
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS auto_fish_last_tick TIMESTAMPTZ;
