-- Track timestamp of last spin per user (used for spin-rate limiting/display)
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS last_spin_at TIMESTAMPTZ;
