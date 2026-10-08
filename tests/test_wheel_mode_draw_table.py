"""The client's WHEEL_MODE_DRAW fallback must cover every server wheel mode.

A missing row (long_shot, S9 playtest) made the wheel keep Steady's segments.
"""
import re
from pathlib import Path

from wheel_modes import WHEEL_MODES

JSX = (Path(__file__).resolve().parent.parent / 'static' / 'app.jsx').read_text()


def test_draw_table_matches_server_modes():
    block = re.search(r'const WHEEL_MODE_DRAW = \{(.*?)\n\};', JSX, re.S).group(1)
    rows = {m: tuple(map(int, v)) for m, *v in
            re.findall(r'(\w+):\s*\{ win_pct: (\d+), lose_pct: (\d+), jackpot_pct: (\d+) \}', block)}
    expected = {m: (c['win_pct'], c['loss_pct'], c['jackpot_pct']) for m, c in WHEEL_MODES.items()}
    assert rows == expected
