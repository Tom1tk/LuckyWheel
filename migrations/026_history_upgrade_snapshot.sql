-- Save all upgrade levels in user_season_history so any future season rollover
-- is fully reversible. Without this, upgrade levels were unrecoverable after a reset.
ALTER TABLE user_season_history
    ADD COLUMN IF NOT EXISTS winmult_inf_level       INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS bonusmult_inf_level     INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS clickmult_inf_level     INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS streak_armor_level      INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS lure_mastery_level      INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS jackpot_resonance_level INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS echo_amp_level          INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS proc_streak_level       INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS final_fish_clicks       BIGINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS owned_items             TEXT[]  NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS active_cosmetics        TEXT[]  NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS equipped_fish           VARCHAR(32) NOT NULL DEFAULT 'default',
    ADD COLUMN IF NOT EXISTS equipped_class          VARCHAR(10);
