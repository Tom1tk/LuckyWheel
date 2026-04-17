-- Telemetry columns for detecting scripted reeling patterns.
-- suspicious_catches counts reel events below the human-floor threshold.
-- catch_count is total successful catches for EWMA normalisation.
-- catch_pct_ewma is the exponential moving average of precise_pct.
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS suspicious_catches INT NOT NULL DEFAULT 0;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS catch_count        INT NOT NULL DEFAULT 0;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS catch_pct_ewma     FLOAT;
