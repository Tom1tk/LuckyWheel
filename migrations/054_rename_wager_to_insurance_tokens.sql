-- 054: T119 — rename wager_tokens to insurance_tokens.
-- Operator chose rename over add+copy for simplicity (the existing
-- wager_tokens column is renamed in place; preserves data). Same for
-- the insurance charges/arm columns. The recharge timestamp column is
-- dropped (no more 1/10min recharge — T119 source #2 is removed).
-- Two new columns gate the new earning sources:
--   * insurance_free_claimed_date    — once-per-UTC-day free-claim
--   * insurance_unlock_grant_given   — exactly-once +5 grant when the
--     player first buys fish_to_wager.
-- All RENAME/DROP statements are wrapped in an IF EXISTS check (Postgres
-- has no IF EXISTS for RENAME, so we use the standard
-- information_schema lookup pattern). Re-applying the migration is a
-- no-op once the columns are in their final state.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='game_state' AND column_name='wager_tokens') THEN
        ALTER TABLE game_state RENAME COLUMN wager_tokens TO insurance_tokens;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='game_state' AND column_name='wager_insurance_charges') THEN
        ALTER TABLE game_state RENAME COLUMN wager_insurance_charges TO insurance_charges;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='game_state' AND column_name='wager_insurance_armed') THEN
        ALTER TABLE game_state RENAME COLUMN wager_insurance_armed TO insurance_armed;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='game_state' AND column_name='wager_insurance_last_recharge') THEN
        ALTER TABLE game_state DROP COLUMN wager_insurance_last_recharge;
    END IF;
END $$;

-- New columns (IF NOT EXISTS makes these idempotent on their own).
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS insurance_free_claimed_date   DATE,
    ADD COLUMN IF NOT EXISTS insurance_unlock_grant_given  BOOLEAN NOT NULL DEFAULT FALSE;
