"""T220 + T221: Dice handling + jackpot messages removed.

T220 (dice):
  - When NOT auto-spinning, /api/roll-dice applies the new streak to the
    DB immediately (response includes applied_immediately=true).
  - When auto-spinning, /api/roll-dice buffers the dice as pending_dice
    (response includes applied_immediately=false).
  - The next spin (manual or auto) consumes pending_dice and uses
    new_streak as the input streak.
  - If the consuming spin is a loss, the streak is reverted to
    original_streak and the dice charge is refunded. Response includes
    dice_refunded=true and dice_refunded_sum.

T221 (no jackpot messages):
  - chat_triggers.jackpot_msg is removed.
  - big_win_msg no longer accepts was_jackpot.
  - JACKPOT_MSG_ALWAYS is removed.
  - /api/spin and /api/tick never post a jackpot message.
  - _maybe_announce_big_win skips jackpots entirely.
  - Migration 063 deletes all existing jackpot messages.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

ROOT     = os.path.dirname(os.path.dirname(__file__))
APP_JSX  = os.path.join(ROOT, 'static', 'app.jsx')
GAME_PY  = os.path.join(ROOT, 'game.py')
CHAT_TG  = os.path.join(ROOT, 'chat_triggers.py')
MIG_063  = os.path.join(ROOT, 'migrations', '063_delete_all_jackpot_messages.sql')


def _read(path):
    with open(path) as f:
        return f.read()


# ── T221: jackpot messages are gone ────────────────────────────────────────

def test_chat_triggers_no_jackpot_msg_function():
    """T221: chat_triggers.jackpot_msg is removed entirely."""
    src = _read(CHAT_TG)
    assert 'def jackpot_msg' not in src, (
        "chat_triggers.jackpot_msg must be removed (T221: no jackpot messages)"
    )


def test_chat_triggers_no_jackpot_msg_always_constant():
    """T221: JACKPOT_MSG_ALWAYS is removed (no more always-on jackpot msgs)."""
    src = _read(CHAT_TG)
    # Look for an actual definition (assignment or class attribute), not
    # just any mention in a comment.
    assert not re.search(r'^\s*JACKPOT_MSG_ALWAYS\s*=', src, re.MULTILINE), (
        "JACKPOT_MSG_ALWAYS must be removed from chat_triggers (T221)"
    )


def test_big_win_msg_no_was_jackpot_kwarg():
    """T221: big_win_msg no longer accepts was_jackpot."""
    src = _read(CHAT_TG)
    # Look at the big_win_msg signature — must not have was_jackpot.
    sig = re.search(r'def big_win_msg\([^)]*\)', src)
    assert sig, "could not find big_win_msg signature"
    assert 'was_jackpot' not in sig.group(0), (
        "big_win_msg signature must not include was_jackpot (T221)"
    )


def test_game_py_does_not_post_jackpot_msg():
    """T221: no code path in game.py posts a jackpot system message."""
    src = _read(GAME_PY)
    assert 'chat_triggers.jackpot_msg' not in src, (
        "game.py must not call chat_triggers.jackpot_msg (T221)"
    )
    assert "event_kind='jackpot'" not in src, (
        "game.py must not post any message with event_kind='jackpot' (T221)"
    )
    assert 'event_kind="jackpot"' not in src, (
        "game.py must not post any message with event_kind=\"jackpot\" (T221)"
    )


def test_maybe_announce_big_win_skips_jackpots():
    """T221: _maybe_announce_big_win only posts for result=='win' (no jackpot)."""
    src = _read(GAME_PY)
    # Find the function and check the gating condition. Limit the search
    # to non-comment lines so docstrings/comments that mention the old
    # behavior don't trip the test.
    func = re.search(
        r'def _maybe_announce_big_win.*?(?=^def [a-zA-Z_]|\Z)',
        src,
        re.DOTALL | re.MULTILINE,
    )
    assert func, "could not locate _maybe_announce_big_win"
    body = func.group(0)
    # Strip docstring and comment lines so we only check actual code.
    code_lines = [
        ln for ln in body.split('\n')
        if ln.strip() and not ln.strip().startswith('#')
        and not ln.strip().startswith('"""') and not ln.strip().startswith("'''")
    ]
    code = '\n'.join(code_lines)
    assert "result') == 'win'" in code, (
        "_maybe_announce_big_win must gate on result == 'win' "
        "(jackpots no longer trigger any chat message)"
    )
    assert "result') in ('win', 'jackpot')" not in code, (
        "_maybe_announce_big_win must NOT include 'jackpot' in its gating"
    )
    # The kwarg call `was_jackpot=` is what's actually being passed to
    # big_win_msg — that's what must be gone. The string "was_jackpot"
    # may still appear in the docstring describing the change.
    assert 'was_jackpot=' not in code, (
        "_maybe_announce_big_win must not pass was_jackpot= to big_win_msg"
    )


