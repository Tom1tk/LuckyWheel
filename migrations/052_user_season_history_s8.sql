-- 052: T109 prep — Season 8 per-player state columns on user_season_history.
--
-- The rollover's `INSERT INTO user_season_history` inside
-- seasons.py::advance_season() (see SEASON_8_MIGRATION_PLAN.md §6.2)
-- snapshots each user's final per-season state alongside the existing S7
-- columns (final_wins, upgrade levels, owned_items, equipped_class, …).
-- Until this migration the history table only held the S7-era columns
-- added by 000_baseline + 026_history_upgrade_snapshot, so S8 player
-- state (wager streaks, insurance, prestige, guard, resilience, casino
-- wheel mode, etc.) was silently lost on every rollover.
--
-- Column rationale (S8 mechanic each column captures):
--   wager_streak / wager_last_stake / wager_banked_wins /
--   wager_banked_losses / wager_last_win_amount — wager system state
--   (T48 red redesign + T119 insurance rename).
--   insurance_charges / insurance_armed / insurance_tokens /
--   insurance_free_claimed_date / insurance_unlock_grant_given —
--   insurance economy (T119 rename from wager_tokens).
--   double_down_pending — double-down escrow flag.
--   active_wheel_mode — Casino wheel mode (steady/safe/risky/etc.).
--   auto_spin_budget — auto-spin purchased budget.
--   guard_charges / guard_last_regen_spin — guard upgrade.
--   resilience_last_use_spin — resilience upgrade cooldown.
--   legacy_wins — accumulated wins across seasons (T-account).
--   prestige_level / prestige_count — prestige ladder.
--   cumulative_wins — lifetime wins tally gated by T106.
--   gravity_drift — wheel-mode bias carry-over.
--   biggest_win_announced — per-season jackpot-announced-once flag (T90).
--   cosmetic_fragments — T118 currency.
--   bounty_claimed_date / catch_of_the_day_date — daily date stamps
--   (T117 bounty / T118 catch-of-the-day).
--   onboarding_step — preserved across seasons (T88), snapshotted here
--   for completeness.
--
-- Deliberately EXCLUDED:
--   aquarium_species — game.py:212 documents this column as dead schema
--   ("never written anywhere"; the aquarium mirrors caught_species
--   instead). Not real player state, so not snapshotted.
--
-- Pre-existing S7 columns on user_season_history (final_wins,
-- final_losses, the upgrade levels, owned_items, equipped_class, …)
-- are NOT touched by this migration. Defaults match the corresponding
-- game_state columns so a NULL write is indistinguishable from a fresh
-- season-0 row.
--
-- Safe + idempotent: pure `ADD COLUMN IF NOT EXISTS` with safe
-- defaults. Reversible by manual DROP COLUMN (no down-migration
-- generated intentionally — the inverse ALTER is a one-liner the
-- operator can run by hand if ever needed).
ALTER TABLE user_season_history
    ADD COLUMN IF NOT EXISTS wager_streak                 INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS wager_last_stake             INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS wager_banked_wins            INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS wager_banked_losses          INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS insurance_charges            INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS insurance_armed              BOOLEAN      NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS wager_last_win_amount        INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS insurance_tokens             INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS double_down_pending          BOOLEAN      NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS active_wheel_mode            VARCHAR(16)  NOT NULL DEFAULT 'steady',
    ADD COLUMN IF NOT EXISTS auto_spin_budget             INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS guard_charges                INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS guard_last_regen_spin        BIGINT       NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS resilience_last_use_spin    BIGINT       NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS legacy_wins                  NUMERIC      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS prestige_level              INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS prestige_count               INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS cumulative_wins              BIGINT       NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS gravity_drift               INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS biggest_win_announced        INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS cosmetic_fragments          INTEGER      NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS bounty_claimed_date         DATE,
    ADD COLUMN IF NOT EXISTS catch_of_the_day_date       DATE,
    ADD COLUMN IF NOT EXISTS insurance_free_claimed_date DATE,
    ADD COLUMN IF NOT EXISTS insurance_unlock_grant_given BOOLEAN      NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS onboarding_step              INTEGER      NOT NULL DEFAULT 0;