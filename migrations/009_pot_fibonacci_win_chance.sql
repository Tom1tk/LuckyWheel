-- Community Pot: Fibonacci target scaling + progressive win chance
-- Instead of 10x multiplier, targets follow Fibonacci sequence (starting 10k, 10k, 20k, 30k, 50k…)
-- Win chance starts at 51% and increases by 1% per fill, capped at 75%.
ALTER TABLE community_pot
    ADD COLUMN IF NOT EXISTS fib_prev     BIGINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS win_chance_pct INTEGER NOT NULL DEFAULT 51;
