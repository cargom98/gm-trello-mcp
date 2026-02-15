# Trello MCP Server

A Model Context Protocol (MCP) server for interacting with Trello boards, lists, and cards.

## Features

- List all boards
- Get board details
- List cards on a board
- Create new cards
- Update card details
- Move cards between lists

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

3. Get your Trello API credentials:

   **Getting your API Key:**
   - Go to <https://trello.com/app-key>
   - Log in to your Trello account if prompted
   - Your API Key will be displayed at the top of the page
   - Copy the key (it's a 32-character hexadecimal string)

   **Getting your Token:**
   - On the same page (<https://trello.com/app-key>), scroll down to the "Token" section
   - Click the "Token" link or "generate a Token" link
   - You'll be asked to authorize the application - click "Allow"
   - Copy the token that's generated (it's a 64-character hexadecimal string)
   - Keep this token secure - it provides access to your Trello account

   **Security Note:** Never commit your API key or token to version control. Always use environment variables or secure configuration management.

4. Set environment variables:

```bash
export TRELLO_API_KEY="your_api_key"
export TRELLO_TOKEN="your_token"
```

## Usage with Kiro

Add to your `.kiro/settings/mcp.json`:

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
