"""Property test: Schema Equivalence for all migrated tools.

# Feature: fastmcp-migration, Property 1: Schema Equivalence

Validates: Requirements 2.2, 3.1, 3.2, 3.3

For each of the 27 tools (board/list, organization, label, and member tools),
compare the FastMCP auto-generated input schema (property names, required
list, types) against the expected schema from the original list_tools()
definitions.
"""
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock

# Ensure TRELLO_API_KEY is set before importing server
if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Expected schemas from the original list_tools() definitions
# ---------------------------------------------------------------------------

EXPECTED_SCHEMAS = {
    "list_boards": {
        "properties": {},
        "required": [],
    },
    "get_board": {
        "properties": {"board_id": "string"},
        "required": ["board_id"],
    },
    "list_board_lists": {
        "properties": {"board_id": "string"},
        "required": ["board_id"],
    },
    "list_board_cards": {
        "properties": {"board_id": "string"},
        "required": ["board_id"],
    },
    "create_card": {
        "properties": {"list_id": "string", "name": "string", "desc": "string"},
        "required": ["list_id", "name"],
    },
    "update_card": {
        "properties": {
            "card_id": "string",
            "name": "string",
            "desc": "string",
            "list_id": "string",
        },
        "required": ["card_id"],
    },
    "get_card": {
        "properties": {"card_id": "string"},
        "required": ["card_id"],
    },
    "create_list": {
        "properties": {"board_id": "string", "name": "string", "pos": "string"},
        "required": ["board_id", "name"],
    },
    # Organization tools (task 3.1)
    "list_organizations": {
        "properties": {},
        "required": [],
    },
    "get_organization": {
        "properties": {"org_id": "string"},
        "required": ["org_id"],
    },
    "list_organization_boards": {
        "properties": {"org_id": "string"},
        "required": ["org_id"],
    },
    "list_organization_members": {
        "properties": {"org_id": "string"},
        "required": ["org_id"],
    },
    "add_organization_member": {
        "properties": {"org_id": "string", "email": "string", "full_name": "string", "type": "string"},
        "required": ["org_id", "email"],
    },
    "remove_organization_member": {
        "properties": {"org_id": "string", "member_id": "string"},
        "required": ["org_id", "member_id"],
    },
    # Label tools (task 4.1)
    "add_card_label": {
        "properties": {"card_id": "string", "label_id": "string"},
        "required": ["card_id", "label_id"],
    },
    "remove_card_label": {
        "properties": {"card_id": "string", "label_id": "string"},
        "required": ["card_id", "label_id"],
    },
    "list_card_labels": {
        "properties": {"card_id": "string"},
        "required": ["card_id"],
    },
    "list_board_labels": {
        "properties": {"board_id": "string"},
        "required": ["board_id"],
    },
    "filter_cards_by_label": {
        "properties": {"board_id": "string", "label_id": "string"},
        "required": ["board_id", "label_id"],
    },
    # Member tools (task 6.1)
    "list_board_members": {
        "properties": {"board_id": "string"},
        "required": ["board_id"],
    },
    "add_board_member": {
        "properties": {"board_id": "string", "member_id": "string", "type": "string"},
        "required": ["board_id", "member_id"],
    },
    "remove_board_member": {
        "properties": {"board_id": "string", "member_id": "string"},
        "required": ["board_id", "member_id"],
    },
    "update_board_member": {
        "properties": {"board_id": "string", "member_id": "string", "type": "string"},
        "required": ["board_id", "member_id", "type"],
    },
    "invite_board_member": {
        "properties": {"board_id": "string", "email": "string", "type": "string"},
        "required": ["board_id", "email"],
    },
    "add_card_member": {
        "properties": {"card_id": "string", "member_id": "string"},
        "required": ["card_id", "member_id"],
    },
    "remove_card_member": {
        "properties": {"card_id": "string", "member_id": "string"},
        "required": ["card_id", "member_id"],
    },
    "list_card_members": {
        "properties": {"card_id": "string"},
        "required": ["card_id"],
    },
}

