---
name: "trello"
displayName: "Trello"
description: "Manage Trello boards, lists, cards, and organizations with full read/write access. Create and update cards, move items between lists, and manage team workspaces."
keywords: ["trello", "boards", "cards", "project-management", "kanban"]
author: "Carlos Gomez"
---

# Trello

## Overview

This power provides complete integration with Trello's API, allowing you to manage boards, lists, cards, and organizations directly from Kiro. Whether you're tracking tasks, organizing projects, or managing team workflows, you can interact with Trello without leaving your development environment.

Key capabilities include:
- List and access all your Trello boards
- Create, update, and move cards between lists
- Manage board lists and their organization
- Handle organization/workspace membership and boards
- Automatic authentication with secure token caching

The power uses Trello's official API with OAuth authentication, ensuring secure access to your Trello data. Tokens are cached locally and never expire unless manually revoked, providing seamless access after initial setup.

## Onboarding

### Prerequisites

- Python 3.8 or higher
- Trello account
- Trello API key (free, obtained from Trello)

### Installation

1. **Get your Trello API key**
   
   Visit https://trello.com/app-key and copy your API key. This is free and takes just a few seconds.

2. **Install the Trello MCP server**
   
   The server is included in this workspace. Ensure you have the dependencies installed:
   
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure in Kiro**
   
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

### Authentication

The server requires a one-time authentication to get a permanent token. There are two methods:

#### Method 1: Automatic (Recommended)

The server will automatically open your browser on first startup:

1. Start Kiro with the MCP server configured
2. Browser opens automatically to Trello authorization page
3. Click "Allow" to authorize
4. Token is captured and saved automatically to `~/.trello_mcp_token.json`
5. Done! The server is ready to use

#### Method 2: Manual Authentication

If automatic authentication doesn't work (headless environment, browser issues):

```bash
# Interactive mode (opens browser)
python -m trello_mcp_server.auth --interactive

# Manual mode (copy-paste token)
python -m trello_mcp_server.auth --manual
```

After authentication, you can remove the API key from mcp.json if desired - the cached token will be used automatically.

### Verification

Check authentication status:

```bash
python -m trello_mcp_server.auth --check
```

## Common Workflows

### Workflow 1: List Your Boards

Get an overview of all accessible Trello boards.

**Steps:**
1. Use `list_boards` tool to see all boards
2. Note the board IDs for further operations

**Example:**
```
Use tool: list_boards
Result: Shows all boards with names and IDs
```

**Common Errors:**
- Error: "Not authenticated"
  - Cause: No token found
  - Solution: Run authentication flow (see Onboarding section)

### Workflow 2: Create and Manage Cards

Create new cards and update them as work progresses.

**Steps:**
1. Get board ID using `list_boards`
2. Get list ID using `list_board_lists` with the board ID
3. Create card using `create_card` with list ID and card name
4. Update card details or move to another list using `update_card`

**Example:**
```
1. list_boards → Get board ID
2. list_board_lists (board_id: "abc123") → Get list ID
3. create_card (list_id: "xyz789", name: "Fix login bug", desc: "Users can't login with email")
4. update_card (card_id: "card123", list_id: "done_list_id") → Move to Done
```

**Common Errors:**
- Error: "Invalid list ID"
  - Cause: List doesn't exist or wrong ID
  - Solution: Use `list_board_lists` to get correct list IDs

### Workflow 3: Organize Board Structure

Create and organize lists on your boards.

**Steps:**
1. Get board ID using `list_boards`
2. Create new list using `create_list` with board ID and list name
3. Optionally specify position (top, bottom, or number)

**Example:**
```
1. list_boards → Get board ID
2. create_list (board_id: "abc123", name: "In Review", pos: "bottom")
```

### Workflow 4: Manage Organization Boards

Work with team workspaces and their boards.

**Steps:**
1. List organizations using `list_organizations`
2. Get organization boards using `list_organization_boards`
3. Manage members with `add_organization_member` or `remove_organization_member`

**Example:**
```
1. list_organizations → Get org ID
2. list_organization_boards (org_id: "myteam") → See all team boards
3. add_organization_member (org_id: "myteam", email: "colleague@example.com")
```

