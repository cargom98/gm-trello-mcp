"""Property test: Invalid ID Rejection.

# Feature: fastmcp-migration, Property 5: Invalid ID Rejection

**Validates: Requirements 5.8**

For any string that does not match the Trello ID validation pattern (empty,
contains special characters, exceeds 64 characters), passing it as an ID
parameter to any tool should return a validation error string without making
any Trello API call.
"""
import os
import asyncio
from unittest.mock import patch, MagicMock

if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"

from hypothesis import given, settings, assume
from hypothesis import strategies as st

import server


# ---------------------------------------------------------------------------
# Hypothesis strategies for generating invalid Trello IDs
# ---------------------------------------------------------------------------

# Empty string — always invalid
empty_id_st = st.just("")

# Strings with special characters that fail the ^[a-zA-Z0-9_-]{1,64}$ regex
special_char_st = st.text(
    alphabet=st.characters(
        whitelist_categories=("P", "S", "Z"),
        blacklist_characters="_-",  # underscore and hyphen ARE allowed
    ),
    min_size=1,
    max_size=64,
).filter(lambda s: not s.isspace() or len(s) > 0)

# Strings longer than 64 characters (valid charset but too long)
too_long_st = st.text(
    alphabet="abcdef0123456789",
    min_size=65,
    max_size=128,
)

# Combined strategy: pick from any of the three invalid categories
invalid_id_st = st.one_of(empty_id_st, special_char_st, too_long_st)


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
# Property tests: Invalid ID Rejection
# ---------------------------------------------------------------------------

@settings(max_examples=100, deadline=None)
@given(invalid_id=invalid_id_st)
def test_get_board_rejects_invalid_id(invalid_id):
    """**Validates: Requirements 5.8**

    For any invalid ID string, get_board() should return a validation error
    without calling make_trello_request.
    """
    with patch.object(server, "make_trello_request") as mock_req:
        result = run_async(server.get_board(board_id=invalid_id))
    assert result.startswith("Validation Error:"), (
        f"Expected validation error for invalid ID {invalid_id!r}, got: {result!r}"
    )
    mock_req.assert_not_called()


@settings(max_examples=100, deadline=None)
@given(invalid_id=invalid_id_st)
def test_get_card_rejects_invalid_id(invalid_id):
    """**Validates: Requirements 5.8**

    For any invalid ID string, get_card() should return a validation error
    without calling make_trello_request.
    """
    with patch.object(server, "make_trello_request") as mock_req:
        result = run_async(server.get_card(card_id=invalid_id))
    assert result.startswith("Validation Error:"), (
        f"Expected validation error for invalid ID {invalid_id!r}, got: {result!r}"
    )
    mock_req.assert_not_called()


@settings(max_examples=100, deadline=None)
@given(invalid_id=invalid_id_st)
def test_list_board_members_rejects_invalid_id(invalid_id):
    """**Validates: Requirements 5.8**

    For any invalid ID string, list_board_members() should return a validation
    error without calling make_trello_request.
    """
    with patch.object(server, "make_trello_request") as mock_req:
        result = run_async(server.list_board_members(board_id=invalid_id))
    assert result.startswith("Validation Error:"), (
        f"Expected validation error for invalid ID {invalid_id!r}, got: {result!r}"
    )
    mock_req.assert_not_called()
