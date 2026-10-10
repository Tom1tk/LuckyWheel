from game import RECENT_SPINS_KEPT, _push_recent_spin


def test_recent_spins_are_newest_first_and_capped():
    recent = []
    for i in range(RECENT_SPINS_KEPT + 3):
        recent = _push_recent_spin(recent, {'result': 'win', 'wins_delta': i})
    assert len(recent) == RECENT_SPINS_KEPT
    assert recent[0] == {'result': 'win', 'wins_delta': RECENT_SPINS_KEPT + 2}
    assert recent[-1]['wins_delta'] == 3


def test_recent_spins_handles_a_missing_log_and_negative_delta():
    assert _push_recent_spin(None, {'result': 'lose', 'wins_delta': -5}) == [{'result': 'lose', 'wins_delta': -5}]
