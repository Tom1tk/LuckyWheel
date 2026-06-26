-- Season 8: wager system columns
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS wager_streak            INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS wager_last_stake        INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS double_down_pending     BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS wager_banked_wins       INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS wager_insurance_charges INTEGER NOT NULL DEFAULT 0;
