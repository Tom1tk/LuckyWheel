"""Tests for the Season 9 community-goal target retunes.

Season 8 postmortem: only goal_wager100k got close (15k / 100k) and
goal_fish5000 had 0 / 5,000. The per-week targets were sized for ~50 players
but the server has ~5 active players, so targets were trimmed while keeping
the per-player caps (which already scale to the small population).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from community_goals import COMMUNITY_GOAL_DEFS


def _def(goal_id):
    return next(g for g in COMMUNITY_GOAL_DEFS if g['goal_id'] == goal_id)


def test_fish_goal_retuned():
    assert _def('goal_fish5000')['target'] == 1500, (
        "goal_fish5000 target should be 1,500 (was 5,000)"
    )


def test_jackpot_goal_retuned():
    assert _def('goal_jackpot500')['target'] == 100, (
        "goal_jackpot500 target should be 100 (was 500)"
    )


def test_prestige_goal_retuned():
    assert _def('goal_prestige50')['target'] == 20, (
        "goal_prestige50 target should be 20 (was 50)"
    )


def test_wager_goal_retuned():
    assert _def('goal_wager100k')['target'] == 25_000, (
        "goal_wager100k target should be 25,000 (was 100,000)"
    )


def test_species_goal_retuned():
    assert _def('goal_species100')['target'] == 100, (
        "goal_species100 target should stay 100"
    )


def test_every_goal_keeps_its_reward_and_cap():
    for g in COMMUNITY_GOAL_DEFS:
        assert g['per_player_cap'] > 0
        assert g['reward_tokens'] == 500
        assert g['reward_fragments'] == 1


def test_migration_075_present():
    root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(root, 'migrations', '075_community_goals_retune.sql')
    assert os.path.exists(path), "075_community_goals_retune.sql must exist"
    with open(path) as f:
        src = f.read()
    for target in ('1500', '100', '20', '25000'):
        assert target in src, f"migration must reference target {target}"
