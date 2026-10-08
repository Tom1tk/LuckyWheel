-- 076: label the seasons that ended before season_log existed (073).
--
-- Map from season_snapshots end dates vs PATCH_NOTES and git history:
-- internal 1-6 = Seasons 1-6; 7 = Season 7 (24 Apr hiatus "Mid-Season 6.7",
-- then S7 Endless from 30 Apr; its podium is the 9 May "correct S7 winners");
-- 8 = "7.7" (9 May - 26 Jun, incl. the High Stakes update). Internal 9 is
-- Season 8 Casino, labelled by advance_season at launch. Dates come from the
-- snapshots, so a DB without them (fresh/test) gets no rows. Idempotent.
INSERT INTO season_log (season_number, label, name, started_at, ended_at)
SELECT m.season_number, m.label, m.name,
       COALESCE(LAG(e.ended_at) OVER (ORDER BY m.season_number), '2026-03-19 00:00+00'),
       e.ended_at
FROM (VALUES (1, '1', NULL), (2, '2', NULL), (3, '3', NULL), (4, '4', NULL),
             (5, '5', NULL), (6, '6', 'Night Ocean'), (7, '7', 'Endless'),
             (8, '7.7', NULL)) AS m(season_number, label, name)
JOIN (SELECT season_number, MIN(snapshot_at) AS ended_at
      FROM season_snapshots GROUP BY season_number) e USING (season_number)
ON CONFLICT DO NOTHING;
