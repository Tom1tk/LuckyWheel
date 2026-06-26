-- Season 8: fishing integration
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS wager_tokens      INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS aquarium_species  TEXT[]  NOT NULL DEFAULT '{}';
