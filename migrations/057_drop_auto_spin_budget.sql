-- Migration 057: T216 drop auto_spin_budget column.
--
-- T216 strips the per-activation 100-spin budget from the auto-spin
-- subsystem. Auto-spin now runs continuously (until the user stops it
-- or the heartbeat auto-stop kicks in after 60s of no /api/tick).
-- The `auto_spin_since` column stays — it's still the source of truth
-- for "is auto-spin currently active".
--
-- Idempotent: DROP COLUMN IF EXISTS is safe to re-run.
--
-- Rollback note: restoring the column would require re-adding it with
-- a default and a re-derive from /api/tick history. Not provided here
-- because the operator has explicitly stated: "there is no budget for
-- auto spin, there shouldnt be" (2026-06-27).

ALTER TABLE game_state DROP COLUMN IF EXISTS auto_spin_budget;
