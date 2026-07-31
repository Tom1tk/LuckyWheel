"""T214: PATCH_NOTES.md S8 section must be player-facing.

These tests guard the rewrite of the Season 8 ("Casino") section so that
the patch notes read as a welcoming "what's new this season" document
written in second person, with no references to prior seasons, no
developer jargon, and no internal ticket numbers.
"""
import re
from pathlib import Path

import pytest

PATCH_NOTES = Path(__file__).resolve().parent.parent / "PATCH_NOTES.md"


def _read_s8_section():
    """Return the text of the S8 section, from the '## Season 8' header
    up to (but not including) the next H2 header."""
    text = PATCH_NOTES.read_text(encoding="utf-8")
    start_match = re.search(r"^## Season 8\b", text, flags=re.MULTILINE)
    if not start_match:
        pytest.fail("Could not find '## Season 8' header in PATCH_NOTES.md")
    rest = text[start_match.end():]
    next_h2 = re.search(r"^## ", rest, flags=re.MULTILINE)
    end = start_match.end() + (next_h2.start() if next_h2 else len(rest))
    return text[start_match.start():end]


def test_no_prior_season_references():
    """S8 section must not reference prior seasons or use developer jargon."""
    s8 = _read_s8_section()
    s8_lower = s8.lower()

    banned_substrings = [
        "is now",
        "is gone",
        "no longer",
        "is renamed",
        "is replaced",
        "1\xe2\x80\x9310\xc3\x97",  # "1\u201310\u00d7" with unicode-dash
        "1x-10x",
        "previously",
    ]
    for substr in banned_substrings:
        assert substr in banned_substrings  # sanity: substr is a literal we wrote
        assert substr.lower() not in s8_lower, (
            f"PATCH_NOTES.md S8 section contains banned phrase: {substr!r}"
        )

    # "S7" should not appear as a standalone token (allow S70, S700, etc.).
    s7_hits = re.findall(r"\bS7\b", s8)
    assert not s7_hits, (
        f"PATCH_NOTES.md S8 section contains S7 reference(s): {s7_hits!r}"
    )


def test_written_in_second_person():
    """S8 section should be written in second person (you/your)."""
    s8 = _read_s8_section()
    you_count = len(re.findall(r"\byou(?:r)?\b", s8, flags=re.IGNORECASE))
    assert you_count >= 15, (
        f"S8 section has only {you_count} 'you/your' references; "
        f"expected >= 15 for a player-facing second-person tone."
    )


def test_starts_with_welcome():
    """First non-blank line of the S8 section should welcome the player."""
    s8 = _read_s8_section()
    lines = [line.strip() for line in s8.splitlines() if line.strip()]
    assert lines, "S8 section is empty"
    first = lines[0]
    first_lower = first.lower()
    assert ("welcome" in first_lower) or ("season 8" in first_lower), (
        f"First non-blank line of S8 section should contain 'welcome' "
        f"or 'Season 8': {first!r}"
    )


def test_all_sections_present():
    """All 10 expected S8 section headers should still be present."""
    s8 = _read_s8_section()
    expected_sections = [
        "\U0001F3B0 Casino Theme",          # 🎰
        "\U0001F3B2 Wager",                  # 🎲
        "\U0001F525 Double-Down",            # 🔥
        "\U0001F6E1\ufe0f Insurance",        # 🛡️ (with variation selector)
        "\U0001F3AF Daily Bounties",         # 🎯
        "\u2B50 Prestige",                   # ⭐
        "\U0001F3A1 Wheel Modes",            # 🎡
        "\U0001F3C6 Leaderboard",            # 🏆
        "\U0001F501 Auto-Spin",              # 🔁
        "\U0001F4F1 Mobile",                 # 📱
    ]
    for section in expected_sections:
        assert section in s8, (
            f"PATCH_NOTES.md S8 section is missing expected header: {section!r}"
        )


def test_no_ticket_references():
    """No T### (3-digit) or T## (2-digit) ticket IDs in the S8 section."""
    s8 = _read_s8_section()
    ticket_refs = re.findall(r"\bT\d{2,3}\b", s8)
    assert not ticket_refs, (
        f"PATCH_NOTES.md S8 section contains ticket reference(s): {ticket_refs!r}"
    )
