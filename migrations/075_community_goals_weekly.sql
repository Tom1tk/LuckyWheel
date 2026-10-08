-- RV-04: weekly community goals (Season 9 tides).
-- Retunes open goal rows to the ~5-player weekly scale and retires goal_prestige50.
-- Idempotent: re-running changes nothing.

-- Open rows take the new targets. Completed rows keep their old target as history.
UPDATE community_goals SET target = 1500  WHERE goal_id = 'goal_fish5000'  AND NOT completed AND target <> 1500;
UPDATE community_goals SET target = 100   WHERE goal_id = 'goal_jackpot500' AND NOT completed AND target <> 100;
UPDATE community_goals SET target = 25000 WHERE goal_id = 'goal_wager100k'  AND NOT completed AND target <> 25000;

-- goal_prestige50 is retired. Drop its open row so it cannot stay active.
-- Completed prestige rows stay as history.
DELETE FROM community_goals WHERE goal_id = 'goal_prestige50' AND NOT completed;
