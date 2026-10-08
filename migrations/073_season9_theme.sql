-- Season 9: grant the Arcade page theme (page_season9) to all existing users
-- and equip it by default (removing any other page_seasonN from
-- active_cosmetics). Players can switch back in the shop. Mirrors the
-- Season 8 migration 051 pattern.
UPDATE game_state SET
  owned_items = CASE
    WHEN 'page_season9' = ANY(owned_items) THEN owned_items
    ELSE array_append(owned_items, 'page_season9')
  END,
  active_cosmetics = array_append(
    ARRAY(SELECT c FROM unnest(active_cosmetics) AS c
          WHERE c NOT IN ('page_season1','page_season2','page_season3',
                          'page_season4','page_season5','page_season6',
                          'page_season7','page_season8','page_season9')),
    'page_season9'
  );
