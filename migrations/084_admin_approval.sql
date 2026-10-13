-- 084: admin panel, account approval, admin settings, daily fishing stats.
-- Idempotent.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS approved BOOLEAN NOT NULL DEFAULT TRUE;
UPDATE users SET is_admin = TRUE WHERE username = 'tom7';

ALTER TABLE user_devices
    ADD COLUMN IF NOT EXISTS fp        JSONB,
    ADD COLUMN IF NOT EXISTS fp_hash   TEXT,
    ADD COLUMN IF NOT EXISTS ua        TEXT,
    ADD COLUMN IF NOT EXISTS ip        TEXT,
    ADD COLUMN IF NOT EXISTS country   TEXT,
    ADD COLUMN IF NOT EXISTS last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW();
CREATE INDEX IF NOT EXISTS user_devices_fp_hash ON user_devices (fp_hash);

CREATE TABLE IF NOT EXISTS app_settings (
    key   TEXT PRIMARY KEY,
    value JSONB NOT NULL
);
INSERT INTO app_settings (key, value) VALUES ('require_approval', 'true') ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS fishing_days (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day          DATE    NOT NULL,
    casts        INTEGER NOT NULL DEFAULT 0,
    last_cast_at TIMESTAMPTZ,
    gap_n        INTEGER NOT NULL DEFAULT 0,
    gap_mean     DOUBLE PRECISION NOT NULL DEFAULT 0,
    gap_m2       DOUBLE PRECISION NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, day)
);
