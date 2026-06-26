-- 049: T106 — change tier gating from `win_count` (count of winning spins) to
-- `cumulative_wins` (lifetime value of wins gained). The previous metric was
-- designed for an auto-spin era where every player spun 100+ times per session.
-- With wager-driven manual play, the count is too slow.
--
-- cumulative_wins is the lifetime tally of wins gained. It is INCREMENTED on
-- every winning spin by wins_delta, and never decremented (not by purchases,
-- not by wager losses, not by prestige). It tracks the value earned, not
-- the value held.
--
-- Backfill: set to current `wins` balance (best available approximation —
-- going forward, increments by wins_delta on every win).
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS cumulative_wins BIGINT DEFAULT 0;
UPDATE game_state SET cumulative_wins = wins WHERE cumulative_wins = 0;
