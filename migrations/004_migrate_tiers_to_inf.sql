-- Convert existing fixed tier ownership to inf_level columns.
-- GREATEST ensures this is safe to re-run (won't downgrade a level already set).
UPDATE game_state SET
    winmult_inf_level = GREATEST(winmult_inf_level,
        CASE
            WHEN 'winmult_7' = ANY(owned_items) THEN 7
            WHEN 'winmult_6' = ANY(owned_items) THEN 6
            WHEN 'winmult_5' = ANY(owned_items) THEN 5
            WHEN 'winmult_4' = ANY(owned_items) THEN 4
            WHEN 'winmult_3' = ANY(owned_items) THEN 3
            WHEN 'winmult_2' = ANY(owned_items) THEN 2
            WHEN 'winmult_1' = ANY(owned_items) THEN 1
            ELSE 0
        END),
    bonusmult_inf_level = GREATEST(bonusmult_inf_level,
        CASE
            WHEN 'bonusmult_6' = ANY(owned_items) THEN 6
            WHEN 'bonusmult_5' = ANY(owned_items) THEN 5
            WHEN 'bonusmult_4' = ANY(owned_items) THEN 4
            WHEN 'bonusmult_3' = ANY(owned_items) THEN 3
            WHEN 'bonusmult_2' = ANY(owned_items) THEN 2
            WHEN 'bonusmult_1' = ANY(owned_items) THEN 1
            ELSE 0
        END),
    clickmult_inf_level = GREATEST(clickmult_inf_level,
        CASE
            WHEN 'double_click_5' = ANY(owned_items) THEN 5
            WHEN 'double_click_4' = ANY(owned_items) THEN 4
            WHEN 'double_click_3' = ANY(owned_items) THEN 3
            WHEN 'double_click_2' = ANY(owned_items) THEN 2
            WHEN 'double_click'   = ANY(owned_items) THEN 1
            ELSE 0
        END);
