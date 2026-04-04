# Implementation Plan: FastMCP Migration

## Overview

Migrate `server.py` from the low-level MCP SDK (`mcp.server.Server` with monolithic `list_tools()`/`call_tool()`) to FastMCP's decorator-based `@mcp.tool()` pattern. The migration is done in-place, preserving all existing behavior, authentication, error handling, and module exports. Tasks are ordered so each step builds on the previous and the server remains functional at each checkpoint.

## Tasks

- [x] 1. Update server initialization and imports
  - [x] 1.1 Replace imports and FastMCP initialization
    - Replace `from mcp.server import Server` with `from mcp.server.fastmcp import FastMCP`
    - Remove `from mcp.types import Tool, TextContent` import
    - Remove `import mcp.server.stdio` import
    - Add `import functools` for the error handling decorator
    - Change `app = Server("trello-mcp-server")` to `mcp_server = FastMCP("trello-mcp-server")`
    - Use `mcp_server` as the variable name to avoid shadowing the `mcp` package import
    - _Requirements: 1.1, 1.3_

  - [x] 1.2 Create the `handle_request_errors` decorator
    - Implement the decorator in `server.py` using `functools.wraps`
    - Handle `ValueError` (ID validation), `requests.exceptions.HTTPError` (with status-code-specific messages for 401, 403, 404, 429), `requests.exceptions.Timeout`, `requests.exceptions.ConnectionError`, and generic `Exception`
    - Error messages must be identical to the current `call_tool()` implementation
    - Return plain `str` error messages (not `list[TextContent]`)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [x] 1.3 Write unit tests for the `handle_request_errors` decorator
    - Test each HTTP status code mapping (401, 403, 404, 429, other)
    - Test Timeout, ConnectionError, ValueError, and generic Exception handling
    - Verify error message strings match the design's error mapping table exactly
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

- [x] 2. Convert board and list tools (8 tools)
  - [x] 2.1 Convert `list_boards`, `get_board`, `list_board_lists`, `list_board_cards`
    - Extract each from the `call_tool()` if/elif chain into a standalone `@mcp_server.tool()` decorated async function
    - Apply `@handle_request_errors` decorator to each
    - Define parameters as typed function arguments (e.g., `board_id: str`)
    - Call `validate_trello_id()` for ID parameters at the start of each function body
    - Return `str` instead of `list[TextContent]`
    - Use docstrings matching the current tool descriptions
    - _Requirements: 2.1, 2.2, 2.5, 3.1, 3.2, 3.3, 4.1, 4.2_

  - [x] 2.2 Convert `create_card`, `update_card`, `get_card`, `create_list`
    - Same pattern as 2.1 for each tool
    - For `create_card`: required params `list_id: str, name: str`, optional `desc: Optional[str] = None`
    - For `update_card`: required `card_id: str`, optional `name: Optional[str] = None, desc: Optional[str] = None, list_id: Optional[str] = None`
    - For `create_list`: required `board_id: str, name: str`, optional `pos: Optional[str] = None`
    - _Requirements: 2.1, 2.2, 2.5, 3.1, 3.2, 3.3, 4.1, 4.3, 4.4_

  - [x] 2.3 Write property test: Schema Equivalence for board/list tools
    - **Property 1: Schema Equivalence**
    - Parameterize over the 8 tools converted in 2.1 and 2.2
    - For each tool, compare FastMCP auto-generated input schema (property names, required list, types) against the expected schema from the original `list_tools()` definitions
    - **Validates: Requirements 2.2, 3.1, 3.2, 3.3**

  - [x] 2.4 Write property test: Output Format Equivalence for board/list tools
    - **Property 2: Output Format Equivalence**
    - For `list_boards`, `get_board`, `create_card`, `update_card`, generate random valid mocked API responses using `hypothesis`
    - Verify the new tool function returns the same formatted string as the old dispatcher would have
    - **Validates: Requirements 4.1**

- [x] 3. Convert organization tools (6 tools)
  - [x] 3.1 Convert `list_organizations`, `get_organization`, `list_organization_boards`, `list_organization_members`, `add_organization_member`, `remove_organization_member`
    - Same decorator pattern as board tools
    - For `add_organization_member`: required `org_id: str, email: str`, optional `full_name: Optional[str] = None, type: Optional[str] = None`
    - For `remove_organization_member`: required `org_id: str, member_id: str`
    - _Requirements: 2.1, 2.2, 2.5, 3.1, 3.2, 3.3, 4.1_

  - [x] 3.2 Write property test: Schema Equivalence for organization tools
    - **Property 1: Schema Equivalence (continued)**
    - Parameterize over the 6 organization tools
    - Compare auto-generated schemas against original definitions
    - **Validates: Requirements 2.2, 3.1, 3.2, 3.3**

