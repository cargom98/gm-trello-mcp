"""Property test: Label Filtering Correctness.

# Feature: fastmcp-migration, Property 4: Label Filtering Correctness

Validates: Requirements 4.5

For any list of cards with random label assignments and for any target label ID,
calling filter_cards_by_label should return exactly the cards whose idLabels
array contains the target label ID, and no others.
"""
import os
import asyncio
from unittest.mock import patch, call

# Ensure TRELLO_API_KEY is set before importing server
if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"

from hypothesis import given, settings, assume
from hypothesis import strategies as st

import server


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Trello IDs: 24-char hex strings
trello_id_st = st.text(
    alphabet="0123456789abcdef",
    min_size=24,
    max_size=24,
)

# Card/board names: non-empty printable text (no null bytes)
name_st = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z"),
        blacklist_characters="\x00",
    ),
    min_size=1,
    max_size=60,
)

# A label object with id, name, color
label_obj_st = st.fixed_dictionaries({
    "id": trello_id_st,
    "name": name_st,
    "color": st.sampled_from(["green", "yellow", "orange", "red", "purple", "blue", "none"]),
})

# A card dict with idLabels drawn from a provided pool of label IDs
def card_st(label_id_pool):
    """Generate a card dict whose idLabels is a subset of label_id_pool."""
    return st.fixed_dictionaries({
        "name": name_st,
        "id": trello_id_st,
        "idList": trello_id_st,
        "idLabels": st.lists(st.sampled_from(label_id_pool), max_size=len(label_id_pool), unique=True)
            if label_id_pool else st.just([]),
        "labels": st.just([]),  # simplified; labels list isn't used for filtering
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


# ---------------------------------------------------------------------------
# Property test: Label Filtering Correctness
# ---------------------------------------------------------------------------

@settings(max_examples=100, deadline=None)
@given(
    label_ids=st.lists(trello_id_st, min_size=1, max_size=6, unique=True),
    data=st.data(),
)
def test_filter_cards_by_label_correctness(label_ids, data):
    """**Validates: Requirements 4.5**

    For any list of cards with random idLabels and any target label ID,
    filter_cards_by_label returns exactly the cards whose idLabels contains
    the target label ID.
    """
    # Pick a target label from the pool
    target_label_id = data.draw(st.sampled_from(label_ids))

    # Generate a random list of cards using the label pool
    cards = data.draw(
        st.lists(card_st(label_ids), min_size=0, max_size=10)
    )

    # Compute expected filtered cards
    expected_cards = [c for c in cards if target_label_id in c.get("idLabels", [])]

    # Board ID for the mock call
    board_id = "abc123def456abc123def456"

    # Build mock side_effect: first call returns cards, second (if needed) returns labels
    board_labels = [{"id": lid, "name": f"Label-{lid[:6]}", "color": "green"} for lid in label_ids]

    def mock_request(method, endpoint, **kwargs):
        if endpoint == f"/boards/{board_id}/cards":
            return cards
        if endpoint == f"/boards/{board_id}/labels":
            return board_labels
        raise ValueError(f"Unexpected request: {method} {endpoint}")

    with patch.object(server, "make_trello_request", side_effect=mock_request) as mock_req:
        result = run_async(server.filter_cards_by_label(board_id=board_id, label_id=target_label_id))

    # Build the set of expected card lines (one per matching card)
    expected_lines = [
        f"- {card['name']} (ID: {card['id']}, List: {card['idList']})"
        for card in expected_cards
    ]

    if not expected_cards:
        # No matching cards → result must contain "(No cards found)"
        assert "(No cards found)" in result, (
            f"Expected '(No cards found)' for empty filter result.\n"
            f"Result: {result}"
        )
    else:
        assert "(No cards found)" not in result, (
            f"Got '(No cards found)' but expected {len(expected_cards)} cards.\n"
            f"Result: {result}"
        )

        # Extract the card lines from the result (lines starting with "- ")
        result_card_lines = [
            line for line in result.split("\n") if line.startswith("- ")
        ]

        # The number of card lines must equal the number of expected cards
        assert len(result_card_lines) == len(expected_cards), (
            f"Expected {len(expected_cards)} card lines but got {len(result_card_lines)}.\n"
            f"Result lines: {result_card_lines}\n"
            f"Expected lines: {expected_lines}"
        )

        # Each expected card line must appear in the result card lines
        # (using sorted comparison to handle order)
        assert sorted(result_card_lines) == sorted(expected_lines), (
            f"Card lines mismatch.\n"
            f"Result lines:   {sorted(result_card_lines)}\n"
            f"Expected lines: {sorted(expected_lines)}"
        )
