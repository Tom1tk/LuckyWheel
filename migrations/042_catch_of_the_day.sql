-- 042: Track catch-of-the-day date for 5x wager token bonus
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS catch_of_the_day_date DATE;
