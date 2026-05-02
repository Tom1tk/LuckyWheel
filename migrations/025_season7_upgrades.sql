-- 025_season7_upgrades.sql
-- Season 7: decision-space upgrades (classes, new infinites, fish exchange).
ALTER TABLE game_state
  ADD COLUMN IF NOT EXISTS lure_mastery_level      INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS jackpot_resonance_level INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS echo_amp_level          INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS proc_streak_level       INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS proc_streak             INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS fish_exchange_total     BIGINT  NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS equipped_class          VARCHAR(10) DEFAULT NULL;
