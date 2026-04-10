-- Season 5: Dice charge system, jackpot echo, streak armor, community pot rework

-- Dice charge system
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS dice_charges INTEGER NOT NULL DEFAULT 1;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS dice_last_recharge TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Jackpot echo flag (persists across a single spin boundary)
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS jackpot_echo_next BOOLEAN NOT NULL DEFAULT FALSE;

-- Streak Armor infinite upgrade level
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS streak_armor_level INTEGER NOT NULL DEFAULT 0;

-- Community pot: fractional win_chance_pct (e.g. 50.5%)
ALTER TABLE community_pot ALTER COLUMN win_chance_pct TYPE NUMERIC(5,1);

-- Community pot: track last decay check timestamp
ALTER TABLE community_pot ADD COLUMN IF NOT EXISTS last_decay_check TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Reset pot to Season 5 starting values
UPDATE community_pot SET
    fib_prev = 0,
    target = 1000,
    win_chance_pct = 50.0,
    filled = false,
    filled_at = NULL,
    total_contributed = 0,
    last_decay_check = NOW()
WHERE id = 1;

