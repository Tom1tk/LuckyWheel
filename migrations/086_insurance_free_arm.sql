-- 086: Safety Line's first insurance each London day is free.
-- Idempotent.
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS insurance_free_arm_date DATE;
