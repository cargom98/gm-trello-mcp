# Project Structure

## Directory Layout

```
trello-mcp-server/
├── .kiro/                      # Kiro configuration
│   ├── settings/               # MCP server settings
│   └── steering/               # Project steering rules
├── trello_mcp_server/          # Main Python package
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # Entry point for `python -m trello_mcp_server`
│   ├── server.py              # MCP server, tools, API client, auth logic
│   └── auth.py                # Standalone authentication CLI
├── docs/                       # Detailed documentation
│   ├── AUTHENTICATION.md      # Detailed auth flow documentation
│   ├── ORGANIZATIONS.md       # Organization management guide
│   ├── STARTUP_FLOW.md        # Server startup documentation
│   └── FUTURE_FEATURES.md     # Planned features
├── venv/                       # Python virtual environment (gitignored)
├── test_auth.py               # Authentication tests
├── test_organizations.py      # Organization management tests
├── requirements.txt           # Python dependencies
├── setup.sh                   # Setup automation script
├── pyproject.toml             # Python project metadata
├── mcp.json                   # MCP server configuration (power config)
├── logo.png                   # Power icon
├── POWER.md                   # Kiro power documentation (main docs)
├── README.md                  # Developer quick start
└── CHANGELOG.md               # Version history
```

## Key Files

### Core Implementation
- `trello_mcp_server/server.py` - Central file containing:
  - `TrelloAuth` class for credential management
  - `make_trello_request()` for API calls
  - MCP tool definitions and handlers
  - OAuth callback server for interactive auth

### Configuration
- `.kiro/settings/mcp.json` - MCP server configuration (workspace-level)
- `~/.kiro/settings/mcp.json` - User-level MCP configuration
- `~/.trello_mcp_token.json` - Cached OAuth credentials (secure, 600 permissions)

### Documentation
- `README.md` - Developer quick start and overview
- `POWER.md` - Kiro power documentation with workflows (main user docs)
- `CHANGELOG.md` - Version history
- `docs/AUTHENTICATION.md` - Complete authentication workflows
- `docs/ORGANIZATIONS.md` - Organization/workspace management
- `docs/STARTUP_FLOW.md` - Server startup process
- `docs/FUTURE_FEATURES.md` - Planned features

## Code Organization

### Server Module (`server.py`)
- Global constants: `TRELLO_API_BASE`, `TOKEN_CACHE_FILE`
- `TrelloAuth` class: Manages API key, token, caching
- `OAuthCallbackHandler`: HTTP handler for OAuth flow
- `make_trello_request()`: Authenticated API client
- `@app.list_tools()`: Tool registration
- `@app.call_tool()`: Tool execution dispatcher
- `main()`: Server startup with auto-authentication

### Auth Module (`auth.py`)
- Standalone CLI for authentication
- Imports `TrelloAuth` from `server.py`
- Supports interactive, manual, and check modes

## Conventions

### Naming
- Python package: `trello_mcp_server` (snake_case)
- MCP server name: `trello` (lowercase)
- Tool names: `list_boards`, `create_card` (snake_case)
- Trello IDs: `board_id`, `list_id`, `card_id`, `org_id`

### Error Handling
- Use `requests.exceptions.HTTPError` for API errors
- Log errors with `logger.error()`
- Return user-friendly error messages via `TextContent`
- Raise `ValueError` for authentication failures

### Security
- Never commit tokens or API keys
- Store tokens in home directory (`~/.trello_mcp_token.json`)
- Set file permissions to 600 on token cache
- Use environment variables for CI/CD

### Testing
- Test files at project root
- Use descriptive test names
- Test both success and error cases
- Include interactive test scripts for manual verification
