# Trello MCP Server

A Model Context Protocol (MCP) server that provides programmatic access to Trello's API. Manage boards, lists, cards, and organizations directly from any MCP-compatible client.

## Quick Start

### 1. Install

```bash
# Using uvx (recommended)
uvx trello-mcp-server

# Using uv
uv tool install trello-mcp-server

# Using pip
pip install trello-mcp-server
```

### 2. Get API Key

Visit https://trello.com/power-ups/admin/new and create a Power-Up to get your API key (free, takes seconds).

### 3. Configure MCP Client

Add to your MCP settings configuration file:

```json
{
  "mcpServers": {
    "trello": {
      "command": "uvx",
      "args": ["trello-mcp-server"],
      "env": {
        "TRELLO_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 4. Authenticate

On first use, the server automatically opens your browser to authorize access. Click "Allow" and you're done!

## Features

- **Boards**: List and get board details
- **Lists**: List and create board lists
- **Cards**: List, create, and update cards (including moving between lists)
- **Card Members**: Add, remove, and list members assigned to cards
- **Card Labels**: Add, remove, and list labels on cards
- **Board Members**: Add, remove, update, and invite board members
- **Organizations**: Manage workspaces, boards, and team members

## Available Tools

### Board Management
- `list_boards` - List all accessible boards
- `get_board` - Get board details
- `list_board_lists` - Get all lists on a board
- `list_board_cards` - Get all cards on a board
- `list_board_labels` - List all available labels on a board

### List Management
- `create_list` - Create a new list on a board

### Card Management
- `create_card` - Create a new card on a list
- `get_card` - Get card details
- `update_card` - Update card properties (name, description, move to list)

### Card Member Management
- `add_card_member` - Add a member to a card
- `remove_card_member` - Remove a member from a card
- `list_card_members` - List all members assigned to a card

### Card Label Management
- `add_card_label` - Add a label to a card
- `remove_card_label` - Remove a label from a card
- `list_card_labels` - List all labels on a card
- `filter_cards_by_label` - Filter cards on a board by label

### Board Member Management
- `list_board_members` - List all board members with permissions
- `add_board_member` - Add an existing user to a board
- `remove_board_member` - Remove a member from a board
- `update_board_member` - Update member permission level
- `invite_board_member` - Invite a new member via email

### Organization Management
- `list_organizations` - List all organizations/workspaces
- `get_organization` - Get organization details
- `list_organization_boards` - Get all boards in an organization
- `list_organization_members` - Get all organization members
- `add_organization_member` - Add a member to an organization
- `remove_organization_member` - Remove a member from an organization

## Development

### Setup

```bash
# Quick setup
./setup.sh

# Or manually
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Authentication

```bash
# Interactive (opens browser)
python -m trello_mcp_server.auth --interactive

# Manual (copy-paste token)
python -m trello_mcp_server.auth --manual

# Check status
python -m trello_mcp_server.auth --check
```

### Testing

```bash
# Run tests
python -m pytest

# Test organization tools
python test_organizations.py
```

## Documentation

- **docs/AUTHENTICATION.md** - Detailed authentication flows
- **docs/ORGANIZATIONS.md** - Organization management guide
- **docs/STARTUP_FLOW.md** - Server startup process
- **docs/FUTURE_FEATURES.md** - Planned features
- **CHANGELOG.md** - Version history

## Architecture

- **Language**: Python 3.8+
- **Protocol**: MCP with stdio transport
- **Authentication**: OAuth 1.0a with automatic token caching
- **Token Storage**: `~/.trello_mcp_token.json` (600 permissions)

## Security

- API keys stored in MCP configuration (safe to share within team)
- Tokens stored in home directory (never committed)
- Automatic file permissions (600) on token cache
- Tokens never expire unless manually revoked

## Support

- Trello API: https://developer.atlassian.com/cloud/trello/
- Get API Key: https://trello.com/power-ups/admin/new
- Manage Tokens: https://trello.com/my/account

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
git clone https://github.com/cargom98/gm-trello-mcp.git
cd gm-trello-mcp
./setup.sh
```

### Running Tests

```bash
python -m pytest
python test_auth.py
python test_organizations.py
```

### Releasing

See [RELEASING.md](RELEASING.md) for detailed release instructions.

Quick release:
```bash
./release.sh
```

## License

See LICENSE file for details.
