-- Season 8: prestige, legacy wins, onboarding, auto-spin budget
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS prestige_level    INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS prestige_count    INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS legacy_wins       NUMERIC NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS onboarding_step   INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS auto_spin_budget  INTEGER NOT NULL DEFAULT 0;
