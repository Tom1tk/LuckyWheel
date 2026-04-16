-- Migration 014: fastest_catch_pct
-- Stores the player's best (lowest) precise-angler percentage from manual catches.
-- NULL = no eligible catch recorded yet.
ALTER TABLE game_state
  ADD COLUMN IF NOT EXISTS fastest_catch_pct FLOAT DEFAULT NULL;
