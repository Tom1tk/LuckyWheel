-- Season 8: build loadouts
CREATE TABLE IF NOT EXISTS build_loadouts (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot       INTEGER NOT NULL CHECK (slot >= 1 AND slot <= 3),
    name       VARCHAR(32) NOT NULL DEFAULT 'Loadout 1',
    config     JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, slot)
);
