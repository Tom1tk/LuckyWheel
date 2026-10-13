-- 083: activity tracking and review flags.
-- Idempotent.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS active_since   TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_action_at TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS cheat_flags (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind       TEXT        NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    last_seen  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    detail     TEXT,
    UNIQUE (user_id, kind, started_at)
);
