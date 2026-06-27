"""Tests for chat_triggers.py — message formatters and threshold constants."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import chat_triggers
from format_wins import format_wins


def test_double_down_win_msg_format():
    msg = chat_triggers.double_down_win_msg('bob', 10, 7500)
    assert msg == f'🔥 bob won a 10x double-down for {format_wins(7500)} wins!'


def test_hot_streak_msg_format():
    msg = chat_triggers.hot_streak_msg('carol')
    # Threshold value comes from the module constant.
    assert msg == f'🔥 carol reached a {chat_triggers.HOT_STREAK_MSG_THRESHOLD}-win hot streak!'


def test_big_win_msg_format():
    msg = chat_triggers.big_win_msg('dave', 6000, 'mirror')
    assert msg == f'💰 dave won {format_wins(6000)} wins in mirror mode!'


def test_prestige_msg_format():
    msg = chat_triggers.prestige_msg('eve', 3)
    assert msg == '⭐ eve reached Prestige Level 3!'


def test_new_player_msg_format():
    msg = chat_triggers.new_player_msg('frank')
    assert msg == '🎉 frank spun the wheel for the first time! Welcome to Season 8!'


def test_singularity_fill_msg_format():
    msg = chat_triggers.singularity_fill_msg(100000)
    assert msg == '🌀 The Singularity has converged! Total contributed: 100000'


def test_goal_milestone_msg_format():
    msg = chat_triggers.goal_milestone_msg(50, 500, 1000)
    assert msg == 'Community goal at 50%: 500 / 1000'


def test_threshold_constants():
    # T221: JACKPOT_MSG_ALWAYS removed (no more jackpot messages).
    assert not hasattr(chat_triggers, 'JACKPOT_MSG_ALWAYS'), (
        "JACKPOT_MSG_ALWAYS must be removed (T221: no jackpot messages)"
    )
    assert chat_triggers.DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE == 5
    assert chat_triggers.HOT_STREAK_MSG_THRESHOLD == 10
    assert chat_triggers.BIG_WIN_THRESHOLD == 5000


def test_no_jackpot_msg_formatter():
    """T221: chat_triggers.jackpot_msg is removed. Jackpots no longer
    produce any chat message format."""
    assert not hasattr(chat_triggers, 'jackpot_msg'), (
        "chat_triggers.jackpot_msg must be removed (T221: no jackpot messages)"
    )


def test_big_win_msg_no_was_jackpot_param():
    """T221: big_win_msg dropped the was_jackpot kwarg. Calling it with
    was_jackpot=True must raise (no silent fall-through)."""
    import pytest
    with pytest.raises(TypeError):
        chat_triggers.big_win_msg('alice', 6000, 'mirror', was_jackpot=True)
