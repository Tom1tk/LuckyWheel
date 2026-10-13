-- 082: browsers each account has used.
-- Idempotent.
CREATE TABLE IF NOT EXISTS user_devices (
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id  TEXT        NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, device_id)
);
CREATE INDEX IF NOT EXISTS user_devices_device_id ON user_devices (device_id);
INSERT INTO user_devices (user_id, device_id)
    SELECT id, device_id FROM users WHERE device_id IS NOT NULL
    ON CONFLICT DO NOTHING;
