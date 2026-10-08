-- 077: widen user_season_history's win-amount columns to NUMERIC, matching
-- game_state since 068. One prod player holds ~1e38 cumulative wins, so
-- advance_season's history copy overflowed bigint and aborted every rollover
-- (found rehearsing RV-10 on a prod clone). Idempotent: re-typing to NUMERIC is a no-op.
ALTER TABLE user_season_history
    ALTER COLUMN cumulative_wins       TYPE NUMERIC,
    ALTER COLUMN biggest_win_announced TYPE NUMERIC,
    ALTER COLUMN wager_banked_wins     TYPE NUMERIC,
    ALTER COLUMN wager_banked_losses   TYPE NUMERIC,
    ALTER COLUMN wager_last_win_amount TYPE NUMERIC;
