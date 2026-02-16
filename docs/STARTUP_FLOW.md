# Trello MCP Server - Startup Authentication Flow

## Overview

The Trello MCP server now requires authentication before starting and automatically handles the OAuth flow on first startup.

## Startup Sequence

### First Time Startup (No Cached Token)

```
1. Server starts
   ↓
2. Checks for cached token in ~/.trello_mcp_token.json
   ↓
3. No token found → Checks for TRELLO_API_KEY environment variable
   ↓
4. API key found → Starts automatic authentication
   ↓
5. Opens default browser to Trello authorization page
   ↓
6. Starts local HTTP server on port 8765 for OAuth callback
   ↓
7. User clicks "Allow" in browser
   ↓
8. JavaScript extracts token from URL fragment
   ↓
9. Token sent to local server via fetch request
   ↓
10. Server saves token to ~/.trello_mcp_token.json (chmod 600)
    ↓
11. Local HTTP server shuts down
    ↓
12. MCP server starts successfully
```

### Subsequent Startups (Token Cached)

```
1. Server starts
   ↓
2. Checks for cached token in ~/.trello_mcp_token.json
   ↓
3. Token found → Loads credentials
   ↓
4. MCP server starts successfully
```

### Startup Without API Key

```
1. Server starts
   ↓
2. Checks for cached token in ~/.trello_mcp_token.json
   ↓
3. No token found → Checks for TRELLO_API_KEY environment variable
   ↓
4. No API key found → Server exits with error message
   ↓
5. Error message instructs user to set TRELLO_API_KEY
```

## Configuration

### Minimal Configuration (Recommended)

`.kiro/settings/mcp.json`:
```json
{
  "mcpServers": {
    "trello": {
      "command": "python",
      "args": ["-m", "trello_mcp_server"],
      "env": {
        "TRELLO_API_KEY": "your_api_key"
      }
    }
  }
}
```

### With Pre-existing Token (CI/CD)

```json
{
  "mcpServers": {
    "trello": {
      "command": "python",
      "args": ["-m", "trello_mcp_server"],
      "env": {
        "TRELLO_API_KEY": "your_api_key",
        "TRELLO_TOKEN": "your_token"
      }
    }
  }
}
```

## Authentication Priority

The server checks for credentials in this order:

1. **Environment variables** (TRELLO_TOKEN + TRELLO_API_KEY)
2. **Cached token file** (~/.trello_mcp_token.json)
3. **Automatic OAuth flow** (if TRELLO_API_KEY is set but no token)
4. **Exit with error** (if no API key found)

## Security Model

### What's Stored Where

| Credential | Location | Version Control | Permissions |
|------------|----------|-----------------|-------------|
| API Key | mcp.json or env var | Optional (safe to commit) | 644 (readable) |
| Token | ~/.trello_mcp_token.json | Never | 600 (owner only) |

### Why This Design?

- **API Key in mcp.json**: Safe to share within a team, identifies the application
- **Token in home directory**: User-specific, grants access to user's Trello account
- **Automatic generation**: Reduces manual steps and potential for errors
- **Cached token**: Avoids repeated OAuth flows

## Manual Authentication

If automatic authentication fails, users can authenticate manually:

```bash
# Interactive (opens browser)
python -m trello_mcp_server.auth --interactive

# Manual (copy-paste token)
python -m trello_mcp_server.auth --manual

# Check status
python -m trello_mcp_server.auth --check

# Set directly
python -m trello_mcp_server.auth --set-key KEY --set-token TOKEN
```

## Error Handling

### No API Key

```
AUTHENTICATION REQUIRED
═══════════════════════════════════════════════════════════════════

TRELLO_API_KEY environment variable not set.

Please set your API key:
  export TRELLO_API_KEY='your_api_key'

Get your API key from: https://trello.com/app-key
═══════════════════════════════════════════════════════════════════
```

### Authentication Timeout

```
AUTHENTICATION FAILED
═══════════════════════════════════════════════════════════════════
Authorization timed out or was cancelled.

Please try again or set credentials manually:
  export TRELLO_API_KEY='your_api_key'
  export TRELLO_TOKEN='your_token'
═══════════════════════════════════════════════════════════════════
```

### Successful Authentication

```
═══════════════════════════════════════════════════════════════════
✓ AUTHENTICATION SUCCESSFUL!
═══════════════════════════════════════════════════════════════════
Credentials saved to: /Users/username/.trello_mcp_token.json

Starting Trello MCP server (authenticated with key: e9a94d46...)
```

## OAuth Flow Details

### Local Callback Server

- **Port**: 8765 (default, configurable)
- **Lifetime**: Only during authentication (not persistent)
- **Endpoints**:
  - `GET /` - Serves HTML with JavaScript to extract token
  - `GET /callback?token=...` - Receives token from JavaScript

### Browser Interaction

1. Server generates OAuth URL with `return_url=http://localhost:8765`
2. Opens URL in default browser using `webbrowser.open()`
3. User sees Trello authorization page
4. User clicks "Allow"
5. Trello redirects to `http://localhost:8765#token=...`
6. JavaScript extracts token from URL fragment
7. JavaScript sends token to `/callback` endpoint
8. Server receives token and shuts down

### Timeout

- **Default**: 120 seconds (2 minutes)
- **Behavior**: If user doesn't authorize within timeout, server exits with error
- **Recovery**: User can restart server to try again

## Comparison with Previous Design

### Before (Tool-based Authentication)

```
1. Server starts (no auth check)
2. User calls authorize_interactive tool
3. Browser opens
4. Token captured
5. User can now use other tools
```

**Issues:**
- Server runs without authentication
- Tools fail with confusing errors if not authenticated
- Extra step for users

### After (Startup Authentication)

```
1. Server checks auth before starting
2. If no auth, automatically opens browser
3. Token captured
4. Server starts fully authenticated
```

**Benefits:**
- Server never runs unauthenticated
- Single startup flow
- Better user experience
- Clearer error messages

## Testing

### Test First Startup

```bash
# Remove cached token
rm ~/.trello_mcp_token.json

# Set API key
export TRELLO_API_KEY="your_api_key"

# Start server (should open browser)
python -m trello_mcp_server
```

### Test Cached Token

```bash
# Start server (should use cached token)
python -m trello_mcp_server
```

### Test No API Key

```bash
# Remove cached token
rm ~/.trello_mcp_token.json

# Unset API key
unset TRELLO_API_KEY

# Start server (should exit with error)
python -m trello_mcp_server
```
