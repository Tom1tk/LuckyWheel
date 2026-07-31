-- 062: Restore the most-recent big_win per player that was dropped by
-- migration 060's NULL-user_id dedup.
--
-- Background:
-- 058's retro dedup kept exactly 1 big_win (NULL user_id partition): the
-- one with the highest id, which happened to be id=270 (an old-format
-- JACKPOT, '🎰 worm67 hit a JACKPOT in steady mode at 1x stake for 0
-- wins!') at created_at 05:34:34.
--
-- The new-format big_win id=269 ('💰 worm67 won 2618217 wins in steady
-- mode!', at created_at 05:34:10) was 24 seconds older, so it was
-- dropped by the dedup.
--
-- 060 then backfilled the old-format JACKPOTs (id=270 included) with
-- event_kind='big_win' and re-ran the dedup — same result, id=270 wins.
--
-- 061 then deleted the defunct JACKPOT format entirely. Net result:
-- the worm67 big_win (id=269) was lost, leaving zero big_wins in chat.
--
-- This migration restores the most-recent big_win per player from the
-- 08:43 backup (the last backup taken before any chat cleanup). For
-- each player who had a big_win in their history, the highest-id
-- (== most-recent) '💰 X won Y wins in M mode!' row is re-inserted
-- with the correct user_id + event_kind.
--
-- Idempotency: the INSERT ... WHERE NOT EXISTS guards against
-- re-creating rows that are already present (a re-run finds no
-- missing big_wins and inserts nothing).

INSERT INTO chat_messages (user_id, username, message, created_at, message_type, event_kind)
SELECT u.id, 'SYSTEM', m.message, m.created_at, 'system', 'big_win'
  FROM (VALUES
    -- worm67's most-recent big_win (id=269 from the 08:43 backup)
    (13, '💰 worm67 won 2618217 wins in steady mode!', '2026-06-27 05:34:10.464577+01'::timestamptz),
    -- tom7's most-recent big_win (id=238 from the 08:43 backup)
    (2,  '💰 tom7 won 170376 wins in steady mode!',    '2026-06-27 00:44:08.146034+01'::timestamptz)
  ) AS m(user_id, message, created_at)
  JOIN users u ON u.id = m.user_id
 WHERE NOT EXISTS (
    SELECT 1 FROM chat_messages cm
    WHERE cm.message = m.message
      AND cm.message_type = 'system'
      AND cm.event_kind = 'big_win'
 );
