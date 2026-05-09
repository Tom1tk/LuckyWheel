-- Add an optional display name to seasons so we can label seasons like "7.7"
-- without changing the integer season_number used internally.
ALTER TABLE seasons ADD COLUMN IF NOT EXISTS name TEXT;
