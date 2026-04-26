-- Season 7: server-side auto-spinning
-- auto_spin_since: when this user's wheel started spinning this season (NULL = not yet started)
-- season_registered: pre-registration flag for next season start

ALTER TABLE game_state
  ADD COLUMN IF NOT EXISTS auto_spin_since TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS season_registered BOOLEAN NOT NULL DEFAULT FALSE;
