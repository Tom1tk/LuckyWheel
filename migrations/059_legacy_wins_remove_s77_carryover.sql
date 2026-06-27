-- 059: T218 retroactive — remove the S7.7→S8 carryover from
-- game_state.legacy_wins. The S7.7 wins were added to legacy_wins by
-- the S7.7→S8 rollover (seasons.py:155, prior to T218's edit). The
-- S7.7 carryover shows up in the S8 prestige panel's "Legacy" badge
-- alongside the operator's S8-specific amount (e.g. tom7's
-- 297,840,637,039 figure = 297,836,900,436 S7.7 + 3,736,603 S8).
-- The operator's intent (2026-06-27 review): the badge is an S8 panel
-- and should show the S8-specific amount only.
--
-- This migration subtracts the S7.7 wins (the `final_wins` recorded
-- in user_season_history at the S7.7→S8 rollover, stored under
-- season_number=8) from each player's current legacy_wins. After
-- this runs:
--
--   legacy_wins' = GREATEST(legacy_wins - S7.7_wins, 0)
--
--   tom7: 297,840,637,039 - 297,836,900,436 = 3,736,603  (S8-specific)
--
-- The `GREATEST(..., 0)` clamp protects against any future state
-- where legacy_wins < S7.7_wins (e.g. a manual edit, a future
-- migration that reduces legacy_wins again). The COALESCE(..., 0)
-- handles new S8 players with no S7.7 row in user_season_history —
-- for them there is no carryover to remove, and the WHERE clause
-- skips the row entirely (legacy_wins > 0 is FALSE so the row is
-- not touched; legacy_wins stays at 0).
--
-- Idempotency: the WHERE clause restricts the UPDATE to rows where
-- legacy_wins is still strictly greater than the S7.7 carryover. On
-- a re-run, every row that already had the carryover removed will
-- fail the predicate (3,736,603 > 297,836,900,436 is FALSE) and the
-- UPDATE is a no-op for them. New S8 players also fail the
-- predicate (0 > 0 is FALSE) and are untouched.
--
-- Files NOT touched by this migration:
--   - user_season_history: the S7.7 final_wins snapshot is the
--     historical record of the rollover and must be preserved.
--   - cumulative_wins: the all-time lifetime value is unchanged;
--     only legacy_wins is reduced.
UPDATE game_state gs
SET legacy_wins = GREATEST(
    legacy_wins - COALESCE(
        (SELECT ush.final_wins
         FROM user_season_history ush
         WHERE ush.user_id = gs.user_id
           AND ush.season_number = 8),
        0
    ),
    0
)
WHERE legacy_wins > COALESCE(
    (SELECT ush.final_wins
     FROM user_season_history ush
     WHERE ush.user_id = gs.user_id
       AND ush.season_number = 8),
    0
);
