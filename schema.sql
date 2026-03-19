-- Casino Wheel App — PostgreSQL schema
-- Run as: psql -U wheelapp -d wheeldb -f schema.sql

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(32) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    ip_address    INET NOT NULL,
    session_token VARCHAR(64),
    device_id     VARCHAR(64),                  -- set from long-lived browser cookie
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One account per device (cookie-based; partial index ignores NULL device_id)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_device ON users(device_id) WHERE device_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS game_state (
    user_id        INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    wins           INTEGER NOT NULL DEFAULT 0,
    losses         INTEGER NOT NULL DEFAULT 0,
    fish_clicks    BIGINT NOT NULL DEFAULT 0,
    streak         INTEGER NOT NULL DEFAULT 0,
    owned_items          TEXT[] NOT NULL DEFAULT '{}',
    equipped_fish        VARCHAR(32) NOT NULL DEFAULT 'default',
    shield_charges       INTEGER NOT NULL DEFAULT 0,    -- iron_shield remaining charges (0 when not owned)
    regen_recharge_wins  INTEGER NOT NULL DEFAULT 0     -- regen_shield: wins until recharged (0 = ready)
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id           SERIAL PRIMARY KEY,
    identifier   VARCHAR(64) NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success      BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_login_attempts ON login_attempts(identifier, attempted_at);
