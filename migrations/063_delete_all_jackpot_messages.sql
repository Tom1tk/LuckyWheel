-- 063: Delete all jackpot chat messages
--
-- T221: jackpot messages are gone entirely. Neither the old format
-- ("🎰 X hit a JACKPOT in M mode at Nx stake for K wins!") nor the
-- new was_jackpot re-style ("🎰 X hit a N jackpot in M mode!") should
-- be in chat. This migration deletes every row that contains 'jackpot'
-- (case-insensitive) in the message body. Regular big_win messages
-- ("💰 X won N wins in M mode!") are untouched.
--
-- Idempotent: re-running the migration finds no 'jackpot' messages and
-- deletes 0 rows.

DELETE FROM chat_messages
 WHERE message ILIKE '%jackpot%';