TOOL_NAMES = list(EXPECTED_SCHEMAS.keys())


# ---------------------------------------------------------------------------
# Helper: resolve the effective type of a FastMCP property to "string"
# ---------------------------------------------------------------------------

def _resolve_type(prop_schema: dict) -> str:
    """Return the canonical type string for a FastMCP-generated property.

    FastMCP represents:
      - required string params as  {"type": "string", ...}
      - optional string params as  {"anyOf": [{"type": "string"}, {"type": "null"}], ...}

    Both should resolve to "string" for equivalence with the original
    hand-written schemas that always used {"type": "string"}.
    """
    if "type" in prop_schema:
        return prop_schema["type"]
    if "anyOf" in prop_schema:
        types = {item["type"] for item in prop_schema["anyOf"] if "type" in item}
        # Remove "null" — the remaining type is the effective type
        types.discard("null")
        if len(types) == 1:
            return types.pop()
    return "unknown"


# ---------------------------------------------------------------------------
# Fetch tool schemas from the live FastMCP instance (cached)
# ---------------------------------------------------------------------------

_tool_schema_cache: dict | None = None


def _get_tool_schemas() -> dict:
    """Return {tool_name: inputSchema} from the FastMCP mcp_server instance."""
    global _tool_schema_cache
    if _tool_schema_cache is not None:
        return _tool_schema_cache

    from mcp.server.fastmcp import FastMCP

    # If a previous test file imported server with a mocked FastMCP,
    # force a clean re-import so we get the real FastMCP instance.
    if "server" in sys.modules:
        srv = sys.modules["server"]
        if not isinstance(getattr(srv, "mcp_server", None), FastMCP):
            del sys.modules["server"]

    import server  # noqa: E402 — side-effect import, same pattern as other tests

    async def _fetch():
        tools = await server.mcp_server.list_tools()
        return {t.name: t.inputSchema for t in tools}

    _tool_schema_cache = asyncio.get_event_loop_policy().new_event_loop().run_until_complete(_fetch())
    return _tool_schema_cache


# ---------------------------------------------------------------------------
# Property-based test: Schema Equivalence
# ---------------------------------------------------------------------------

@settings(max_examples=100, deadline=None)
@given(tool_name=st.sampled_from(TOOL_NAMES))
def test_schema_equivalence(tool_name: str):
    """**Validates: Requirements 2.2, 3.1, 3.2, 3.3**

    For any tool in the migrated server, the FastMCP auto-generated input
    schema (property names, required list, and types) should be equivalent
    to the original hand-written inputSchema from the list_tools() definition.
    """
    schemas = _get_tool_schemas()
    expected = EXPECTED_SCHEMAS[tool_name]

    assert tool_name in schemas, f"Tool '{tool_name}' not found in FastMCP server"
    actual_schema = schemas[tool_name]

    # 1. Property names must match
    actual_props = set(actual_schema.get("properties", {}).keys())
    expected_props = set(expected["properties"].keys())
    assert actual_props == expected_props, (
        f"[{tool_name}] Property names differ: "
        f"expected={sorted(expected_props)}, got={sorted(actual_props)}"
    )

    # 2. Required fields must match
    actual_required = sorted(actual_schema.get("required", []))
    expected_required = sorted(expected["required"])
    assert actual_required == expected_required, (
        f"[{tool_name}] Required fields differ: "
        f"expected={expected_required}, got={actual_required}"
    )

    # 3. Types must match (resolving FastMCP's anyOf for optionals)
    for prop_name, expected_type in expected["properties"].items():
        actual_prop = actual_schema["properties"][prop_name]
        actual_type = _resolve_type(actual_prop)
        assert actual_type == expected_type, (
            f"[{tool_name}].{prop_name} type differs: "
            f"expected='{expected_type}', got='{actual_type}'"
        )
