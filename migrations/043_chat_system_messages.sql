-- 043: Allow NULL user_id in chat_messages for system messages.
-- System messages (username='SYSTEM') have no associated user, so the
-- NOT NULL constraint and FK to users must be dropped.

ALTER TABLE chat_messages ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_user_id_fkey;
