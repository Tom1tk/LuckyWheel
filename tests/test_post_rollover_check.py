"""RV-10: cosmetics/species kept check in bin/post_rollover_check.py (pure, no database)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'bin'))
import post_rollover_check  # noqa: E402


def test_new_species_and_cosmetics_are_not_a_loss():
    sample = [[1, ['fish_a'], ['carp']]]
    now = {1: ({'fish_a', 'fish_b'}, {'carp', 'trout'})}
    assert post_rollover_check.find_lost(sample, now) == ({}, {})


def test_lost_species_is_reported():
    sample = [[1, [], ['carp', 'trout']]]
    now = {1: (set(), {'carp'})}
    assert post_rollover_check.find_lost(sample, now) == ({}, {1: ['trout']})


def test_sampled_user_missing_from_now_counts_as_lost():
    sample = [[7, ['fish_a'], []]]
    assert post_rollover_check.find_lost(sample, {}) == ({7: ['fish_a']}, {})
