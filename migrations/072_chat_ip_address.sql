-- 072: Capture the originating user's IP on chat messages.
--
-- T241 hid test users from /api/leaderboard by adding a `WHERE
-- u.ip_address <> '127.0.0.1'` filter on the join. The same pattern
-- is needed on /api/chat, but chat_messages stores the username
-- denormalized (no FK to users for system messages, and the test
-- pollution is in the *text* of system messages, not the row's
-- user_id). The cleanest fix: add an `ip_address INET` column on
-- chat_messages itself, populate it on INSERT, and filter on it at
-- SELECT time.
--
-- New rows (post-migration) carry the IP of the user who triggered
-- the message. System messages with a triggering user_id copy that
-- user's IP; user messages copy the poster's IP. The new
-- _build_chat_query filter is `ip_address IS NULL OR ip_address <>
-- '127.0.0.1'` (NULL = system message not tied to a known user;
-- we accept those because they would have failed the join filter
-- before T241 anyway).
--
-- Backfill: 0 rows. The 106 test-user "first spin" system messages
-- already in chat_messages are deleted by a one-off cleanup script
-- (see deploy notes) — they have no triggering user_id and their
-- text is the only signal of test pollution. Backfilling would
-- require parsing the text, which is fragile.
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS ip_address INET;
CREATE INDEX IF NOT EXISTS idx_chat_messages_ip_created
  ON chat_messages (ip_address, created_at DESC);
