-- 068: T226 — Widen win-amount columns to NUMERIC (unlimited)
--
-- Bug (operator, 2026-06-27): T225 widened wager_last_win_amount,
-- biggest_win_announced, wager_banked_wins, wager_banked_losses to
-- BIGINT (max 9,223,372,036,854,775,807). Dylan then grew to:
--   wins                   = 221,775,682,209,505
--   legacy_wins            = 18,991,584,931
--   cumulative_wins        = 221,817,666,596,529
--   biggest_win_announced  = 140,463,137,867,975
-- That's 0.002% of the bigint max, but the operator reports that
-- previous seasons have legitimately hit values exceeding 1e50+.
-- With BIGINT we'd cap at 9.2e18; if 1e50 is the real target we
-- need unlimited precision.
--
-- The two existing win-amount columns that are already NUMERIC
-- (wins, legacy_wins) have been holding huge values across seasons
-- without issue. The two new ones (cumulative_wins already
-- BIGINT, plus the four BIGINTs from T225) are the ones we need
-- to widen.
--
-- Why NUMERIC and not just BIGINT:
--   - wins and legacy_wins are already NUMERIC. Aligning all
--     win-amount columns to NUMERIC keeps the schema consistent
--     and gives us unlimited precision.
--   - 1e50 doesn't fit in BIGINT (max 9.2e18). NUMERIC is the
--     only Postgres type that holds it.
--   - Tradeoff: psycopg2 returns NUMERIC as Python Decimal, so
--     any int() casts in game.py need to handle Decimal. The
--     int(Decimal(...)) call works correctly for the integer
--     values we use (truncates fractional; ours are always
--     integer-valued).
--
-- Cost: this is a table rewrite in PG (ALTER TYPE on a numeric
-- column from bigint/numeric is cheap since values fit, but PG
-- still rewrites). game_state is small (<100 rows) so this is
-- fast.
--
-- JSON serialisation: NUMERIC values that exceed
-- Number.MAX_SAFE_INTEGER (~9e15) lose precision when round-tripped
-- through JavaScript's Number type. This is the same pre-existing
-- condition as wins/legacy_wins and has been the working behavior
-- for previous seasons. The client formats these as scientific
-- notation in format.js, so the display is correct even if the
-- underlying value has lost a few digits of precision.
--
-- Idempotent: ALTER TYPE on a column that's already NUMERIC is a
-- no-op rewrite. Safe to re-run.

ALTER TABLE game_state
    ALTER COLUMN cumulative_wins        TYPE NUMERIC USING cumulative_wins::NUMERIC,
    ALTER COLUMN biggest_win_announced  TYPE NUMERIC USING biggest_win_announced::NUMERIC,
    ALTER COLUMN wager_last_win_amount  TYPE NUMERIC USING wager_last_win_amount::NUMERIC,
    ALTER COLUMN wager_banked_wins      TYPE NUMERIC USING wager_banked_wins::NUMERIC,
    ALTER COLUMN wager_banked_losses    TYPE NUMERIC USING wager_banked_losses::NUMERIC;
