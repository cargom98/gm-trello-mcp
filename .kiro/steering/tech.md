# Technology Stack

## Language & Runtime
- Python 3.8+
- Async/await for MCP server implementation

## Core Dependencies
- `mcp>=1.0.0` - Model Context Protocol SDK
- `requests>=2.31.0` - HTTP client for Trello API calls

## Architecture
- MCP server using stdio transport
- OAuth 1.0a authentication with Trello API
- Local HTTP server for OAuth callback (port 8765)
- Token caching in `~/.trello_mcp_token.json` with 600 permissions

## Project Structure
- `trello_mcp_server/` - Main package
  - `server.py` - MCP server implementation, tool handlers, API client
  - `auth.py` - Standalone authentication CLI
  - `__main__.py` - Package entry point
- `docs/` - Detailed documentation
- Test files at root level

## Common Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Quick setup (runs above commands)
./setup.sh
```

### Development
```bash
# Run server (via MCP)
python -m trello_mcp_server

# Authenticate interactively
python -m trello_mcp_server.auth --interactive

# Authenticate manually
python -m trello_mcp_server.auth --manual

# Check auth status
python -m trello_mcp_server.auth --check

# Run tests
python -m pytest

# Test organization tools
python test_organizations.py
python test_organizations.py --org-id myteam
```

### MCP Configuration
Add to your MCP client's settings file:
```json
{
  "mcpServers": {
    "trello": {
      "command": "uvx",
      "args": ["trello-mcp-server"],
      "env": {
        "TRELLO_API_KEY": "your_api_key"
      }
    }
  }
}
```

## API Integration
- Base URL: `https://api.trello.com/1`
- Authentication: API key + OAuth token in query params
- Rate limits: 300 requests per 10 seconds per token
