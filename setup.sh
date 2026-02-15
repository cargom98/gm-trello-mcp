#!/bin/bash
# Setup script for Trello MCP Server

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add the server to your Kiro MCP configuration (.kiro/settings/mcp.json)"
echo "2. Use the 'get_auth_url' tool with your API key from: https://trello.com/app-key"
echo "3. Visit the generated URL to authorize and get your token"
echo "4. Use the 'set_token' tool to save your credentials"
echo ""
echo "Alternatively, you can set environment variables:"
echo "   export TRELLO_API_KEY='your_api_key'"
echo "   export TRELLO_TOKEN='your_token'"
