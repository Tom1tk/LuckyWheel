-- 047: hardening columns for T69 (wager, gravity, big-win) + T84 (milestone tracking)
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS wager_last_win_amount         INTEGER   NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS wager_banked_losses           INTEGER   NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS wager_insurance_last_recharge TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS gravity_drift                 INTEGER   NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS biggest_win_announced         INTEGER   NOT NULL DEFAULT 0;

ALTER TABLE community_goals
    ADD COLUMN IF NOT EXISTS milestone_25 BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS milestone_50 BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS milestone_75 BOOLEAN NOT NULL DEFAULT FALSE;
