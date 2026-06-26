-- Season 8: force-equip the casino page theme (page_season8) for all existing
-- users so everyone is on it by default. Grants ownership if missing (050 may
-- already have done so) and makes it the active page theme, removing any other
-- page_seasonN from active_cosmetics. Players can switch back in the shop.
UPDATE game_state SET
  owned_items = CASE
    WHEN 'page_season8' = ANY(owned_items) THEN owned_items
    ELSE array_append(owned_items, 'page_season8')
  END,
  active_cosmetics = array_append(
    ARRAY(SELECT c FROM unnest(active_cosmetics) AS c
          WHERE c NOT IN ('page_season1','page_season2','page_season3',
                          'page_season4','page_season5','page_season6',
                          'page_season7','page_season8')),
    'page_season8'
  );
