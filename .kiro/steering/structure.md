# Project Structure

## Directory Layout

```
trello-mcp-server/
├── .kiro/                      # Development configuration
│   ├── settings/               # Local MCP server settings
│   └── steering/               # Project steering rules
├── docs/                       # Detailed documentation
│   ├── AUTHENTICATION.md      # Detailed auth flow documentation
│   ├── ORGANIZATIONS.md       # Organization management guide
│   ├── STARTUP_FLOW.md        # Server startup documentation
│   └── FUTURE_FEATURES.md     # Planned features
├── tests/                      # Test files
│   ├── test_auth.py           # Authentication tests
│   ├── test_organizations.py  # Organization management tests
│   ├── test_release.sh        # Release testing script
│   └── verify_card_members.py # Card member verification tests
├── venv/                       # Python virtual environment (gitignored)
├── __init__.py                # Package initialization
├── __main__.py                # Entry point for `python -m trello_mcp_server`
├── server.py                  # MCP server, tools, API client, auth logic
├── auth.py                    # Standalone authentication CLI
├── requirements.txt           # Python dependencies
├── setup.sh                   # Setup automation script
├── pyproject.toml             # Python project metadata
├── README.md                  # Quick start guide
└── CHANGELOG.md               # Version history
```

## Key Files

### Core Implementation
- `server.py` - Central file containing:
  - `TrelloAuth` class for credential management
  - `make_trello_request()` for API calls
  - MCP tool definitions and handlers
  - OAuth callback server for interactive auth
- `auth.py` - Standalone authentication CLI

### Configuration
- `.kiro/settings/mcp.json` - Local MCP server configuration (for development)
- `~/.trello_mcp_token.json` - Cached OAuth credentials (secure, 600 permissions)

### Documentation
- `README.md` - Quick start guide and installation
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
- Test files in `tests/` directory
- Use descriptive test names
- Test both success and error cases
- Include interactive test scripts for manual verification
