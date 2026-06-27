-- 061: T209 follow-up #2 — per-player chat dedup + remove defunct jackpot format.
--
-- Two problems with the prior cleanup (migrations 058 + 060):
--
-- 1. The OLD jackpot message format ('🎰 X hit a JACKPOT in M mode at Nx
--    stake for K wins!') is DEFUNCT. The new chat code (post-T209) no
--    longer emits jackpot-format messages — jackpots are re-styled via
--    the was_jackpot parameter on big_win_msg, producing the SAME format
--    as a regular big_win ('💰 X won N wins in M mode!'). The 15 old
--    jackpot messages in the chat are noise. Delete them.
--
-- 2. ALL old system messages have user_id=NULL (the old post_system_message
--    always set user_id=NULL). The dedup DELETE PARTITION BY (user_id,
--    event_kind) therefore groups every system message into ONE bucket,
--    so only 1 message per event_kind survives across ALL users. The
--    operator wants per-player dedup: each player has their own big_win
--    in chat, overwritten only when THAT player gets a bigger win.
--    The new chat code (post_dedup_system_message) correctly uses
--    user_id=current_user.id for new messages — we just need to backfill
--    user_id on the old messages for the retroactive cleanup.
--
-- This migration:
--   1. Deletes all old-format jackpot messages (defunct — new code
--      never emits this format).
--   2. Backfills user_id on remaining system messages by parsing the
--      username from the message content (the format is consistently
--      '<emoji> <username> <verb> ...').
--   3. Backfills event_kind for first_spin + prestige (they were never
--      in the dedup set, but tagging them keeps the data clean and the
--      next dedup pass will skip them as expected).
--   4. Re-runs the per-user dedup DELETE.
--
-- Idempotency: the jackpot DELETE is unconditional on the message
-- pattern (no rows match on a re-run). The user_id backfill only
-- touches rows where user_id IS NULL (no-op on re-run). The event_kind
-- backfill only touches rows where event_kind IS NULL AND user_id IS
-- NULL (no-op on re-run). The dedup DELETE is safe to re-run (after
-- dedup, ROW_NUMBER()=1 for every row in the partition and WHERE rn>1
-- matches nothing).

-- Step 1: delete the defunct jackpot-format messages
DELETE FROM chat_messages
 WHERE message_type = 'system'
   AND message LIKE '🎰 %hit a JACKPOT%';

-- Step 2: backfill user_id + event_kind by parsing the username.
-- The format is consistently '<emoji> <username> <verb> ...'. We match
-- on '<emoji> <username> <verb>' to avoid false matches like 'tom' from
-- 'tom7' (since 'tom won' won't match a message saying 'tom7 won').

UPDATE chat_messages cm
   SET user_id = u.id, event_kind = 'big_win'
  FROM users u
 WHERE cm.message_type = 'system'
   AND cm.user_id IS NULL
   AND cm.message LIKE '💰 ' || u.username || ' won %';

UPDATE chat_messages cm
   SET user_id = u.id, event_kind = 'hot_streak'
  FROM users u
 WHERE cm.message_type = 'system'
   AND cm.user_id IS NULL
   AND cm.message LIKE '🔥 ' || u.username || ' reached a %';

UPDATE chat_messages cm
   SET user_id = u.id, event_kind = 'first_spin'
  FROM users u
 WHERE cm.message_type = 'system'
   AND cm.user_id IS NULL
   AND cm.message LIKE '🎉 ' || u.username || ' spun the wheel%';

UPDATE chat_messages cm
   SET user_id = u.id, event_kind = 'prestige'
  FROM users u
 WHERE cm.message_type = 'system'
   AND cm.user_id IS NULL
   AND cm.message LIKE '⭐ ' || u.username || ' reached Prestige%';

-- Step 3: per-user dedup — keep at most 1 of each (user_id, event_kind)
-- pair. The DEDUP_EVENT_KINDS set (per chat.py) is:
--   big_win, hot_streak, goal_milestone_25, goal_milestone_50, goal_milestone_75
-- first_spin and prestige are NOT in this set and are preserved as
-- historical records.
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
