# Trello MCP Server

A Model Context Protocol (MCP) server for interacting with Trello boards, lists, and cards.

## Features

- List all boards
- Get board details
- List cards on a board
- Create new cards
- Update card details
- Move cards between lists
- Automatic authentication on first startup

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Get your Trello API key from https://trello.com/app-key

## Usage with Kiro

Add to your `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "trello": {
      "command": "python",
      "args": ["-m", "trello_mcp_server"],
      "env": {
        "TRELLO_API_KEY": "your_api_key_from_trello"
      }
    }
  }
}
```

**Important:** Only store your API key in mcp.json, never the token.

## Authentication

The server requires authentication before it can start. You have two options:

### Option 1: Use MCP Tools (Recommended)

1. **First time setup** - Set both credentials as environment variables to start the server:

```json
{
  "mcpServers": {
    "trello": {
      "command": "python",
      "args": ["-m", "trello_mcp_server"],
      "env": {
        "TRELLO_API_KEY": "your_api_key",
        "TRELLO_TOKEN": "temporary_token"
      }
    }
  }
}
```

2. **Use the `authorize_interactive` tool** in Kiro to get a permanent token:
   - Opens browser automatically
   - Captures token and saves to `~/.trello_mcp_token.json`

3. **Remove credentials from mcp.json** - The cached token will be used automatically

### Option 2: Manual Authentication

Use the standalone authentication script:

```bash
# Interactive (opens browser and captures token)
python -m trello_mcp_server.auth --interactive

# Manual (copy-paste token)
python -m trello_mcp_server.auth --manual

# Check status
python -m trello_mcp_server.auth --check
```

After authentication, configure without credentials:

```json
{
  "mcpServers": {
    "trello": {
      "command": "python",
      "args": ["-m", "trello_mcp_server"]
    }
  }
}
```

The server will use the cached token from `~/.trello_mcp_token.json`.

## Available Tools

### Board Management
- `list_boards` - List all accessible boards
- `get_board` - Get board details

### List Management
- `list_board_lists` - Get all lists on a board
- `create_list` - Create a new list

### Card Management
- `list_board_cards` - Get all cards on a board
- `get_card` - Get card details
- `create_card` - Create a new card
- `update_card` - Update card properties (including moving between lists)

## Security

- API keys are stored in mcp.json (version controlled, but safe to share within your team)
- Tokens are stored in `~/.trello_mcp_token.json` (never committed to version control)
- Token cache file has restricted permissions (600 - owner read/write only)
- Tokens never expire unless manually revoked

## Troubleshooting

### Server won't start

**Cause:** No authentication found

**Solution:** Ensure `TRELLO_API_KEY` is set in mcp.json or as an environment variable. The server will automatically open your browser to complete authentication.

### Browser doesn't open

**Cause:** No default browser configured or headless environment

**Solution:** Use manual authentication:
```bash
python -m trello_mcp_server.auth --manual
```

### Port already in use

**Cause:** Port 8765 is already in use during OAuth callback

**Solution:** The authentication will fail and you can retry. If it persists, use manual authentication.

### Check authentication status

```bash
python -m trello_mcp_server.auth --check
```

## Advanced Usage

For detailed authentication workflows and troubleshooting, see [AUTHENTICATION.md](AUTHENTICATION.md).

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
python -m pytest

# Check authentication
python -m trello_mcp_server.auth --check
```
