-- 048: wager system redesign (T102)
-- wager_last_stake column repurposed: old 1-10 multiplier → new 0/5/10/.../45 percentage.
-- Migration: (old_stake - 1) * 5
--   old 1× → 0%, 2× → 5%, 3× → 10%, ..., 7× → 30%, 8× → 35%, 9× → 40%, 10× → 45%
-- (No data loss; cap is 45% which is the new max)
UPDATE game_state
SET wager_last_stake = LEAST(45, GREATEST(0, (COALESCE(wager_last_stake, 1) - 1) * 5))
WHERE wager_last_stake IS NOT NULL;
