"""Property test: Output Format Equivalence for board/list tools.

# Feature: fastmcp-migration, Property 2: Output Format Equivalence

Validates: Requirements 4.1

For `list_boards`, `get_board`, `create_card`, `update_card`, generate random
valid mocked API responses using hypothesis and verify the new tool function
returns the same formatted string as the old dispatcher would have.
"""
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock

# Ensure TRELLO_API_KEY is set before importing server
if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

import server

# ---------------------------------------------------------------------------
# Hypothesis strategies for generating Trello-like data
# ---------------------------------------------------------------------------

# Trello IDs: 24-char hex strings
trello_id_st = st.text(
    alphabet="0123456789abcdef",
    min_size=24,
    max_size=24,
)

# Board/card names: non-empty text (printable, no null bytes)
name_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"), blacklist_characters="\x00"),
    min_size=1,
    max_size=100,
)

# URLs starting with https://
url_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="\x00"),
    min_size=1,
    max_size=80,
).map(lambda s: f"https://{s}")

# Optional description text (can be empty string or non-empty)
desc_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"), blacklist_characters="\x00"),
    min_size=0,
    max_size=200,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_async(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Property tests: Output Format Equivalence
# ---------------------------------------------------------------------------

@settings(max_examples=100, deadline=None)
@given(
    boards=st.lists(
        st.fixed_dictionaries({
            "name": name_st,
            "id": trello_id_st,
        }),
        min_size=0,
        max_size=10,
    )
)
def test_list_boards_output_equivalence(boards):
    """**Validates: Requirements 4.1**

    For any list of board dicts returned by the Trello API, the new
    list_boards() tool function should produce the same formatted string
    as the old call_tool() dispatcher.
    """
    # Expected output from old dispatcher logic
    result = "\n".join([f"- {board['name']} (ID: {board['id']})" for board in boards])
    expected = f"Your Trello Boards:\n{result}"

    with patch.object(server, "make_trello_request", return_value=boards):
        actual = run_async(server.list_boards())

    assert actual == expected, (
        f"list_boards output mismatch:\n"
        f"  expected: {expected!r}\n"
        f"  actual:   {actual!r}"
    )


@settings(max_examples=100, deadline=None)
@given(
    board=st.fixed_dictionaries({
        "name": name_st,
        "id": trello_id_st,
        "url": url_st,
    }, optional={"desc": desc_st}),
)
def test_get_board_output_equivalence(board):
    """**Validates: Requirements 4.1**

    For any board dict returned by the Trello API, the new get_board()
    tool function should produce the same formatted string as the old
    call_tool() dispatcher.
    """
    expected = (
        f"Board: {board['name']}\n"
        f"ID: {board['id']}\n"
        f"URL: {board['url']}\n"
        f"Description: {board.get('desc', 'N/A')}"
    )

    with patch.object(server, "make_trello_request", return_value=board):
        actual = run_async(server.get_board(board_id="abc123def456abc123def456"))

    assert actual == expected, (
        f"get_board output mismatch:\n"
        f"  expected: {expected!r}\n"
        f"  actual:   {actual!r}"
    )


@settings(max_examples=100, deadline=None)
@given(
    card=st.fixed_dictionaries({
        "name": name_st,
        "id": trello_id_st,
        "url": url_st,
    }),
)
def test_create_card_output_equivalence(card):
    """**Validates: Requirements 4.1**

    For any card dict returned by the Trello API after creation, the new
    create_card() tool function should produce the same formatted string
    as the old call_tool() dispatcher.
    """
    expected = (
        f"Created card: {card['name']}\n"
        f"ID: {card['id']}\n"
        f"URL: {card['url']}"
    )

    with patch.object(server, "make_trello_request", return_value=card):
        actual = run_async(server.create_card(
            list_id="abc123def456abc123def456",
            name="Test Card",
        ))

    assert actual == expected, (
        f"create_card output mismatch:\n"
        f"  expected: {expected!r}\n"
        f"  actual:   {actual!r}"
    )


@settings(max_examples=100, deadline=None)
@given(
    card=st.fixed_dictionaries({
        "name": name_st,
        "id": trello_id_st,
        "url": url_st,
    }),
)
def test_update_card_output_equivalence(card):
    """**Validates: Requirements 4.1**

    For any card dict returned by the Trello API after update, the new
    update_card() tool function should produce the same formatted string
    as the old call_tool() dispatcher.
    """
    expected = (
        f"Updated card: {card['name']}\n"
        f"ID: {card['id']}\n"
        f"URL: {card['url']}"
    )

    with patch.object(server, "make_trello_request", return_value=card):
        actual = run_async(server.update_card(
            card_id="abc123def456abc123def456",
            name="Updated Name",
        ))

    assert actual == expected, (
        f"update_card output mismatch:\n"
        f"  expected: {expected!r}\n"
        f"  actual:   {actual!r}"
    )
