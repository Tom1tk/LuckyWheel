-- 065: T222 follow-up — backfill user_id on legacy NULL-event-kind
-- prestige messages.
--
-- Migration 064 assumed all prestige messages had event_kind='prestige',
-- but the legacy post_system_message path never set event_kind. So the
-- backfill UPDATE in 064 was a no-op for those rows. They stayed with
-- user_id=NULL and event_kind=NULL, which means the per-user dedup
-- SELECT can't find them (it filters by user_id + event_kind).
--
-- This migration fixes that:
--   1. Tag legacy NULL-event-kind messages that look like prestige
--      announcements with event_kind='prestige' (so the dedup path
--      can see them in future posts).
--   2. Backfill user_id by matching the username in the message body.
--   3. Keep only the latest per user (delete older duplicates).
--
-- Idempotent: re-running finds no rows to update and deletes nothing.

-- Step 1: tag the legacy NULL-event-kind prestige messages.
UPDATE chat_messages
   SET event_kind = 'prestige'
 WHERE event_kind IS NULL
   AND message LIKE '⭐ % reached Prestige Level %';

-- Step 2: backfill user_id from the embedded username.
UPDATE chat_messages cm
   SET user_id = u.id
  FROM users u
 WHERE cm.event_kind = 'prestige'
   AND cm.user_id IS NULL
   AND cm.message LIKE ('⭐ ' || u.username || ' reached Prestige Level %');

-- Step 3: keep only the latest per user; delete the rest (and any
-- remaining NULL-user-id rows that didn't backfill).
DELETE FROM chat_messages
 WHERE event_kind = 'prestige'
   AND id NOT IN (
       SELECT MAX(id) FROM chat_messages
        WHERE event_kind = 'prestige'
          AND user_id IS NOT NULL
        GROUP BY user_id
   );
