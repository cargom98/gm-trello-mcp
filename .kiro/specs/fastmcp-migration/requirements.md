# Requirements Document

## Introduction

Migrate the existing Trello MCP server from the low-level MCP SDK (`mcp.server.Server` with manual `@app.list_tools()` / `@app.call_tool()` dispatchers) to the FastMCP decorator-based approach. FastMCP simplifies tool registration by using `@mcp.tool()` decorators on individual functions, eliminating the monolithic dispatcher pattern. The migration must preserve all existing functionality, authentication flows, error handling, and the stdio transport while modernizing the server architecture.

## Glossary

- **FastMCP**: A high-level API provided by the `mcp` package (`from mcp.server.fastmcp import FastMCP`) that uses decorator-based tool registration instead of manual schema definitions and dispatcher functions.
- **Low_Level_MCP**: The current approach using `mcp.server.Server` with `@app.list_tools()` and `@app.call_tool()` handler patterns requiring manual `Tool` schema definitions and a monolithic dispatcher.
- **Server**: The Trello MCP server application (`server.py`) that exposes Trello API operations as MCP tools.
- **Tool_Function**: An individual Python function decorated with `@mcp.tool()` that handles a single MCP tool invocation, with parameters defined via function arguments and type hints.
- **Dispatcher**: The current monolithic `call_tool()` function that routes tool calls to handler logic via if/elif chains based on the tool name.
- **TrelloAuth**: The authentication class managing API key and OAuth token credentials, including caching and interactive browser-based authorization.
- **Token_Cache**: The JSON file at `~/.trello_mcp_token.json` storing cached Trello API credentials with 600 file permissions.
- **Stdio_Transport**: The MCP communication transport using standard input/output streams for client-server communication.

## Requirements

### Requirement 1: FastMCP Server Initialization

**User Story:** As a developer, I want the server to use FastMCP initialization, so that tool registration is simplified and follows modern MCP patterns.

#### Acceptance Criteria

1. THE Server SHALL initialize using `FastMCP("trello-mcp-server")` from `mcp.server.fastmcp` instead of `Server("trello-mcp-server")` from `mcp.server`.
2. THE Server SHALL use `mcp.run(transport="stdio")` for starting the stdio transport instead of manually creating `stdio_server()` read/write streams.
3. THE Server SHALL retain the server name `"trello-mcp-server"` in the FastMCP constructor.

### Requirement 2: Decorator-Based Tool Registration

**User Story:** As a developer, I want each tool to be registered via `@mcp.tool()` decorators on individual functions, so that tool definitions are co-located with their implementation and the monolithic dispatcher is eliminated.

#### Acceptance Criteria

1. WHEN a tool is registered, THE Server SHALL use the `@mcp.tool()` decorator on an individual async function for that tool.
2. THE Server SHALL define tool parameters as typed function arguments instead of manual `inputSchema` dictionaries.
3. THE Server SHALL remove the monolithic `list_tools()` function that returns a list of `Tool` objects.
4. THE Server SHALL remove the monolithic `call_tool()` dispatcher function that routes calls via if/elif chains.
5. THE Server SHALL register all 26 existing tools as individual decorated functions: `list_boards`, `get_board`, `list_board_lists`, `list_board_cards`, `create_card`, `update_card`, `get_card`, `create_list`, `list_organizations`, `get_organization`, `list_organization_boards`, `list_organization_members`, `add_organization_member`, `remove_organization_member`, `add_card_label`, `remove_card_label`, `list_card_labels`, `list_board_labels`, `filter_cards_by_label`, `list_board_members`, `add_board_member`, `remove_board_member`, `update_board_member`, `invite_board_member`, `add_card_member`, `remove_card_member`, `list_card_members`.

### Requirement 3: Tool Parameter Typing

**User Story:** As a developer, I want tool parameters to use Python type hints, so that FastMCP can auto-generate input schemas and provide validation.

#### Acceptance Criteria

1. THE Server SHALL define required tool parameters as non-optional typed function arguments (e.g., `board_id: str`).
2. THE Server SHALL define optional tool parameters with default values of `None` and `Optional` type hints (e.g., `desc: Optional[str] = None`).
3. THE Server SHALL preserve the existing parameter names and descriptions for each tool using the same names as the current `inputSchema` definitions.

