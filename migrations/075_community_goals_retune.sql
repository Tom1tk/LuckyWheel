-- Season 9: retune community goal targets to the live ~5-player server.
-- Season 8 postmortem: goals never filled (jackpot 98/500, wager 15k/100k,
-- fish 0/5,000) — the per-player caps worked, the targets were 5-10x too
-- big for the real player count. Update the existing rows in place; new
-- rows inherit the retuned COMMUNITY_GOAL_DEFS in community_goals.py.
UPDATE community_goals SET target = 1500   WHERE goal_id = 'goal_fish5000';
UPDATE community_goals SET target = 100    WHERE goal_id = 'goal_jackpot500';
UPDATE community_goals SET target = 20     WHERE goal_id = 'goal_prestige50';
UPDATE community_goals SET target = 25000  WHERE goal_id = 'goal_wager100k';
-- goal_species100 keeps its 100 target (closest to filling in S8: 30/100).
