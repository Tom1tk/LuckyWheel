-- Tide Regatta: each tide day is a race; a player's first 3 stakes in it count.
CREATE TABLE IF NOT EXISTS regatta_stakes (
    user_id   INTEGER  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tide_date DATE     NOT NULL,
    race      SMALLINT NOT NULL CHECK (race BETWEEN 1 AND 7),
    n         SMALLINT NOT NULL CHECK (n BETWEEN 1 AND 3),
    result    TEXT     NOT NULL,
    score     SMALLINT NOT NULL,
    at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, tide_date, race, n)
);
CREATE INDEX IF NOT EXISTS regatta_stakes_tide ON regatta_stakes (tide_date, race);

-- One row per finished race, so its chat line posts once.
CREATE TABLE IF NOT EXISTS regatta_announced (
    tide_date DATE     NOT NULL,
    race      SMALLINT NOT NULL,
    PRIMARY KEY (tide_date, race)
);
