-- 073: Season 9 "Tides" — weekly sub-seasons and a permanent season label log.
--
-- seasons.sub_number: NULL for a whole season, 1, 2, ... for a tide within the
-- player-facing season (9.1, 9.2, ...). season_log: one row per ended season,
-- so every internal season_number has a player-facing label. Idempotent.
ALTER TABLE seasons ADD COLUMN IF NOT EXISTS sub_number INTEGER;

CREATE TABLE IF NOT EXISTS season_log (
    season_number INTEGER PRIMARY KEY,
    label         TEXT NOT NULL,
    name          TEXT,
    started_at    TIMESTAMPTZ,
    ended_at      TIMESTAMPTZ
);