## Troubleshooting

### MCP Server Connection Issues

**Problem:** MCP server won't start or connect

**Symptoms:**
- Error: "Connection refused"
- Server not responding
- No tools available

**Solutions:**
1. Verify Python installation: `python --version` (should be 3.8+)
2. Check dependencies are installed: `pip install -r requirements.txt`
3. Verify API key is set in mcp.json
4. Check authentication status: `python -m trello_mcp_server.auth --check`
5. Review server logs in Kiro's MCP panel
6. Restart Kiro and reconnect the MCP server

### Authentication Errors

**Error:** "Not authenticated"

**Cause:** No valid token found

**Solution:**
1. Check if token file exists: `ls -la ~/.trello_mcp_token.json`
2. If missing, run authentication: `python -m trello_mcp_server.auth --interactive`
3. Verify API key is correct in mcp.json
4. Restart the MCP server after authentication

### Browser Doesn't Open During Authentication

**Cause:** No default browser configured or headless environment

**Solution:**
Use manual authentication:
```bash
python -m trello_mcp_server.auth --manual
```
This will provide a URL to visit manually and prompt for the token.

### Port Already in Use

**Cause:** Port 8765 is already in use during OAuth callback

**Solution:**
1. The authentication will timeout and you can retry
2. Or use manual authentication: `python -m trello_mcp_server.auth --manual`
3. Or specify different port: `python -m trello_mcp_server.auth --interactive --port 8766`

### API Rate Limits

**Error:** "Rate limit exceeded"

**Cause:** Too many API requests in short time

**Solution:**
1. Wait a few minutes before retrying
2. Trello's rate limits are generous (300 requests per 10 seconds per token)
3. Batch operations when possible

### Invalid IDs

**Error:** "Invalid board/list/card ID"

**Cause:** Using wrong ID or ID from different account

**Solution:**
1. Always get IDs from list operations first
2. Board IDs: Use `list_boards`
3. List IDs: Use `list_board_lists`
4. Card IDs: Use `list_board_cards`
5. Verify you have access to the resource

## Best Practices

- Always use `list_boards` first to get current board IDs rather than hardcoding them
- Use descriptive card names and descriptions for better organization
- Leverage list movement to track card progress through workflows
- Cache board and list IDs in your workflow to reduce API calls
- Use organization tools for team collaboration and board management
- Check authentication status before long operations
- Keep your API key secure - never commit it to version control
- Token cache file (`~/.trello_mcp_token.json`) has restricted permissions (600) for security

## MCP Config Placeholders

**IMPORTANT:** Before using this power, replace the following placeholder in `mcp.json` with your actual value:

- **`YOUR_TRELLO_API_KEY`**: Your Trello API key for accessing the Trello API.
  - **How to get it:**
    1. Go to https://trello.com/app-key
    2. Log in to your Trello account if prompted
    3. Copy the API key shown at the top of the page
    4. Replace `YOUR_TRELLO_API_KEY` in mcp.json with your actual key

**After replacing the placeholder, your mcp.json should look like:**
```json
{
  "mcpServers": {
    "trello": {
      "command": "python",
      "args": ["-m", "trello_mcp_server"],
      "env": {
        "TRELLO_API_KEY": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
      }
    }
  }
}
```

## Configuration

**Environment Variables:**
- `TRELLO_API_KEY`: Your Trello API key (required for initial setup)
- `TRELLO_TOKEN`: Optional - can be set manually, but automatic authentication is recommended

**Token Storage:**
- Location: `~/.trello_mcp_token.json`
- Permissions: 600 (owner read/write only)
- Contains: API key and OAuth token
- Lifetime: Never expires unless manually revoked

**Security Notes:**
- API keys can be stored in mcp.json (safe to share within your team)
- Tokens are stored separately in home directory (never commit to version control)
- Token file has restricted permissions automatically
- Revoke tokens at https://trello.com/my/account if needed

---

**Package:** `trello_mcp_server` (local Python module)
**MCP Server:** trello
