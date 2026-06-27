-- 055: T212 — add a `player_facing_number` column to the `seasons` table.
--
-- The `seasons` table has two existing columns that conflate two
-- different things:
--   * `season_number` — auto-incrementing DB row id, used as the
--     primary key for snapshots / history. The operator never sees
--     this number directly.
--   * `name` — a human-readable label like "Casino", "7.7",
--     "6 — Bioluminescence". This is what the chat / patch notes use.
--
-- What was missing is the **player-facing** season number: the digit
-- shown to operators and players. For the current row the player-facing
-- season is S8, but the DB row id is 9 (the auto-increment counter
-- never resets, so the S8 row was inserted at row 9). The top-right
-- widget currently displays `season.season_name` ("Casino"), which the
-- operator flagged as wrong on 2026-06-27 ("The top right says season
-- casino, this needs to say season 8").
--
-- The fix: add a separate `player_facing_number` column that is set
-- per-row at creation time. The S8 row is backfilled to 8 here; future
-- rollovers (S8 → S8.1 or S8 → S9) set their own value in
-- `seasons.py:advance_season`. Older rows are left NULL — the JSX
-- falls back to `season.season_number` when the new column is absent.
--
-- Idempotency: `ADD COLUMN IF NOT EXISTS` makes the column creation
-- safe to re-run. The `UPDATE` is guarded by `name = 'Casino'` so it
-- only touches the S8 row; on a re-run after the row has been
-- advanced to a different name, the UPDATE matches nothing and is a
-- no-op.

ALTER TABLE seasons
    ADD COLUMN IF NOT EXISTS player_facing_number INTEGER;

UPDATE seasons
   SET player_facing_number = 8
 WHERE name = 'Casino'
   AND player_facing_number IS NULL;
