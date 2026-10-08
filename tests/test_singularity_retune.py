"""Tests for the Season 9 singularity meter retune (100M → 5M target)."""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import models

ROOT = os.path.dirname(os.path.dirname(__file__))
MIG = os.path.join(ROOT, 'migrations', '074_singularity_retune.sql')


def test_per_player_cap_retuned():
    assert models.SINGULARITY_PER_PLAYER_CAP == 2_000_000, (
        "Season 9 singularity per-player cap should be 2M (was 25M)"
    )


def test_migration_sets_5m_target():
    assert os.path.exists(MIG), "074_singularity_retune.sql must exist"
    with open(MIG) as f:
        src = f.read()
    assert re.search(r'UPDATE\s+singularity_meter\s+SET\s+target\s*=\s*5000000',
                     src), (
        "migration must set singularity_meter.target to 5,000,000"
    )


def test_game_fallback_target_is_5m():
    game_src = open(os.path.join(ROOT, 'game.py')).read()
    # The /api/state + /api/singularity responses must fall back to 5M when
    # the meter row is missing (kept in sync with the migration's target).
    assert re.search(r"5_000_000", game_src), (
        "game.py must use 5_000_000 as the singularity fallback target"
    )


def test_meter_progress_is_preserved():
    """Total_contributed must not be reset by the retune (keeps progress)."""
    with open(MIG) as f:
        src = f.read()
    assert 'total_contributed' not in src, (
        "migration must not touch total_contributed — the meter keeps progress"
    )
