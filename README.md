# Trello MCP Server

A Model Context Protocol (MCP) server that integrates Trello with Kiro, enabling you to manage boards, lists, cards, and organizations directly from your development environment.

## Quick Start

### 1. Get API Key

Visit https://trello.com/power-ups/admin/new and create a Power-Up to get your API key (free, takes seconds).

### 2. Install as Kiro Power

This repo is designed to be installed as a Kiro power. The `mcp.json` file contains the configuration that will be automatically applied when you install the power.

### 3. Authenticate

On first use, the server automatically opens your browser to authorize access. Click "Allow" and you're done!

## Features

- **Boards**: List and get board details
- **Lists**: List and create board lists
- **Cards**: List, create, and update cards (including moving between lists)
- **Organizations**: Manage workspaces, boards, and team members

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

- **POWER.md** - Complete power documentation with workflows and troubleshooting
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

## License

See LICENSE file for details.
