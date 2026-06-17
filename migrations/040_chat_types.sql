-- Season 8: chat message types (chat, replay, system, event)
ALTER TABLE chat_messages
    ADD COLUMN IF NOT EXISTS message_type VARCHAR(16) NOT NULL DEFAULT 'chat';
