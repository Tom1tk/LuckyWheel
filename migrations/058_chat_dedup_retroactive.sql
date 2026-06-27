-- Migration 058: T209 retroactive chat dedup.
--
-- Adds the event_kind column to chat_messages (so per-user dedup of
-- auto-posted system messages can target the right rows) and cleans up
-- the operator's existing chat backlog: for each (user_id, event_kind)
-- pair in DEDUP_EVENT_KINDS, keep only the most recent message and
-- delete older duplicates. First-spin and prestige messages
-- (event_kind = 'first_spin', 'prestige', or NULL) are NOT touched --
-- they're historical records the operator wants preserved.
--
-- Idempotent: re-running is a no-op once the backlog is deduped, and
-- the ALTER / UPDATE statements are guarded with IF NOT EXISTS / IS NULL.

ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS event_kind VARCHAR(32);

-- Backfill event_kind for existing system messages based on the message
-- content patterns emitted by chat_triggers.py. New posts set
-- event_kind via post_dedup_system_message directly.
UPDATE chat_messages SET event_kind = 'big_win'
WHERE message_type = 'system' AND event_kind IS NULL
  AND (message LIKE '💰 %won %wins in %mode!'
    OR message LIKE '🎰 %hit a %jackpot in %mode!');

UPDATE chat_messages SET event_kind = 'hot_streak'
WHERE message_type = 'system' AND event_kind IS NULL
  AND message LIKE '🔥 %reached a %-win hot streak!';

UPDATE chat_messages SET event_kind = 'goal_milestone_25'
WHERE message_type = 'system' AND event_kind IS NULL
  AND message LIKE 'Community goal at 25:%';

UPDATE chat_messages SET event_kind = 'goal_milestone_50'
WHERE message_type = 'system' AND event_kind IS NULL
  AND message LIKE 'Community goal at 50:%';

UPDATE chat_messages SET event_kind = 'goal_milestone_75'
WHERE message_type = 'system' AND event_kind IS NULL
  AND message LIKE 'Community goal at 75:%';

-- Dedup: for each (user_id, event_kind) pair in DEDUP_EVENT_KINDS, keep
-- only the most recent chat message; delete older duplicates. Safe to
-- re-run — once the set is deduped, ROW_NUMBER() = 1 for every row and
-- the DELETE matches nothing.
DELETE FROM chat_messages
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (
            PARTITION BY user_id, event_kind
            ORDER BY created_at DESC, id DESC
        ) AS rn
        FROM chat_messages
        WHERE message_type = 'system'
          AND event_kind IN (
              'big_win',
              'hot_streak',
              'goal_milestone_25',
              'goal_milestone_50',
              'goal_milestone_75'
          )
    ) t
    WHERE rn > 1
);
