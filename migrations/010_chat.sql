CREATE TABLE chat_messages (
    id         BIGSERIAL PRIMARY KEY,
    user_id    INTEGER   NOT NULL REFERENCES users(id),
    username   TEXT      NOT NULL,
    message    TEXT      NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_chat_messages_id_desc ON chat_messages (id DESC);

CREATE TABLE chat_spam_tracking (
    user_id           INTEGER PRIMARY KEY REFERENCES users(id),
    recent_timestamps TIMESTAMPTZ[] NOT NULL DEFAULT '{}',
    blocked_until     TIMESTAMPTZ,
    block_count       INTEGER NOT NULL DEFAULT 0,
    last_block_at     TIMESTAMPTZ
);
