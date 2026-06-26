-- 053: T117 — per-bounty claim tracking.
-- The legacy claim gate was a single per-day `bounty_claimed_date` column
-- on game_state (migration 044). That gate prevented multiple claims per
-- day, which is incompatible with the per-bounty semantics introduced in
-- T117 (each completed bounty has its own Claim button granting
-- position-based tokens; max 6 tokens/day across the 3 daily bounties).
-- We add per-bounty `claimed` / `claimed_at` columns on `bounty_progress`
-- (the natural key is the (user_id, bounty_date, bounty_id) primary key,
-- already in place from migration 036).
-- The legacy `game_state.bounty_claimed_date` column is intentionally LEFT
-- IN PLACE for now: the T43 onboarding gate still references it (see
-- prestige.py PRESTIGE_RESET_COLUMNS) and T119 is a later round that may
-- drop it. Removing it here would expand the diff and risk breaking
-- T43/T119.
ALTER TABLE bounty_progress
  ADD COLUMN IF NOT EXISTS claimed    BOOLEAN     NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;
