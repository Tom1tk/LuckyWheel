-- Season 8: community goals (replaces community_pot)
CREATE TABLE IF NOT EXISTS community_goals (
    id            SERIAL PRIMARY KEY,
    goal_id       VARCHAR(32) NOT NULL,
    season_number INTEGER NOT NULL,
    week_number   INTEGER NOT NULL,
    target        INTEGER NOT NULL,
    current       INTEGER NOT NULL DEFAULT 0,
    completed     BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at  TIMESTAMPTZ,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(season_number, week_number)
);

CREATE TABLE IF NOT EXISTS community_goal_contributions (
    goal_id     VARCHAR(32) NOT NULL,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contributed INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (goal_id, user_id)
);
