-- Season 9: retune the singularity community meter.
-- Season 8 postmortem: the 100M target never filled (147,930 / 100M in the
-- whole era — 99.3% from one player). Lowering to 5M makes a cycle
-- convergible by a handful of active players; models.SINGULARITY_PER_PLAYER_CAP
-- is lowered in parallel (2M per player per cycle) so no single player can
-- solo-fill it. Total_contributed is kept (the meter keeps its progress).
UPDATE singularity_meter SET target = 5000000 WHERE id = 1;
