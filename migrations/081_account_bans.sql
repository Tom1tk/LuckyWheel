-- 081: account suspensions.
-- Idempotent.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS banned_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ban_reason   TEXT;
