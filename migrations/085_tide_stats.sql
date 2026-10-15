-- 085: per-player, per-tide counters (how stakes, dice and Surge are used).
-- Idempotent. Bumped in the same transaction as the action that causes them.
CREATE TABLE IF NOT EXISTS tide_stats (
    user_id              INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tide_date            DATE    NOT NULL,   -- London date of the Friday the tide turned
    manual_spins         BIGINT  NOT NULL DEFAULT 0,
    auto_spins           BIGINT  NOT NULL DEFAULT 0,
    staked_spins         BIGINT  NOT NULL DEFAULT 0,
    stake_pct_sum        BIGINT  NOT NULL DEFAULT 0,
    staked_wins_gained   NUMERIC NOT NULL DEFAULT 0,
    staked_wins_lost     NUMERIC NOT NULL DEFAULT 0,
    stake_wins_sum       BIGINT  NOT NULL DEFAULT 0,
    double_downs         INTEGER NOT NULL DEFAULT 0,
    insurance_used       INTEGER NOT NULL DEFAULT 0,
    dice_rolls           INTEGER NOT NULL DEFAULT 0,
    surge_from_catch     BIGINT  NOT NULL DEFAULT 0,
    surge_from_auto_fish BIGINT  NOT NULL DEFAULT 0,
    surge_from_catch_up  BIGINT  NOT NULL DEFAULT 0,
    surge_from_bounty    BIGINT  NOT NULL DEFAULT 0,
    surge_spent          BIGINT  NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, tide_date)
);
