"""Property test: Optional Field Passthrough for `update_card`.

# Feature: fastmcp-migration, Property 3: Optional Field Passthrough

Validates: Requirements 4.4

Use hypothesis to generate random subsets of {name, desc, list_id} with random
string values. Mock make_trello_request and verify only the provided fields
appear in the data dict argument. Verify omitted fields are not present.
"""
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock, call

# Ensure TRELLO_API_KEY is set before importing server
if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

import server


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Non-empty strings for field values (printable, no null bytes)
field_value_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"), blacklist_characters="\x00"),
    min_size=1,
    max_size=100,
)

# Strategy: generate a random subset of optional fields with random values.
# Each field is independently either present (with a random string) or absent (None).
optional_fields_st = st.fixed_dictionaries({
    "name": st.one_of(st.none(), field_value_st),
    "desc": st.one_of(st.none(), field_value_st),
    "list_id": st.one_of(st.none(), field_value_st),
})


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


# The mapping from update_card kwargs to data dict keys
FIELD_TO_DATA_KEY = {
    "name": "name",
    "desc": "desc",
    "list_id": "idList",
}


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------

@settings(max_examples=100, deadline=None)
@given(fields=optional_fields_st)
def test_optional_field_passthrough(fields):
    """**Validates: Requirements 4.4**

    For any subset of optional fields provided to update_card, only the
    provided fields should appear in the data dictionary sent to
    make_trello_request, and omitted fields should not be present.
    """
    # Build kwargs: only pass fields that are not None
    kwargs = {k: v for k, v in fields.items() if v is not None}

    # Mock response for make_trello_request
    mock_response = {"name": "card", "id": "abc123def456abc123def456", "url": "https://trello.com/c/abc"}

    with patch.object(server, "make_trello_request", return_value=mock_response) as mock_req:
        run_async(server.update_card(card_id="abc123def456abc123def456", **kwargs))

        # Verify make_trello_request was called
        mock_req.assert_called_once()

        # Extract the data dict passed to make_trello_request("PUT", ..., data=data)
        actual_data = mock_req.call_args.kwargs.get("data", {}) or {}

        # Check provided fields ARE in data with correct mapped keys and values
        for field_name, value in kwargs.items():
            data_key = FIELD_TO_DATA_KEY[field_name]
            assert data_key in actual_data, (
                f"Field '{field_name}' was provided (value={value!r}) but "
                f"'{data_key}' is missing from data dict: {actual_data}"
            )
            assert actual_data[data_key] == value, (
                f"Field '{field_name}' value mismatch: expected {value!r}, "
                f"got {actual_data[data_key]!r}"
            )

        # Check omitted fields are NOT in data
        for field_name, value in fields.items():
            if value is None:
                data_key = FIELD_TO_DATA_KEY[field_name]
                assert data_key not in actual_data, (
                    f"Field '{field_name}' was omitted (None) but "
                    f"'{data_key}' is present in data dict: {actual_data}"
                )
