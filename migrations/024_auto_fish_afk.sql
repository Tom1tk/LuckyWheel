-- Track whether the user had auto-fish enabled when they closed the tab,
-- so the server can process catch-up fish ticks on their return.
ALTER TABLE game_state
  ADD COLUMN IF NOT EXISTS auto_fish_enabled BOOLEAN NOT NULL DEFAULT FALSE;
