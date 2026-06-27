-- 060: T209 follow-up — backfill event_kind for the OLD jackpot message
-- format that migration 058 missed.
--
-- Migration 058's backfill used the NEW chat_triggers.big_win_msg format
-- (which produces messages like '🎰 X hit a N jackpot in M mode!'). The
-- OLD code (pre-T209) emitted a different jackpot message format:
--   '🎰 X hit a JACKPOT in M mode at Nx stake for K wins!'
-- Notes:
--   * 'JACKPOT' is uppercase in the old format
--   * the message has 'at Nx stake for K wins!' instead of the
--     big_win-style 'won N wins in M mode!'
--
-- The 18 jackpot messages from worm67 + tom7 in 2026-06-27 chat were
-- not caught by 058's LIKE pattern, so they kept event_kind = NULL and
-- slipped past the dedup DELETE.
--
-- This migration:
-- 1. Backfills those old-format jackpot messages with event_kind='big_win'
--    (so they participate in the same dedup as the new format).
-- 2. Re-runs the dedup DELETE to collapse them to 1 per user.
--
-- Idempotency: the backfill only touches rows where event_kind IS NULL
-- (so re-running after a successful first pass is a no-op). The dedup
-- DELETE is safe to re-run (after dedup, ROW_NUMBER() = 1 for every row
-- in the partition and the WHERE rn > 1 matches nothing).

UPDATE chat_messages
   SET event_kind = 'big_win'
 WHERE message_type = 'system'
   AND event_kind IS NULL
   AND message LIKE '🎰 %hit a JACKPOT%';

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
