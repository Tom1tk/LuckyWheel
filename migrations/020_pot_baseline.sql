-- 020_pot_baseline.sql
-- Raise community pot starting target from 1000 → 40000.
-- Designed so 3 players at autofisher_2 + lure_3 (≈6000 fish/hr each)
-- take roughly 2 hours combined to fill the first cycle.
UPDATE community_pot SET
    target              = 40000,
    total_contributed   = 0,
    filled              = false,
    filled_at           = NULL,
    last_decay_check    = NOW()
WHERE id = 1;
