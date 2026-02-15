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
echo "1. Get your Trello credentials from: https://trello.com/app-key"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Set your environment variables:"
echo "   export TRELLO_API_KEY='your_api_key'"
echo "   export TRELLO_TOKEN='your_token'"
echo "4. Test the server: python -m trello_mcp_server"
