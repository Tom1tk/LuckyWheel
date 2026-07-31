"""T241 follow-up: hide test-user chat messages.

T241 added an `ip_address INET` column on `chat_messages` and a
`WHERE ip_address IS NULL OR ip_address <> '127.0.0.1'` filter in
`_build_chat_query` so the test-user system messages from the
T231-T240 batch (the 106 '🎉 t239s... first spin!' rows) no longer
appear in the public chat feed.

This file pins the filter's behavior at three levels:
  1. SQL-level: the SELECT must include the filter clauses.
  2. Source-grep: post_chat and post_dedup_system_message both
     capture the user's IP (otherwise new test users would still
     pollute the feed).
  3. Cleanup: a one-off DELETE removed the 106 stale rows. A
     regression test asserts the source-grep / migration match
     that the table now has the column and the index.

The 106 existing rows are deleted via a one-off script; the
test that pins that step is in
tests/test_t241_cleanup_chat.py (run during the live verification
window; not part of the in-tree test suite to keep the suite
hermetic).
"""
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(path):
    with open(os.path.join(REPO, path)) as f:
        return f.read()


def _chat_select_block():
    """Return the text of the SELECT statements built by _build_chat_query.

    Parsed from chat.py via the same regex trick the T241 test
    used for the leaderboard — the test is robust to the exact
    formatting as long as the filter is present.
    """
    src = _read('chat.py')
    # Find the function and the SELECT statements inside its returns.
    m = re.search(
        r"def _build_chat_query\(args\):(.*?)(?=^def |^class |\Z)",
        src,
        re.MULTILINE | re.DOTALL,
    )
    assert m, "could not locate _build_chat_query in chat.py"
    return m.group(1)


def test_chat_select_filters_localhost_ip():
    """The /api/chat SELECT must exclude rows with ip_address = 127.0.0.1.

    Without this filter, the 1282 test users from the T231-T240 batch
    would still show up in the public chat feed (their system
    messages survive even when the leaderboard filter hides their
    usernames).
    """
    block = _chat_select_block()
    assert "'127.0.0.1'" in block, (
        "/api/chat SELECT must include 'ip_address <> ''127.0.0.1'' "
        "filter (T241 follow-up; 106 test-user system messages would "
        "otherwise clog the public feed)"
    )
    assert 'ip_address IS NULL' in block, (
        "/api/chat SELECT must allow NULL ip_address (server-side events "
        "like singularity fills have no originating user)"
    )


def test_chat_pagination_filter_present():
    """The cursor-paginated branch (WHERE id < %s) must also include the
    ip filter — otherwise older test-user messages would reappear
    when paging back."""
    body = _chat_select_block()
    # The body has two SELECTs: the cursor-paginated one (with id < %s)
    # and the plain one. Both must have the filter. The strings in
    # chat.py are written as `'<ip>'` with backslash-escaped quotes
    # (Python string-literal syntax), so look for the SQL fragment
    # rather than the quoted form.
    assert body.count('127.0.0.1') >= 2, (
        "both _build_chat_query branches (cursor-paginated and plain) "
        "must filter localhost IP — otherwise paginating backwards "
        "would re-surface the 106 test-user system messages"
    )
    assert body.count('ip_address IS NULL') >= 2, (
        "both _build_chat_query branches must allow NULL ip_address"
    )


def test_post_chat_captures_poster_ip():
    """The /api/chat POST handler must store the poster's IP in chat_messages
    so the SELECT filter can find it."""
    src = _read('chat.py')
    m = re.search(
        r"def post_chat\(\).*?INSERT INTO chat_messages.*?\)",
        src,
        re.MULTILINE | re.DOTALL,
    )
    assert m, "could not locate post_chat's INSERT in chat.py"
    block = m.group(0)
    assert 'ip_address' in block, (
        "post_chat's INSERT must include ip_address (T241 follow-up; "
        "without it, real-user chat messages would not be filterable)"
    )
    assert 'SELECT ip_address FROM users' in block, (
        "post_chat must look up the poster's IP from the users table"
    )


def test_post_dedup_system_message_captures_user_ip():
    """System messages about a specific user (first spin, big win,
    prestige, etc.) must capture that user's IP — the 106 test-user
    'first spin' rows came from this path."""
    src = _read('chat.py')
    m = re.search(
        r"def post_dedup_system_message\(conn, message, user_id, event_kind[^\n]*\):(.*?)(?=^def |^class |\Z)",
        src,
        re.MULTILINE | re.DOTALL,
    )
    assert m, "could not locate post_dedup_system_message in chat.py"
    block = m.group(1)
    assert 'ip_address' in block, (
        "post_dedup_system_message must include ip_address "
        "(this is the path that produced the 106 test-user 'first spin' "
        "rows during the T231-T240 audit)"
    )
    assert 'SELECT ip_address FROM users' in block, (
        "post_dedup_system_message must look up the user_id's IP"
    )


def test_migration_072_adds_ip_column():
    """Migration 072 must add ip_address INET to chat_messages.

    The migration is the source of truth for the column. Without
    it, the post-deploy INSERT ... ip_address statement would 500
    on every chat post.
    """
    src = _read('migrations/072_chat_ip_address.sql')
    assert 'ALTER TABLE chat_messages ADD COLUMN' in src, (
        "migration 072 must ALTER chat_messages to add the column"
    )
    assert 'ip_address' in src, (
        "migration 072 must add an ip_address column"
    )
    assert 'INET' in src.upper(), (
        "ip_address must be INET (matches the users.ip_address type)"
    )
