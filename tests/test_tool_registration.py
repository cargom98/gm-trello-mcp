"""Unit tests for tool registration completeness.

Verifies that all 27 tools are registered on the FastMCP instance with
correct names, and that the server name is "trello-mcp-server".

Requirements: 1.3, 2.5
"""
import os
import sys
import asyncio

# Ensure TRELLO_API_KEY is set before importing server
if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"

import pytest

from mcp.server.fastmcp import FastMCP

# Guard against a previous test file having replaced mcp_server with a mock.
if "server" in sys.modules:
    srv = sys.modules["server"]
    if not isinstance(getattr(srv, "mcp_server", None), FastMCP):
        del sys.modules["server"]

import server  # noqa: E402
mcp_server = server.mcp_server


EXPECTED_TOOL_NAMES = sorted([
    "list_boards",
    "get_board",
    "list_board_lists",
    "list_board_cards",
    "create_card",
    "update_card",
    "get_card",
    "create_list",
    "list_organizations",
    "get_organization",
    "list_organization_boards",
    "list_organization_members",
    "add_organization_member",
    "remove_organization_member",
    "add_card_label",
    "remove_card_label",
    "list_card_labels",
    "list_board_labels",
    "filter_cards_by_label",
    "list_board_members",
    "add_board_member",
    "remove_board_member",
    "update_board_member",
    "invite_board_member",
    "add_card_member",
    "remove_card_member",
    "list_card_members",
])


@pytest.fixture(scope="module")
def registered_tools():
    """Fetch the list of registered tools from the FastMCP instance."""
    async def _fetch():
        return await mcp_server.list_tools()
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_fetch())
    finally:
        loop.close()


def test_server_name():
    """Server name should be 'trello-mcp-server'."""
    assert mcp_server.name == "trello-mcp-server"


def test_all_expected_tools_registered(registered_tools):
    """All 27 expected tools should be registered on the FastMCP instance."""
    actual_names = sorted(t.name for t in registered_tools)
    missing = set(EXPECTED_TOOL_NAMES) - set(actual_names)
    assert not missing, f"Missing tools: {missing}"


def test_no_unexpected_tools_registered(registered_tools):
    """No unexpected tools should be registered — exact match."""
    actual_names = sorted(t.name for t in registered_tools)
    extra = set(actual_names) - set(EXPECTED_TOOL_NAMES)
    assert not extra, f"Unexpected tools: {extra}"
    assert actual_names == EXPECTED_TOOL_NAMES
