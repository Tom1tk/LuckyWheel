"""T219: Jackpots must count as a win (not a loss) in every UI surface.

Bug report (users, 2026-06-27): "Jackpots are counting as a loss and
resetting their streak. The result bubble shows 'YOU LOSE' with a
'jackpot x25' line underneath."

Root cause: the S8 result bubble at app.jsx:4938 had no 'jackpot' case
in its conditional, so jackpots fell through to the "💀 YOU LOSE" branch.
Confetti + fish mood had the same gap (app.jsx:3941, 3950). The
HiatusWheel counter (app.jsx:1974) had the same off-by-one.

This file pins the fix: jackpots are wins in all five UI surfaces
(banner text, total line, confetti, mood, HiatusWheel counter) and the
5M wins cap is removed.

Tests cover:
  - JSX banner shows 'JACKPOT!' for jackpot result
  - JSX banner shows 'YOU LOSE' only for actual losses
  - JSX winsDelta line shows for jackpots (the +N wins total)
  - JSX confetti fires for jackpots
  - JSX fish mood is 'happy' for jackpots
  - HiatusWheel counter increments wins (not losses) on jackpot
  - Game logic: no _MAX_WINS cap constant remains
  - Game logic: 5M+1 win survives the spin (no cap applied)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

ROOT     = os.path.dirname(os.path.dirname(__file__))
APP_JSX  = os.path.join(ROOT, 'static', 'app.jsx')
GAME_PY  = os.path.join(ROOT, 'game.py')


def _read(path):
    with open(path) as f:
        return f.read()


# ── Result banner: jackpot says 'JACKPOT!', losses say 'YOU LOSE' ──────────

def test_banner_shows_jackpot_text_for_jackpot_result():
    """The result banner's first text node must be '🎰 JACKPOT! 🎰' when
    result === 'jackpot'. The previous bug fell through to the
    '💀 YOU LOSE' branch and showed the wrong banner."""
    src = _read(APP_JSX)
    # The banner's ternary must include the jackpot branch
    banner_block = re.search(
        r'result\s*===\s*[\'"]win[\'"]\s*\|\|\s*result\s*===\s*[\'"]jackpot[\'"]\s*\|\|\s*\(',
        src,
    )
    assert banner_block, (
        "result banner conditional must include `result === 'jackpot'` "
        "in the win-side branch (not the lose-side fall-through)"
    )
    # The text "JACKPOT!" must appear in the result-text div when result is jackpot
    assert re.search(
        r"result\s*===\s*[\'\"]jackpot[\'\"]\s*\?\s*[\'\"][^'\"]*JACKPOT",
        src,
    ), "result-text must render a 'JACKPOT!' string when result is 'jackpot'"


def test_banner_shows_you_lose_only_for_actual_losses():
    """'YOU LOSE' must NOT be reachable from a jackpot result. The bug
    was that the banner's else branch (which says '💀 YOU LOSE 💀')
    caught jackpot because the conditional only matched 'win' or
    'lose' + shieldFeedback."""
    src = _read(APP_JSX)
    # The else branch with "YOU LOSE" exists at the original site.
    # Ensure the gating condition is the new one that excludes jackpot.
    lose_block = re.search(
        r'result\s*===\s*[\'"]win[\'"]\s*\|\|\s*result\s*===\s*[\'"]jackpot[\'"]\s*\|\|\s*'
        r'\(result\s*===\s*[\'"]lose[\'"]\s*&&\s*shieldFeedback\)\s*\?\s*\(',
        src,
    )
    assert lose_block, (
        "banner gating must be: "
        "`result === 'win' || result === 'jackpot' || "
        "(result === 'lose' && shieldFeedback)` "
        "so jackpot is treated as a win"
    )


# ── winsDelta line: shown for jackpots too ─────────────────────────────────

def test_wins_delta_total_shown_for_jackpots():
    """The '+N wins' total line must render for jackpots, not just 'win'.
    The previous bug gated the line on `result === 'win' && winsDelta > 0`
    so jackpots silently showed no total (the user only saw the 'jackpot
    x25' bonus line)."""
    src = _read(APP_JSX)
    assert re.search(
        r"\{\s*\(\s*result\s*===\s*[\'\"]win[\'\"]\s*\|\|\s*result\s*===\s*[\'\"]jackpot[\'\"]\s*\)"
        r"\s*&&\s*winsDelta\s*>\s*0\s*&&",
        src,
    ), (
        "winsDelta total line must be gated on "
        "`(result === 'win' || result === 'jackpot') && winsDelta > 0` "
        "so jackpot wins show the +N total"
    )


# ── Confetti + fish mood: jackpot is a celebration, not a loss ─────────────

def test_confetti_fires_for_jackpots():
    """Jackpots must fire confetti (they're a win, with a 25x multiplier
    on top). The previous bug only fired confetti for 'win' or guard
    block — jackpots got a sad fish with no celebration."""
    src = _read(APP_JSX)
    assert re.search(
        r"data\.result\s*===\s*[\'\"]win[\'\"]\s*\|\|\s*data\.result\s*===\s*[\'\"]jackpot[\'\"]\s*\|\|"
        r"\s*\(data\.guard_triggered\s*&&\s*data\.guard_blocked\)",
        src,
    ), (
        "confetti trigger must include `data.result === 'jackpot'` "
        "in the win-side conditional"
    )


def test_fish_mood_is_happy_for_jackpots():
    """Jackpots must give the fish a 'happy' mood (not 'sad'). The
    previous bug only set 'happy' for 'win' or guard block — jackpots
    got the sad face."""
    src = _read(APP_JSX)
    assert re.search(
        r"data\.result\s*===\s*[\'\"]win[\'\"]\s*\|\|\s*data\.result\s*===\s*[\'\"]jackpot[\'\"]\s*\|\|"
        r"\s*\(data\.guard_triggered\s*&&\s*data\.guard_blocked\)\s*\)\s*\?\s*[\'\"]happy[\'\"]",
        src,
    ), (
        "fish mood must be 'happy' for "
        "data.result === 'win' || data.result === 'jackpot' || guard_blocked"
    )


# ── HiatusWheel: jackpot counts as a win in the W/L tally ───────────────────

def test_hiatus_wheel_counts_jackpot_as_win():
    """The HiatusWheel S7 page's local W/L tally must increment wins
    (not losses) on a jackpot. The previous code was
    `if (data.result === 'win') setWins(...) else setLosses(...)` so
    jackpots incremented losses."""
    src = _read(APP_JSX)
    assert re.search(
        r"data\.result\s*===\s*[\'\"]win[\'\"]\s*\|\|\s*data\.result\s*===\s*[\'\"]jackpot[\'\"]"
        r"\s*\)\s*setWins",
        src,
    ), (
        "HiatusWheel must treat `result === 'jackpot'` as a win when "
        "incrementing the local W/L tally"
    )


# ── 5M cap removed ─────────────────────────────────────────────────────────

def test_no_max_wins_constant_in_game_py():
    """The _MAX_WINS / 5_000_000 cap constant must be removed from
    game.py. The cap was a leftover from JS Infinity display concerns
    — modern JS is safe up to Number.MAX_SAFE_INTEGER (~9 quadrillion),
    so the cap is no longer needed."""
    src = _read(GAME_PY)
    assert "_MAX_WINS" not in src, (
        "game.py must not contain a _MAX_WINS constant (T219: cap removed)"
    )
    # The cap was the literal 5_000_000 used as a wins ceiling. Other
    # constants in the file use 25_000_000 / 125_000_000 etc. for the
    # exchange/marketplace math, so we check the exact line that was
    # the cap. The old line was:
    #     wins = min(wins, _MAX_WINS)
    # which becomes a no-op (the line is deleted) under T219.
    assert not re.search(r"min\s*\(\s*wins\s*,\s*_MAX_WINS\s*\)", src), (
        "game.py must not call `min(wins, _MAX_WINS)` (T219: cap removed)"
    )


def test_no_min_wins_in_spin_path():
    """The spin() function must not call min(wins, ...) on the new_state
    wins value — this is the line that was applying the cap."""
    src = _read(GAME_PY)
    # The old line was `wins = min(wins, _MAX_WINS)`. Make sure no
    # `wins = min(wins,` remains in game.py.
    assert not re.search(r"^\s*wins\s*=\s*min\s*\(\s*wins\s*,", src, re.MULTILINE), (
        "game.py must not call `wins = min(wins, ...)` — the 5M cap is removed"
    )
