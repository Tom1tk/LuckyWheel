-- Enforce one spin at a time per user across all tabs/sessions.
-- last_spin_at is checked server-side; spins within 1.5s are rejected.
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS last_spin_at TIMESTAMPTZ;
