-- Season 8: singularity rework — community meter replaces personal purchase
CREATE TABLE IF NOT EXISTS singularity_meter (
    id                 INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    total_contributed  BIGINT  NOT NULL DEFAULT 0,
    target             BIGINT  NOT NULL DEFAULT 100000000,
    filled             BOOLEAN NOT NULL DEFAULT FALSE,
    filled_at          TIMESTAMPTZ,
    fill_count         INTEGER NOT NULL DEFAULT 0
);

INSERT INTO singularity_meter (id)
VALUES (1)
ON CONFLICT (id) DO NOTHING;