### Requirement 4: Functional Equivalence of Tool Behavior

**User Story:** As a developer, I want all tools to produce identical responses after migration, so that existing MCP clients experience no change in behavior.

#### Acceptance Criteria

1. WHEN any tool is called with valid arguments, THE Server SHALL return the same text content as the current implementation.
2. WHEN `list_boards` is called, THE Server SHALL return a formatted list of board names and IDs from the authenticated user.
3. WHEN `create_card` is called with a `list_id` and `name`, THE Server SHALL create a card and return the card name, ID, and URL.
4. WHEN `update_card` is called, THE Server SHALL update only the provided fields (name, desc, list_id) and return the updated card details.
5. WHEN `filter_cards_by_label` is called, THE Server SHALL fetch all board cards, filter by the specified label ID, and return matching cards.

### Requirement 5: Error Handling Preservation

**User Story:** As a developer, I want error handling to remain consistent after migration, so that clients receive the same error messages for the same failure conditions.

#### Acceptance Criteria

1. WHEN a Trello API call returns HTTP 401, THE Server SHALL return "Error: Authentication failed. Please check your credentials."
2. WHEN a Trello API call returns HTTP 403, THE Server SHALL return "Error: Permission denied. You don't have access to this resource."
3. WHEN a Trello API call returns HTTP 404, THE Server SHALL return "Error: Resource not found. Please check the ID."
4. WHEN a Trello API call returns HTTP 429, THE Server SHALL return "Error: Rate limit exceeded. Please try again later."
5. WHEN a Trello API call times out, THE Server SHALL return "Error: Request timed out. Please try again."
6. WHEN a network connection error occurs, THE Server SHALL return "Error: Cannot connect to Trello API. Please check your network."
7. WHEN an unexpected error occurs, THE Server SHALL return "Error: An unexpected error occurred. Please try again."
8. WHEN a tool receives an invalid Trello ID, THE Server SHALL return a validation error message before making any API call.

### Requirement 6: Authentication Flow Preservation

**User Story:** As a developer, I want the authentication system to remain unchanged, so that existing token caches and environment variable configurations continue to work.

#### Acceptance Criteria

1. THE Server SHALL retain the `TrelloAuth` class with identical credential management logic.
2. THE Server SHALL continue to read `TRELLO_API_KEY` and `TRELLO_TOKEN` from environment variables.
3. THE Server SHALL continue to load and save cached tokens from `~/.trello_mcp_token.json` with 600 file permissions.
4. WHEN the server starts without valid credentials, THE Server SHALL trigger the interactive browser-based OAuth flow.
5. THE Server SHALL retain the `OAuthCallbackHandler` and local HTTP server for OAuth callback handling.
6. THE Server SHALL retain the `validate_trello_id()` function for input sanitization.
7. THE Server SHALL retain the `make_trello_request()` function for authenticated Trello API calls.

### Requirement 7: Entry Point and Package Compatibility

**User Story:** As a developer, I want the package entry points to continue working, so that existing installation and launch configurations remain valid.

#### Acceptance Criteria

1. THE Server SHALL export a `run()` function callable as the `trello-mcp-server` console script entry point.
2. THE Server SHALL remain importable from `__main__.py` via `from .server import main as server_main`.
3. THE Server SHALL preserve the `main()` async function that performs startup authentication checks before running the server.
4. THE `auth.py` module SHALL continue to import `TrelloAuth`, `TOKEN_CACHE_FILE`, and `logger` from `server.py` without modification.

### Requirement 8: Dependency Update

**User Story:** As a developer, I want the project dependencies to reflect the FastMCP requirement, so that the package installs correctly.

#### Acceptance Criteria

1. THE Server project SHALL specify `mcp>=1.26.0` as a dependency in `pyproject.toml` and `requirements.txt` (this version includes FastMCP).
2. THE Server project SHALL retain `requests>=2.32.0` as a dependency.
3. THE Server project SHALL not introduce any new dependencies beyond what is required by FastMCP.
