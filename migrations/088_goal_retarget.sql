-- 088: Tide 9.4 goal targets for auto play. Goal rows store their target at
-- insert, and the 9.4 row is inserted by the old code at the turn, so retarget
-- open rows here. The stake goal changes unit (wins -> stakes), so its progress restarts.
-- Idempotent.
UPDATE community_goals SET target = 60000 WHERE goal_id = 'goal_fish5000' AND NOT completed;
UPDATE community_goals SET target = 4000 WHERE goal_id = 'goal_jackpot500' AND NOT completed;
WITH retargeted AS (
    UPDATE community_goals
       SET target = 40, current = 0, milestone_25 = FALSE, milestone_50 = FALSE, milestone_75 = FALSE
     WHERE goal_id = 'goal_wager100k' AND NOT completed AND target <> 40
    RETURNING goal_id
)
DELETE FROM community_goal_contributions WHERE goal_id IN (SELECT goal_id FROM retargeted);
