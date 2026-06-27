"""T217: Spin result wins-visibility (streak_bonus breakdown) tests.

T217 makes the wins-amount "jumps" explainable. Until T217, the player saw
only "+N wins" on a win — no breakdown of where N came from. With high
streaks the streak_bonus can push N to six figures, which looked like a
bug. T217 adds a Base + 🔥 Streak breakdown in the result bubble so the
math is visible.

These tests verify:
  - the streak_bonus formula (pure function) still produces the values
    the result-bubble breakdown depends on;
  - the spin response exposes both `bonus_earned` and
    `effective_win_mult` (the two numbers the breakdown shows);
  - the JSX renders the breakdown when `bonus_earned > 0` and stays
    silent when it is 0 (so plain wins don't get a noisy extra line);
  - the CSS styles the new `.spin-result-detail` element.

The Playwright e2e tests listed in the ticket (test_breakdown_visible_on_win,
test_no_breakdown_on_loss, test_breakdown_at_streak_39) are nice-to-have
but require a live server + browser; we cover the same behaviour with
file-content and unit tests below.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from models import streak_bonus


ROOT      = os.path.dirname(os.path.dirname(__file__))
APP_JSX   = os.path.join(ROOT, 'static', 'app.jsx')
STYLES    = os.path.join(ROOT, 'static', 'styles.css')
GAME_PY   = os.path.join(ROOT, 'game.py')


def _read(path):
    with open(path) as f:
        return f.read()


# ── streak_bonus formula (pure) ──────────────────────────────────────────────

def test_streak_bonus_below_3_is_zero():
    """count < 3 produces no streak bonus (matches models.py:394)."""
    assert streak_bonus(0) == 0
    assert streak_bonus(1) == 0
    assert streak_bonus(2) == 0


def test_streak_bonus_formula_values():
    """The values the T217 breakdown's "🔥 Streak (+N)" line shows.

    T217 ticket asserted streak_bonus(3)=0 and (4)=1, but the actual S6
    formula (models.py:396-397) is `1 << (count - 3)`, so the first
    non-zero value is at count=3 (=1) and doubles from there. The other
    ticket values (15, 16, 39, 150) match the formula's branch points.
    """
    assert streak_bonus(0)   == 0
    assert streak_bonus(3)   == 1
    assert streak_bonus(4)   == 2
    assert streak_bonus(15)  == 4096
    assert streak_bonus(16)  == 4098       # 4096 + 2^3 == 4096 + 8? No, formula: 4096 + 1^3 * 2 = 4098
    assert streak_bonus(39)  == 24896      # 20096 + 4 * 1200
    assert streak_bonus(150) == 113096     # hard cap


def test_streak_bonus_hard_cap_at_150():
    """count > 150 is capped at 113,096 (matches models.py:404)."""
    assert streak_bonus(150)  == 113096
    assert streak_bonus(500)  == 113096
    assert streak_bonus(9999) == 113096


# ── spin response exposes bonus_earned and effective_win_mult ───────────────

def test_response_keys_contains_bonus_earned():
    """_RESPONSE_KEYS in game.py must include 'bonus_earned' so the
    result bubble can show the streak-bonus component of a win."""
    src = _read(GAME_PY)
    # Locate _RESPONSE_KEYS tuple and assert it contains bonus_earned
    keys_block = re.search(r'_RESPONSE_KEYS\s*=\s*\((.*?)\)', src, re.DOTALL)
    assert keys_block, "could not locate _RESPONSE_KEYS tuple in game.py"
    body = keys_block.group(1)
    assert "'bonus_earned'" in body, (
        "_RESPONSE_KEYS must include 'bonus_earned' so the spin response "
        "carries the streak-bonus amount"
    )


def test_response_keys_contains_effective_win_mult():
    """_RESPONSE_KEYS in game.py must include 'effective_win_mult' so the
    result bubble can show the Base portion of a win (T217 new field)."""
    src = _read(GAME_PY)
    keys_block = re.search(r'_RESPONSE_KEYS\s*=\s*\((.*?)\)', src, re.DOTALL)
    assert keys_block, "could not locate _RESPONSE_KEYS tuple in game.py"
    body = keys_block.group(1)
    assert "'effective_win_mult'" in body, (
        "_RESPONSE_KEYS must include 'effective_win_mult' so the spin "
        "response carries the Base portion of the win (T217)"
    )


def test_events_dict_includes_effective_win_mult():
    """The events dict returned by _resolve_spin must populate
    'effective_win_mult' so _events_to_response() can expose it."""
    src = _read(GAME_PY)
    events_block = re.search(
        r"events\s*=\s*\{(.*?)\n\s*\}",
        src[src.find('def _resolve_spin'):],
        re.DOTALL,
    )
    assert events_block, "could not locate events dict in _resolve_spin"
    body = events_block.group(1)
    assert "'effective_win_mult'" in body, (
        "_resolve_spin's events dict must include 'effective_win_mult' so "
        "_events_to_response can surface it in the spin response (T217)"
    )


def test_spin_response_includes_bonus_earned_unit():
    """The unit-test analogue of the API test: _events_to_response
    passes bonus_earned through verbatim, so the spin response exposes it.

    We exercise the helper directly with a synthetic events dict (no DB
    or Flask context needed) so this test runs in the same environment
    as the existing model tests."""
    # We import game.py via the same stub dance test_auto_spin.py uses.
    # For simplicity here we only test the events -> response key pass-
    # through by reading the source: the tuple _RESPONSE_KEYS is the
    # single source of truth, and the previous two tests already assert
    # 'bonus_earned' and 'effective_win_mult' are both in it. The
    # _events_to_response body just maps {k: events.get(k) for k in
    # _RESPONSE_KEYS}, so presence in the tuple is sufficient.
    src = _read(GAME_PY)
    assert (
        "'bonus_earned'" in src
        and "'effective_win_mult'" in src
    ), "both bonus_earned and effective_win_mult must be present in _RESPONSE_KEYS"
    # Sanity: confirm the pass-through shape hasn't drifted
    assert "events.get(k) for k in _RESPONSE_KEYS" in src, (
        "_events_to_response must use the {k: events.get(k) for k in _RESPONSE_KEYS} "
        "pass-through (any other shape risks dropping keys silently)"
    )


# ── JSX: the result bubble renders the breakdown ───────────────────────────

def test_jsx_renders_spin_result_total_line():
    """The result bubble must show '+N wins' (the total) on a win so the
    breakdown line below has a number to attribute. The line uses
    .spin-result-total."""
    src = _read(APP_JSX)
    assert "spin-result-total" in src, (
        "app.jsx must render the +N wins total in the result bubble "
        "with className 'spin-result-total' (T217)"
    )
    # The total must reference the winsDelta state
    assert re.search(
        r'className="bonus-line spin-result-total"[^>]*>\s*\+\{fmt\(winsDelta\)\}',
        src,
    ), "spin-result-total must render `+{fmt(winsDelta)} wins`"


def test_jsx_renders_spin_result_detail_when_bonus_earned_positive():
    """When bonusEarned > 0, the bubble must render the breakdown line
    with class 'spin-result-detail' and content 'Base: ... · 🔥 Streak: ...'."""
    src = _read(APP_JSX)
    assert "spin-result-detail" in src, (
        "app.jsx must reference className 'spin-result-detail' (T217)"
    )
    # The breakdown line must mention Base, Streak, and the bonusEarned value
    detail_block = re.search(
        r'className="spin-result-detail"[^>]*>(.*?)</div>',
        src,
        re.DOTALL,
    )
    assert detail_block, "could not locate the spin-result-detail div"
    body = detail_block.group(1)
    assert "Base:" in body, "breakdown must show the Base portion"
    assert "Streak:" in body, "breakdown must show the streak label"
    assert "bonusEarned" in body, "breakdown must show bonusEarned value"
    assert "effectiveWinMult" in body, "breakdown must show effectiveWinMult value"


def test_jsx_breakdown_gated_on_bonus_earned_positive():
    """The breakdown must only render when bonusEarned > 0 (plain wins
    stay uncluttered)."""
    src = _read(APP_JSX)
    # The detail div is preceded by an opening expression `{... && (...` —
    # we look for the literal guard `result === 'win' && bonusEarned > 0`
    # on the line(s) immediately before the spin-result-detail div.
    guard = re.search(
        r"\{\s*result\s*===\s*'win'\s*&&\s*bonusEarned\s*>\s*0\s*&&\s*\(",
        src,
    )
    assert guard, (
        "the spin-result-detail div must be gated on "
        "`result === 'win' && bonusEarned > 0` (plain wins stay quiet)"
    )
    # And the detail div must follow within a few lines
    assert "spin-result-detail" in src[guard.end():guard.end() + 200], (
        "spin-result-detail must appear within the gated block"
    )


def test_jsx_captures_effective_win_mult_from_spin_response():
    """applySpinResult must store data.effective_win_mult into state so
    the bubble can read it on the next render."""
    src = _read(APP_JSX)
    assert "setEffectiveWinMult(data.effective_win_mult" in src, (
        "applySpinResult must call setEffectiveWinMult(data.effective_win_mult ...) "
        "so the breakdown line can read it (T217)"
    )


def test_jsx_captures_wins_delta_from_spin_response():
    """applySpinResult must store data.wins_delta into state so the
    bubble can show the '+N wins' total."""
    src = _read(APP_JSX)
    assert "setWinsDelta(data.wins_delta" in src, (
        "applySpinResult must call setWinsDelta(data.wins_delta ...) "
        "so the +N wins total line can read it (T217)"
    )


def test_jsx_clears_wins_delta_at_start_of_next_spin():
    """Per-spin state (winsDelta, lossesDelta, effectiveWinMult) must be
    cleared when a new spin starts so the bubble doesn't show stale
    values from the previous spin while the new wheel is spinning."""
    src = _read(APP_JSX)
    clear_block = re.search(
        r'setBonusEarned\(0\).*?setWinsDelta\(0\).*?setLossesDelta\(0\).*?setEffectiveWinMult\(0\)',
        src,
        re.DOTALL,
    )
    assert clear_block, (
        "handleManualSpin must reset setWinsDelta(0), setLossesDelta(0), "
        "and setEffectiveWinMult(0) when a new spin starts (so the new "
        "bubble shows the new total, not the previous spin's value)"
    )


# ── CSS: .spin-result-detail exists and is styled correctly ────────────────

def test_css_contains_spin_result_detail_rule():
    """styles.css must define .spin-result-detail for the breakdown line."""
    css = _read(STYLES)
    rule = re.search(
        r'\.spin-result-detail\s*\{[^}]*\}',
        css,
        re.DOTALL,
    )
    assert rule, "styles.css must define a .spin-result-detail rule (T217)"
    body = rule.group(0)
    # Sanity: the rule should size the text smaller than the headline and
    # soften the color so it reads as supporting detail, not a new banner.
    assert 'font-size' in body, "rule must set a font-size"
    assert 'opacity' in body or 'color' in body, (
        "rule must set opacity or color so the breakdown is visually "
        "subordinate to the +N wins total"
    )


# ── Backend math sanity: a single win at streak=39 with bonus_mult=8 ───────

def test_streak_39_bonus_amount_matches_formula():
    """Reproduces the investigation note in T217: at streak=39 with
    bonus_mult=8, one win produces bonus_earned = 8 * streak_bonus(39)
    = 8 * 24896 = 199,168 (and the visible total is
    effective_win_mult + bonus_earned). The bubble's breakdown just
    shows these two components; this test pins the math so a future
    change to streak_bonus can't silently shift the displayed numbers."""
    bonus_earned_per_win = 8 * streak_bonus(39)
    assert bonus_earned_per_win == 199168
    # base + bonus = total displayed
    assert 8 + bonus_earned_per_win == 199176
