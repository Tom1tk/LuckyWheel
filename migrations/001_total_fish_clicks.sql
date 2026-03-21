-- Add total_fish_clicks: cumulative lifetime count, never decremented.
-- fish_clicks remains the spendable currency.
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS total_fish_clicks BIGINT NOT NULL DEFAULT 0;
