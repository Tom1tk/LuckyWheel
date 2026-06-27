-- Migration 069: T229 — reformat existing chat win numbers using the
-- T227 tier ladder (K, M, B, T, scientific) — same as static/js/format.js
-- and the new format_wins.py module.
--
-- This is a one-time cleanup pass. chat_triggers.py was updated in T229
-- so that *new* system messages are formatted at generation time. This
-- migration just re-formats the 9 messages already in the DB:
--
--   pre:  '🔥 dylan won a 45x double-down for 3405169339238 wins!'
--   post: '🔥 dylan won a 45x double-down for 3.41T wins!'
--
-- Two patterns are matched (mutually exclusive per message):
--   1) big_win:      "won N wins in M mode!"            -- format N
--   2) double_down:  "won a Nx double-down for M wins!" -- format M
--
-- The migration is idempotent: the regex 'won \d+ wins' doesn't match
-- a formatted value like 'won 140.46T wins' (the dot breaks the
-- \d+ run), so a re-run is a no-op.

-- The same tier ladder as format_wins.format_wins (Python) and
-- static/js/format.js format_wins (JS). Drift between these three
-- implementations should be caught by their respective test files
-- (tests/test_format_wins.py for JS, tests/test_format_wins_python.py
-- for Python, and the explicit 'post' assertions below for SQL).
CREATE OR REPLACE FUNCTION _t229_format_wins(n numeric) RETURNS text AS $$
DECLARE
    abs_val numeric;
    neg boolean;
    s text;
BEGIN
    IF n IS NULL OR n = 'NaN'::numeric THEN
        RETURN '0';
    END IF;

    neg := n < 0;
    abs_val := abs(n);

    IF abs_val < 1000 THEN
        s := round(abs_val)::text;
    ELSIF abs_val < 1000000 THEN
        s := regexp_replace(round((abs_val / 1000)::numeric, 1)::text, '\.?0+$', '');
        s := s || 'K';
    ELSIF abs_val < 1000000000 THEN
        s := regexp_replace(round((abs_val / 1000000)::numeric, 2)::text, '\.?0+$', '');
        s := s || 'M';
    ELSIF abs_val < 1000000000000 THEN
        s := regexp_replace(round((abs_val / 1000000000)::numeric, 2)::text, '\.?0+$', '');
        s := s || 'B';
    ELSIF abs_val < 1000000000000000 THEN
        s := regexp_replace(round((abs_val / 1000000000000)::numeric, 2)::text, '\.?0+$', '');
        s := s || 'T';
    ELSE
        -- Scientific notation. The '9.99EEEE' format (4 E's, no FM
        -- mode) handles arbitrary exponents (1e15 through 1e1000+).
        -- Notes from trial-and-error on Postgres 16:
        --   * 2-E and 3-E forms ('0.00EE', '0.00EEE') give ' #.##EE'
        --     for 3.59e16+ — the format width is too narrow.
        --   * 5-E+ forms ('0.00EEEEE') are rejected with
        --     "EEEE is incompatible with other formats".
        --   * '0.00EEEE' works but prepends a space (sign placeholder).
        --   * '9.99EEEE' works AND no leading space. Use this.
        -- Output is lowercase 'e+' to match static/js/format.js and
        -- format_wins.py.
        s := to_char(abs_val, '9.99EEEE');
    END IF;

    IF neg THEN
        s := '-' || s;
    END IF;
    RETURN s;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Apply to all system messages with win numbers.
DO $$
DECLARE
    msg_record RECORD;
    new_message text;
    m text;
    updated_count integer := 0;
BEGIN
    FOR msg_record IN
        SELECT id, message
        FROM chat_messages
        WHERE message_type = 'system'
          AND (message ~ 'won \d+ wins' OR message ~ 'double-down for \d+ wins')
    LOOP
        new_message := msg_record.message;

        -- Pattern 1: big_win "won N wins"
        WHILE new_message ~ 'won \d+ wins' LOOP
            m := (regexp_match(new_message, 'won (\d+) wins'))[1];
            new_message := regexp_replace(
                new_message,
                'won \d+ wins',
                'won ' || _t229_format_wins(m::numeric) || ' wins'
            );
        END LOOP;

        -- Pattern 2: double_down "double-down for N wins"
        WHILE new_message ~ 'double-down for \d+ wins' LOOP
            m := (regexp_match(new_message, 'double-down for (\d+) wins'))[1];
            new_message := regexp_replace(
                new_message,
                'double-down for \d+ wins',
                'double-down for ' || _t229_format_wins(m::numeric) || ' wins'
            );
        END LOOP;

        IF new_message IS DISTINCT FROM msg_record.message THEN
            UPDATE chat_messages SET message = new_message WHERE id = msg_record.id;
            updated_count := updated_count + 1;
            RAISE NOTICE 'T229 reformat id=% : % -> %', msg_record.id, msg_record.message, new_message;
        END IF;
    END LOOP;

    RAISE NOTICE 'T229 reformat complete: % messages updated', updated_count;
END;
$$;

-- Drop the helper function (kept only for the duration of this migration).
DROP FUNCTION _t229_format_wins(numeric);
