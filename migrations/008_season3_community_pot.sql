-- Season 3: Community Pot
-- Single-row table tracking aggregate fish click contributions from all players.
CREATE TABLE IF NOT EXISTS community_pot (
    id                INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    total_contributed BIGINT NOT NULL DEFAULT 0,
    target            BIGINT NOT NULL DEFAULT 10000,
    filled            BOOLEAN NOT NULL DEFAULT FALSE,
    filled_at         TIMESTAMPTZ DEFAULT NULL
);
INSERT INTO community_pot (id, target) VALUES (1, 10000) ON CONFLICT DO NOTHING;
