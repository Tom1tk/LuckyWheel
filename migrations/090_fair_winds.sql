-- 090: Fair Winds (Tide 9.4): today's picked boon and when it was picked.
-- Kept apart from owned_items/talent_alloc so a boon can never stick. Idempotent.
ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS fair_winds_boon TEXT,
    ADD COLUMN IF NOT EXISTS fair_winds_at TIMESTAMPTZ;
