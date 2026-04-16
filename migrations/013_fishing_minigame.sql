-- 013_fishing_minigame.sql
-- Cast & Reel fishing minigame: session tracking, encyclopedia, and lucky-next flag.
ALTER TABLE game_state
  ADD COLUMN IF NOT EXISTS fishing_cast_at    TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS fishing_bite_at    TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS fishing_lucky_next BOOLEAN   NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS caught_species     TEXT[]    NOT NULL DEFAULT ARRAY[]::TEXT[];
