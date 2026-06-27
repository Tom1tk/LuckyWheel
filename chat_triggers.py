"""Auto-post system message triggers for Season 8.

Centralizes code-level constants for which events should post a chat message
and the message templates. Used by game.py endpoints to call
post_system_message() with the right event_kind and message text.
"""

# ── Trigger thresholds ───────────────────────────────────────────────────────
JACKPOT_MSG_ALWAYS = True
DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE = 5
HOT_STREAK_MSG_THRESHOLD = 10
BIG_WIN_THRESHOLD = 5000


# ── Message formatters ───────────────────────────────────────────────────────
def jackpot_msg(username: str, mode: str, stake: int, wins_delta: int) -> str:
    return f'🎰 {username} hit a JACKPOT in {mode} mode at {stake}x stake for {wins_delta} wins!'


def double_down_win_msg(username: str, effective_stake: int, wins_delta: int) -> str:
    return f'🔥 {username} won a {effective_stake}x double-down for {wins_delta} wins!'


def hot_streak_msg(username: str) -> str:
    return f'🔥 {username} reached a {HOT_STREAK_MSG_THRESHOLD}-win hot streak!'


def big_win_msg(username: str, wins_delta: int, mode: str, *, was_jackpot: bool = False) -> str:
    if was_jackpot:
        return f'🎰 {username} hit a {wins_delta} jackpot in {mode} mode!'
    return f'💰 {username} won {wins_delta} wins in {mode} mode!'


def prestige_msg(username: str, level: int) -> str:
    return f'⭐ {username} reached Prestige Level {level}!'


def new_player_msg(username: str) -> str:
    return f'🎉 {username} spun the wheel for the first time! Welcome to Season 8!'


def singularity_fill_msg(total: int) -> str:
    return f'🌀 The Singularity has converged! Total contributed: {total}'


def goal_milestone_msg(pct: int, current: int, target: int) -> str:
    return f'Community goal at {pct}%: {current} / {target}'