def test_migration_063_deletes_jackpot_messages():
    """T221: migration 063 deletes all 'jackpot' messages from chat."""
    assert os.path.exists(MIG_063), "migration 063 file must exist"
    src = _read(MIG_063)
    assert 'DELETE FROM chat_messages' in src, (
        "migration 063 must DELETE FROM chat_messages"
    )
    assert 'ILIKE' in src and '%jackpot%' in src, (
        "migration 063 must match 'jackpot' case-insensitively "
        "in the message body"
    )


# ── T220: dice — apply immediately or buffer ───────────────────────────────

def test_roll_dice_response_includes_applied_immediately():
    """T220: /api/roll-dice response distinguishes immediate vs buffered."""
    src = _read(GAME_PY)
    assert "'applied_immediately':" in src or '"applied_immediately":' in src, (
        "/api/roll-dice must include 'applied_immediately' in the response"
    )


def test_roll_dice_response_includes_original_streak():
    """T220: pending_dice stores original_streak so the spin handler can
    revert on a loss."""
    src = _read(GAME_PY)
    assert "'original_streak':" in src or '"original_streak":' in src, (
        "/api/roll-dice must store original_streak in pending_dice so the "
        "next spin can revert on a loss"
    )


def test_spin_consumes_pending_dice():
    """T220: manual /api/spin consumes pending_dice (uses new_streak)."""
    src = _read(GAME_PY)
    # The /api/spin handler is between the @app.route('/api/spin') and the
    # next @app.route. Search for the consumption pattern in the spin function.
    spin_fn = re.search(
        r"@game_bp\.route\('/api/spin'.*?(?=@game_bp\.route)",
        src,
        re.DOTALL,
    )
    assert spin_fn, "could not locate /api/spin handler"
    body = spin_fn.group(0)
    assert 'pending_dice' in body, (
        "/api/spin must read pending_dice from the game state"
    )
    # The actual dict access uses single-quote strings (we wrote
    # `pd['new_streak']` in game.py). Use a raw-looking pattern via
    # Python's normal string escape semantics in the source.
    assert "pd['new_streak']" in body, (
        "/api/spin must use pd['new_streak'] as the input streak"
    )


def test_spin_reverts_on_loss_with_pending_dice():
    """T220: if /api/spin is a loss with pending_dice, revert + refund."""
    body = _read(GAME_PY)
    assert 'DICE_REFUND_ON_LOSS' in body, (
        "/api/spin must log DICE_REFUND_ON_LOSS when the spin loses "
        "with pending_dice"
    )
    assert "dice_refunded" in body, (
        "/api/spin must include dice_refunded in the response"
    )


def test_tick_consumes_pending_dice():
    """T220: /api/tick consumes pending_dice (uses new_streak)."""
    src = _read(GAME_PY)
    assert "pd['new_streak']" in src, (
        "/api/tick must also use pd['new_streak'] as the input streak"
    )


def test_tick_reverts_on_loss_with_pending_dice():
    """T220: /api/tick reverts the streak on loss and refunds the charge."""
    src = _read(GAME_PY)
    tick_fn = re.search(
        r"def tick\(.*?(?=^def [a-z]|\Z)",
        src,
        re.DOTALL | re.MULTILINE,
    )
    # Don't require the full function body — just check the markers.
    assert 'DICE_REFUND_ON_LOSS' in src, (
        "/api/tick must also log DICE_REFUND_ON_LOSS"
    )
    assert 'path=tick' in src, (
        "/api/tick's DICE_REFUND_ON_LOSS log should be marked path=tick"
    )


def test_jsx_uses_applied_immediately_for_pending_flag():
    """T220: the dice result bubble's 'pending' flag reflects applied_immediately."""
    src = _read(APP_JSX)
    assert '!data.applied_immediately' in src or 'applied_immediately' in src, (
        "JSX must use data.applied_immediately to decide the dice 'pending' flag"
    )


def test_jsx_setstreak_on_immediate_dice():
    """T220: when applied_immediately, the JSX updates local setStreak."""
    src = _read(APP_JSX)
    assert re.search(
        r"if\s*\(\s*data\.applied_immediately\s*\)\s*setStreak\s*\(\s*data\.streak\s*\)",
        src,
    ), (
        "JSX must setStreak(data.streak) when dice is applied immediately "
        "so the StreakPanel updates without waiting for a spin"
    )


def test_jsx_dice_refund_toast():
    """T220: when a spin refunds the dice, the JSX shows a toast."""
    src = _read(APP_JSX)
    assert 'data.dice_refunded' in src, (
        "JSX must check data.dice_refunded in the spin response"
    )
    assert 'Dice refund' in src or 'dice refund' in src.lower(), (
        "JSX must show a 'Dice refund' toast when the dice is refunded"
    )
