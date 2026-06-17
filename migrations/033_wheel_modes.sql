-- Season 8: wheel modes
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS active_wheel_mode VARCHAR(16) NOT NULL DEFAULT 'steady';
