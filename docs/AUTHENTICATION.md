# Trello MCP Server - Authentication Flow

## Overview

The Trello MCP Server uses OAuth 1.0a for authentication. This document describes the complete flow for generating and using authentication tokens.

## Prerequisites

- A Trello account
- Access to https://trello.com/app-key

## Authentication Flow

### Quick Start: Automatic Authentication (Easiest)

The fastest way to authenticate is using the automatic flow:

1. **Get your API key** from https://trello.com/app-key
2. **Use the `authorize_interactive` tool** in Kiro with your API key
3. **Your browser opens automatically** to the Trello authorization page
4. **Click "Allow"** in your browser
5. **Done!** The token is automatically captured and saved

```
Use authorize_interactive with:
- api_key: "your_api_key_from_trello"
```

The tool will:
- Open your default browser to Trello's authorization page
- Start a local server to capture the OAuth callback
- Automatically save the token when you click "Allow"
- Confirm successful authentication

### Manual Authentication Flow

If automatic authentication doesn't work (firewall, headless environment, etc.), use the manual flow:

### Step 1: Get Your API Key

1. Visit https://trello.com/app-key in your browser
2. Log in to your Trello account if prompted
3. Your API Key will be displayed at the top of the page
4. Copy the API key (32-character hexadecimal string)
5. Keep this key secure - it identifies your application

### Step 2: Generate Authorization URL (Manual Method)

Use the `get_auth_url` tool in Kiro:

```
Use the get_auth_url tool with:
- api_key: "your_api_key_from_step_1"
- app_name: "Trello MCP Server" (optional)
```

The tool will return a URL like:
```
https://trello.com/1/authorize?expiration=never&name=Trello%20MCP%20Server&scope=read,write&response_type=token&key=your_api_key
```

### Step 3: Authorize the Application

1. Copy the authorization URL from Step 2
2. Open it in your web browser
3. Review the permissions requested:
   - **Read access**: View your boards, lists, and cards
   - **Write access**: Create and modify boards, lists, and cards
4. Click "Allow" to authorize the application
5. Trello will display your token on the success page
6. Copy the token (64-character hexadecimal string)

### Step 4: Save Your Credentials

Use the `set_token` tool in Kiro:

```
Use the set_token tool with:
- api_key: "your_api_key_from_step_1"
- token: "your_token_from_step_3"
```

The tool will:
- Save your credentials to `~/.trello_mcp_token.json`
- Set secure file permissions (600 - owner read/write only)
- Confirm successful authentication

### Step 5: Verify Authentication

Use the `check_auth` tool to verify:

```
Use the check_auth tool (no parameters needed)
```

You should see:
```
✓ Authenticated with API key: e9a94d46...
```

### Step 6: Start Using Trello Tools

You can now use all Trello tools:
- `list_boards` - View your boards
- `create_card` - Create new cards
- `update_card` - Modify existing cards
- And more...

## Available Authentication Methods

### 1. Automatic Interactive (Recommended)
- **Tool**: `authorize_interactive`
- **Pros**: Fully automatic, no copy-paste needed
- **Cons**: Requires browser access, local server on port 8765
- **Best for**: Desktop users, interactive sessions

### 2. Manual URL Method
- **Tool**: `get_auth_url` + `set_token`
- **Pros**: Works in any environment, no local server needed
- **Cons**: Requires manual copy-paste of token
- **Best for**: Restricted environments, troubleshooting

### 3. Environment Variables
- **Setup**: Export `TRELLO_API_KEY` and `TRELLO_TOKEN`
- **Pros**: No tools needed, works for automation
- **Cons**: Manual token generation required first
- **Best for**: CI/CD, scripts, automated deployments

## Token Storage
- **Best for**: Restricted environments, troubleshooting

### 3. Environment Variables
- **Setup**: Export `TRELLO_API_KEY` and `TRELLO_TOKEN`
- **Pros**: No tools needed, works for automation
- **Cons**: Manual token generation required first
- **Best for**: CI/CD, scripts, automated deployments

