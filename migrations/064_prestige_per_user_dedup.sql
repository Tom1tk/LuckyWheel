-- 064: T222 — Per-user prestige dedup + backfill user_id
--
-- The old post_system_message() always set user_id=NULL and didn't set
-- event_kind. After T209 added per-user dedup via post_dedup_system_message,
-- prestige still wasn't in the dedup set so this didn't matter — but T222
-- adds prestige to the dedup set, which means a user_id IS needed for
-- the per-user cleanup to actually be per-user.
--
-- This migration:
--   1. Tags legacy NULL-event_kind prestige messages (from the old code)
--      with event_kind='prestige' so they're findable by the dedup path.
--   2. Backfills user_id on existing prestige messages by parsing the
--      username out of the message text ("⭐ {user} reached Prestige
--      Level {N}!" → look up users.username = the captured user).
--   3. Deletes all but the LATEST prestige message per user (one row
--      per user, the most recent one).
--
-- Idempotent: re-running after a successful first pass is a no-op (the
-- tagging UPDATE is filtered on event_kind IS NULL, the backfill is
-- filtered on user_id IS NULL, and the DELETE's subquery is empty).
--
-- (T222 follow-up 065 was added because the original 064 didn't tag the
-- legacy NULL-event_kind rows — see that migration for the backfill fix
-- that was applied separately to a live DB. Both 064 and 065 are correct
-- for fresh-DB initialisation; 065 exists to retroactively clean a DB
-- where 064 ran first.)

-- Step 1: tag the legacy NULL-event_kind prestige messages.
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

-- Step 3: for each user, keep only their most recent prestige message.
-- Any remaining NULL-user_id prestige messages (the old format that
-- predates any user lookup) are deleted entirely — they can't be
-- attributed to a user and would just be ungrouped dedup noise.
DELETE FROM chat_messages
 WHERE event_kind = 'prestige'
   AND id NOT IN (
       SELECT MAX(id) FROM chat_messages
        WHERE event_kind = 'prestige'
          AND user_id IS NOT NULL
        GROUP BY user_id
   );
