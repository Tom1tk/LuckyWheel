"""Tide 9.3: offline catch-up reaches 72 h back, or to the turn on a first visit."""
from datetime import datetime, timedelta, timezone

import talents

UTC = timezone.utc
# Fri 23 Oct 2026 21:00 BST = 20:00 UTC; Sat 24 Oct 21:00 is still BST.
TURN = datetime(2026, 10, 23, 20, 0, tzinfo=UTC)


def test_tide_start_is_last_friday_turn():
    assert talents.tide_start(TURN + timedelta(days=3)) == TURN
    assert talents.tide_start(TURN) == TURN
    assert talents.tide_start(TURN - timedelta(minutes=1)) == TURN - timedelta(days=7)


def test_returning_player_gets_72h():
    now = TURN + timedelta(days=5)
    last = now - timedelta(days=4)  # seen this tide
    assert talents.offline_floor(now, last) == now - timedelta(hours=72)


def test_first_visit_reaches_back_to_the_turn():
    now = TURN + timedelta(days=5)
    last = TURN - timedelta(days=2)  # last seen in the previous tide
    assert talents.offline_floor(now, last) == TURN


def test_first_visit_soon_after_turn_keeps_72h():
    now = TURN + timedelta(hours=2)
    last = TURN - timedelta(days=2)
    assert talents.offline_floor(now, last) == now - timedelta(hours=72)
