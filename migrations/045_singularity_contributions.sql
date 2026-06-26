-- 045: Track each player's lifetime contribution to the current Singularity
-- meter cycle (keyed by fill_count, so the per-player cap resets each time
-- the meter fills and restarts). singularity_contribute() previously had no
-- per-player tracking at all, so the 25,000,000 cap (spec S13) was never
-- enforced.
CREATE TABLE IF NOT EXISTS singularity_contributions (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fill_count  INTEGER NOT NULL,
    contributed BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, fill_count)
);
