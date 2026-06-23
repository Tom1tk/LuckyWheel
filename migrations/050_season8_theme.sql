-- Grant the Season 8 casino background theme (page_season8) to all existing
-- users so it is owned and switchable from the cosmetic store. Unlike the
-- Season 7 migration this does NOT force-equip it — the operator equips it
-- (or force-equips at ship time) after sign-off on the visuals.
UPDATE game_state SET
  owned_items = CASE
    WHEN 'page_season8' = ANY(owned_items) THEN owned_items
    ELSE array_append(owned_items, 'page_season8')
  END;
