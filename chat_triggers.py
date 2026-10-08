"""Auto-post system message triggers for Season 8.

Centralizes code-level constants for which events should post a chat message
and the message templates. Used by game.py endpoints to call
post_system_message() with the right event_kind and message text.

T221: jackpot messages are gone entirely. Jackpots no longer post any
system message — neither the old "JACKPOT in M mode at Nx stake" format
nor the "hit a N jackpot" was_jackpot re-style. The `was_jackpot`
parameter on `big_win_msg` is removed; `JACKPOT_MSG_ALWAYS` is removed.

T229: win numbers in big_win_msg and double_down_win_msg are formatted
through format_wins (the Python port of static/js/format.js) so chat
output uses the same tier ladder as the rest of the app (T227).

T230: double_down_win_msg now uses the big-win style format
("💰 X won a Nx double-down for M in MODE mode!") and includes the
mode parameter. The big-win message is suppressed in game.py when a
double-down is active, so a single spin now produces a single message
instead of two. Standalone double-down messages are gone.
"""

from format_wins import format_wins


# ── Trigger thresholds ───────────────────────────────────────────────────────
DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE = 5
HOT_STREAK_MSG_THRESHOLD = 10
BIG_WIN_THRESHOLD = 5000


# ── Message formatters ───────────────────────────────────────────────────────
def double_down_win_msg(username: str, effective_stake: int, wins_delta: int, mode: str) -> str:
    # T230: merged big-win style. The 🔥 emoji is replaced with 💰 so a
    # double-down big win no longer collides visually with the hot-streak
    # milestone (also 🔥). The 'in MODE mode' suffix is borrowed from
    # big_win_msg to give the merged message the same shape.
    return f'💰 {username} won a {effective_stake}x double-down for {format_wins(wins_delta)} wins in {mode} mode!'


def hot_streak_msg(username: str) -> str:
    return f'🔥 {username} reached a {HOT_STREAK_MSG_THRESHOLD}-win hot streak!'


def big_win_msg(username: str, wins_delta: int, mode: str) -> str:
    return f'💰 {username} won {format_wins(wins_delta)} wins in {mode} mode!'


def new_player_msg(username: str) -> str:
    return f'🎉 {username} spun the wheel for the first time! Welcome to the Tides!'


def tide_turned_msg(ended_label: str, podium: list, next_label: str) -> str:
    # ponytail: three 32-char names push this past chat.MAX_MSG_LEN (150) and the tail gets cut.
    medals = ' · '.join(f'{m} {name}' for m, name in zip(('🥇', '🥈', '🥉'), podium))
    middle = f' {medals} —' if medals else ' —'
    return f'🌊 Tide {ended_label} has turned!{middle} Tide {next_label} starts now. Good luck!'


def goal_milestone_msg(pct: int, current: int, target: int) -> str:
    return f'Community goal at {pct}%: {current} / {target}'
