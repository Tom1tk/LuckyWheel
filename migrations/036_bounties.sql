-- Season 8: daily bounties
CREATE TABLE IF NOT EXISTS bounty_progress (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bounty_date  DATE    NOT NULL,
    bounty_id    VARCHAR(32) NOT NULL,
    progress     INTEGER NOT NULL DEFAULT 0,
    completed    BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, bounty_date, bounty_id)
);

ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS cosmetic_fragments INTEGER NOT NULL DEFAULT 0;