### Location
Credentials are stored in: `~/.trello_mcp_token.json`

### Format
```json
{
  "api_key": "your_32_character_api_key",
  "token": "your_64_character_token"
}
```

### Security
- File permissions: 600 (owner read/write only)
- Not stored in version control (.gitignore)
- Not stored in mcp.json configuration
- Automatically loaded on server startup

## Token Storage

Tokens generated with `expiration=never` do not expire unless:
- You manually revoke them at https://trello.com/my/account
- You regenerate your API key
- Trello detects suspicious activity

## Token Expiration

If you need to regenerate your token:

1. Visit https://trello.com/my/account
2. Go to "Applications" section
3. Find "Trello MCP Server" (or your app name)
4. Click "Revoke" to invalidate the old token
5. Follow Steps 2-4 above to generate a new token

## Regenerating Tokens

### "Not authenticated" Error

**Cause**: No credentials found or invalid credentials

**Solution**:
1. Run `check_auth` to verify status
2. If not authenticated, follow Steps 1-4 above
3. Ensure `~/.trello_mcp_token.json` exists and has correct permissions

### "Invalid token" Error

**Cause**: Token has been revoked or API key changed

**Solution**:
1. Delete `~/.trello_mcp_token.json`
2. Follow Steps 1-4 to generate new credentials

### "Permission denied" Error

**Cause**: Token doesn't have required permissions

**Solution**:
1. Revoke the old token at https://trello.com/my/account
2. Generate a new token with correct scope (read,write)
3. Ensure you clicked "Allow" during authorization

## Security Best Practices

1. **Never commit credentials** - Keep API keys and tokens out of version control
2. **Use environment variables for CI/CD** - Don't hardcode credentials in scripts
3. **Rotate tokens periodically** - Generate new tokens every few months
4. **Revoke unused tokens** - Clean up old tokens at https://trello.com/my/account
5. **Monitor API usage** - Check for unexpected activity in your Trello account
6. **Use separate tokens per environment** - Different tokens for dev/staging/prod

## Alternative: Environment Variables

For CI/CD pipelines or automated environments:

```bash
export TRELLO_API_KEY="your_api_key"
export TRELLO_TOKEN="your_token"
```

The server will automatically use these if no cached token is found.

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Get API Key                                              │
│    https://trello.com/app-key                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Generate Auth URL                                        │
│    Tool: get_auth_url(api_key)                              │
│    Returns: Authorization URL                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Authorize in Browser                                     │
│    Visit URL → Review Permissions → Click "Allow"          │
│    Receive: Token                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Save Credentials                                         │
│    Tool: set_token(api_key, token)                          │
│    Saves to: ~/.trello_mcp_token.json                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Verify Authentication                                    │
│    Tool: check_auth()                                       │
│    Status: ✓ Authenticated                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Use Trello Tools                                         │
│    list_boards, create_card, update_card, etc.              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start Example

Here's a complete example conversation with Kiro:

```
You: Use get_auth_url with my API key: e9a94d46df7b6a1bb3bd0df25d125b47

Kiro: Visit this URL to authorize the app:
https://trello.com/1/authorize?expiration=never&name=Trello%20MCP%20Server&scope=read,write&response_type=token&key=e9a94d46df7b6a1bb3bd0df25d125b47

After authorizing, you'll receive a token. Use the 'set_token' tool to save it.

You: [Visit URL in browser, click Allow, copy token]
     Use set_token with api_key: e9a94d46df7b6a1bb3bd0df25d125b47 
     and token: ATTA1234567890abcdef...

Kiro: ✓ Credentials saved successfully! You can now use other Trello tools.

You: List my boards

Kiro: Your Trello Boards:
- Project Management (ID: 5f8a9b2c...)
- Personal Tasks (ID: 6a1b3c4d...)
- Team Roadmap (ID: 7b2c4d5e...)
```

## Support

For issues or questions:
- Trello API Documentation: https://developer.atlassian.com/cloud/trello/
- Trello API Key Management: https://trello.com/app-key
- Account Settings: https://trello.com/my/account
