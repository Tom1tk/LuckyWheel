-- Grant Season 7 wormhole background theme to all existing users and force-equip it
UPDATE game_state SET
  owned_items = CASE
    WHEN 'page_season7' = ANY(owned_items) THEN owned_items
    ELSE array_append(owned_items, 'page_season7')
  END,
  active_cosmetics = array_append(
    ARRAY(SELECT c FROM unnest(active_cosmetics) AS c
          WHERE c NOT IN ('page_season1','page_season2','page_season3',
                          'page_season4','page_season5','page_season6','page_season7')),
    'page_season7'
  );