- [x] 4. Convert label tools (5 tools)
  - [x] 4.1 Convert `add_card_label`, `remove_card_label`, `list_card_labels`, `list_board_labels`, `filter_cards_by_label`
    - Same decorator pattern
    - For `filter_cards_by_label`: required `board_id: str, label_id: str`
    - _Requirements: 2.1, 2.2, 2.5, 3.1, 3.2, 3.3, 4.1, 4.5_

  - [x] 4.2 Write property test: Label Filtering Correctness
    - **Property 4: Label Filtering Correctness**
    - Generate random lists of card dicts with random `idLabels` arrays using `hypothesis`
    - Mock `make_trello_request` to return the generated cards
    - Verify `filter_cards_by_label` returns exactly the cards whose `idLabels` contains the target label ID
    - **Validates: Requirements 4.5**

- [x] 5. Checkpoint - Verify board, org, and label tools
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Convert member tools (7 tools)
  - [x] 6.1 Convert `list_board_members`, `add_board_member`, `remove_board_member`, `update_board_member`, `invite_board_member`, `add_card_member`, `remove_card_member`, `list_card_members`
    - Same decorator pattern
    - For `add_board_member`: required `board_id: str, member_id: str`, optional `type: Optional[str] = None`
    - For `update_board_member`: required `board_id: str, member_id: str, type: str`
    - For `invite_board_member`: required `board_id: str, email: str`, optional `type: Optional[str] = None`
    - _Requirements: 2.1, 2.2, 2.5, 3.1, 3.2, 3.3, 4.1_

  - [x] 6.2 Write property test: Schema Equivalence for member tools
    - **Property 1: Schema Equivalence (continued)**
    - Parameterize over the 8 member tools (including `list_card_members`)
    - Compare auto-generated schemas against original definitions
    - **Validates: Requirements 2.2, 3.1, 3.2, 3.3**

- [x] 7. Remove old dispatcher and update entry point
  - [x] 7.1 Remove `list_tools()` and `call_tool()` functions
    - Delete the entire `@app.list_tools()` decorated `list_tools()` function
    - Delete the entire `@app.call_tool()` decorated `call_tool()` function (including the if/elif dispatcher)
    - Remove any remaining references to `app` variable
    - _Requirements: 2.3, 2.4_

  - [x] 7.2 Update `main()` to use FastMCP's `run_async()`
    - Replace the `async with mcp.server.stdio.stdio_server()` block with `await mcp_server.run_async(transport="stdio")`
    - Keep all authentication checks and logging in `main()` unchanged
    - Preserve the `run()` synchronous wrapper function
    - _Requirements: 1.2, 7.1, 7.3_

  - [x] 7.3 Write property test: Optional Field Passthrough for `update_card`
    - **Property 3: Optional Field Passthrough**
    - Use `hypothesis` to generate random subsets of `{name, desc, list_id}` with random string values
    - Mock `make_trello_request` and verify only the provided fields appear in the `data` dict argument
    - Verify omitted fields are not present in the data dict
    - **Validates: Requirements 4.4**

  - [x] 7.4 Write property test: Invalid ID Rejection
    - **Property 5: Invalid ID Rejection**
    - Use `hypothesis` to generate invalid ID strings (empty, special characters, >64 chars)
    - Call tool functions that accept ID parameters with the invalid IDs
    - Verify a validation error string is returned without `make_trello_request` being called
    - **Validates: Requirements 5.8**

- [x] 8. Checkpoint - Full migration verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Verify module exports and integration
  - [x] 9.1 Verify `auth.py` import compatibility
    - Confirm `auth.py` can still import `TrelloAuth`, `TOKEN_CACHE_FILE`, and `logger` from `server`
    - Confirm `__main__.py` can still import `main` from `.server`
    - Confirm `pyproject.toml` entry point `server:run` still resolves correctly
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 9.2 Write unit tests for tool registration completeness
    - Verify all 26 tools are registered on the FastMCP instance
    - Verify each tool has the correct name
    - Verify the server name is `"trello-mcp-server"`
    - _Requirements: 1.3, 2.5_

  - [x] 9.3 Verify dependency declarations
    - Confirm `requirements.txt` has `mcp>=1.26.0` and `requests>=2.32.0`
    - Confirm `pyproject.toml` dependencies match
    - No new dependencies should be added
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The variable name `mcp_server` is used instead of `mcp` to avoid shadowing the `mcp` package import
