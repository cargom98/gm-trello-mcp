---
name: "trello"
displayName: "Trello"
description: "Manage Trello boards, lists, cards, and organizations with full read/write access. Create and update cards, move items between lists, and manage team workspaces."
keywords: ["trello", "boards", "cards", "project-management", "kanban", "tasks", "workflow"]
author: "Carlos Gomez"
version: "1.0.0"
---

# Trello Power

Integrate Trello directly into your Kiro workflow. Manage boards, lists, cards, and team workspaces without leaving your development environment.

## What You Can Do

- List and access all your Trello boards
- Create, update, and move cards between lists
- Manage board lists and their organization
- Handle organization/workspace membership and boards
- Automatic OAuth authentication with secure token caching

The power uses Trello's official API with OAuth 1.0a authentication. Tokens are cached locally and never expire unless manually revoked.

## Getting Started

### Prerequisites

- Python 3.8+
- Trello account
- Trello API key (free from Trello)

### Setup

1. **Get your Trello API key**
   
   Visit https://trello.com/power-ups/admin/new to create a Power-Up. You'll receive your API key immediately (free, takes seconds).

2. **Configure the power**
   
   When you install this power, update the `TRELLO_API_KEY` placeholder in the MCP configuration with your actual API key.

3. **Authenticate**
   
   On first use, the server automatically opens your browser to authorize access. Click "Allow" and the token is saved securely to `~/.trello_mcp_token.json`. That's it!

### Alternative: Manual Authentication

If automatic authentication doesn't work:

```bash
# Interactive (opens browser)
python -m trello_mcp_server.auth --interactive

# Manual (copy-paste token)
python -m trello_mcp_server.auth --manual

# Check status
python -m trello_mcp_server.auth --check
```

## Available Tools

### Boards
- `list_boards` - List all accessible boards
- `get_board` - Get board details

### Lists
- `list_board_lists` - Get all lists on a board
- `create_list` - Create a new list

### Cards
- `list_board_cards` - Get all cards on a board
- `get_card` - Get card details
- `create_card` - Create a new card
- `update_card` - Update card properties (name, description, list, position)

### Organizations/Workspaces
- `list_organizations` - List all organizations you belong to
- `get_organization` - Get organization details
- `list_organization_boards` - Get all boards in an organization
- `list_organization_members` - Get all members of an organization
- `add_organization_member` - Add a member to an organization
- `remove_organization_member` - Remove a member from an organization

## Common Workflows

### Workflow 1: Create and Track a Task

**Goal:** Create a new card and move it through your workflow.

1. Get your board: `list_boards`
2. Find the right list: `list_board_lists` with board_id
3. Create the card: `create_card` with list_id, name, and description
4. Move to done: `update_card` with card_id and new list_id

**Example:**
```
list_boards → board_id: "abc123"
list_board_lists(board_id: "abc123") → list_id: "xyz789"
create_card(list_id: "xyz789", name: "Fix login bug")
update_card(card_id: "card123", list_id: "done_list_id")
```

### Workflow 2: Organize Your Boards

**Goal:** View all boards and their structure.

1. List all boards: `list_boards`
2. For each board, get lists: `list_board_lists`
3. For each list, get cards: `list_board_cards`

### Workflow 3: Manage Team Access

**Goal:** Add a new team member to your workspace.

1. Find your workspace: `list_organizations`
2. Add the member: `add_organization_member` with org_id and email
3. Verify: `list_organization_members`

### Workflow 4: Create Board Structure

**Goal:** Set up lists for a new project.

1. Get board ID: `list_boards`
2. Create lists: `create_list` for "To Do", "In Progress", "Done"
3. Verify: `list_board_lists`

## Troubleshooting

### Authentication Issues

**Problem:** "Not authenticated" error

**Solution:**
1. Check token exists: `ls -la ~/.trello_mcp_token.json`
2. Re-authenticate: `python -m trello_mcp_server.auth --interactive`
3. Verify API key in MCP configuration
4. Restart MCP server in Kiro

### Browser Won't Open

**Problem:** Automatic authentication doesn't open browser

**Solution:** Use manual authentication:
```bash
python -m trello_mcp_server.auth --manual
```
This provides a URL to visit and prompts for the token.

### Invalid IDs

**Problem:** "Invalid board/list/card ID" error

**Solution:** Always get IDs from list operations first:
- Board IDs: `list_boards`
- List IDs: `list_board_lists`
- Card IDs: `list_board_cards`

### Rate Limits

**Problem:** "Rate limit exceeded" error

**Solution:** Wait a few minutes. Trello allows 300 requests per 10 seconds per token. Batch operations when possible.

### Port Already in Use

**Problem:** Port 8765 in use during authentication

**Solution:** Use manual authentication or wait and retry.

## Tips & Best Practices

- Always get IDs from list operations rather than hardcoding them
- Use descriptive card names and descriptions
- Cache board and list IDs to reduce API calls
- Tokens never expire unless manually revoked at https://trello.com/my/account
- API keys are safe to share within your team
- Token cache file has restricted permissions (600) for security

## Configuration Details

**Required Placeholder:**
- `YOUR_TRELLO_API_KEY` - Get from https://trello.com/power-ups/admin/new

**Token Storage:**
- Location: `~/.trello_mcp_token.json`
- Permissions: 600 (owner read/write only)
- Lifetime: Never expires unless manually revoked

**Security:**
- API keys in mcp.json (safe to share)
- Tokens in home directory (never commit)
- Revoke at https://trello.com/my/account if needed
