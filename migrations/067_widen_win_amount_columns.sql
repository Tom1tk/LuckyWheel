-- 067: T225 — Widen win-amount columns to BIGINT
--
-- Bug (operator, 2026-06-27, dylan user_id=5): dylan kept getting
-- "spin failed" 500 errors. Stack trace showed:
--     psycopg2.errors.NumericValueOutOfRange: integer out of range
-- at game.py:1456 (the manual /api/spin UPDATE).
--
-- Root cause: T219 (jackpot-as-win + 5M cap removed) let dylan's
-- wager mode payouts grow without bound. Two columns that store
-- win amounts remained typed as INTEGER (signed 32-bit, max
-- 2,147,483,647):
--   - wager_last_win_amount  (dylan: 2,103,551,393 = 98% of max)
--   - biggest_win_announced  (dylan: 2,103,551,393 = 98% of max)
-- Two more sit at 0 today but are structurally the same kind of
-- value and would overflow in a single large wager for any player:
--   - wager_banked_wins
--   - wager_banked_losses
--
-- On a winning spin that produced a wins_delta or payout above the
-- 43M headroom, the UPDATE raised NumericValueOutOfRange and the
-- client received a 500. This is why dylan was intermittently
-- unable to spin: small wins / losses worked, big wins crashed.
--
-- Fix: ALTER COLUMN ... TYPE BIGINT on all four. BIGINT is 8 bytes
-- with a max of 9,223,372,036,854,775,807 (~9.2 × 10^18) — far
-- more than any plausible spin payout. ALTER TYPE on a numeric /
-- int column is a table rewrite in PG, but game_state is small
-- (<100 rows) so this is cheap.
--
-- The USING clause is a defensive no-op cast: PG already knows the
-- values fit in bigint (they fit in int, and int fits in bigint),
-- so the rewrite just widens the storage.
--
-- Idempotent: ALTER TYPE on a column that's already BIGINT is a
-- cheap no-op (Postgres 9.2+ skips the table rewrite when the new
-- type is the same internal representation, but for int→bigint it
-- does rewrite; on a re-run the rewrite just rewrites the same
-- values). Safe to re-run.

ALTER TABLE game_state
    ALTER COLUMN wager_last_win_amount TYPE BIGINT USING wager_last_win_amount::BIGINT,
    ALTER COLUMN biggest_win_announced TYPE BIGINT USING biggest_win_announced::BIGINT,
    ALTER COLUMN wager_banked_wins    TYPE BIGINT USING wager_banked_wins::BIGINT,
    ALTER COLUMN wager_banked_losses  TYPE BIGINT USING wager_banked_losses::BIGINT;
