-- Migration 070: T230 — delete standalone double-down chat messages.
--
-- T229 introduced the big-win tier ladder in chat. T230 goes one step
-- further: a double-down that lands a big win used to post TWO messages
-- (a 🔥 'X won a Nx double-down for M' and a 💰 'X won M in MODE' for
-- the same win), which was a duplicate. The two are now merged into
-- one big-win-style message at generation time (chat_triggers.py +
-- game.py), so going forward only ONE message is posted.
--
-- This migration removes the 8 historical standalone double-down
-- messages from chat_messages. The player's per-user big_win (the
-- most recent one) is preserved — and that big_win would have been
-- updated in place via the per-player dedup, so the chat still
-- surfaces the most-relevant big-win info.
--
-- The migration is idempotent: re-running finds no rows to delete
-- and reports 0 affected.

BEGIN;

DELETE FROM chat_messages
 WHERE message_type = 'system'
   AND message ~ '^🔥 .* won a \d+x double-down for ';

-- Idempotency report: zero rows deleted on a re-run.
DO $$
DECLARE
    remaining integer;
BEGIN
    SELECT COUNT(*) INTO remaining
      FROM chat_messages
     WHERE message_type = 'system'
       AND message ~ '^🔥 .* won a \d+x double-down for ';
    RAISE NOTICE 'T230 double-down cleanup complete: % legacy messages remain', remaining;
END;
$$;

COMMIT;
