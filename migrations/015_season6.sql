-- 015_season6.sql
-- Season 6: Night Ocean — reset community pot to S6 starting values.
-- The game_state reset (fishing columns, dice, streak_armor, etc.) is handled
-- automatically by _perform_rollover in seasons.py when ends_at expires.
-- This migration resets only the shared community_pot singleton, which the
-- rollover does not touch, matching the pattern set by 011_season5.sql.

UPDATE community_pot SET
    fib_prev            = 0,
    target              = 1000,
    win_chance_pct      = 50.0,
    filled              = false,
    filled_at           = NULL,
    total_contributed   = 0,
    last_decay_check    = NOW()
WHERE id = 1;
