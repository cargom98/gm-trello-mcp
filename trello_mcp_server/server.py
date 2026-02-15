"""Trello MCP Server implementation."""
import os
import logging
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trello-mcp-server")

# Trello API configuration
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_API_BASE = "https://api.trello.com/1"

app = Server("trello-mcp-server")

def make_trello_request(method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
    """Make a request to the Trello API."""
    if not TRELLO_API_KEY or not TRELLO_TOKEN:
        raise ValueError("TRELLO_API_KEY and TRELLO_TOKEN environment variables must be set")
    
    url = f"{TRELLO_API_BASE}{endpoint}"
    auth_params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    
    if params:
        auth_params.update(params)
    
    response = requests.request(method, url, params=auth_params, json=data)
    response.raise_for_status()
    return response.json()

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Trello tools."""
    return [
        Tool(
            name="list_boards",
            description="List all boards accessible to the authenticated user",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="get_board",
            description="Get details about a specific board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board"
                    }
                },
                "required": ["board_id"]
            }
        ),
        Tool(
            name="list_board_lists",
            description="Get all lists on a board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board"
                    }
                },
                "required": ["board_id"]
            }
        ),
        Tool(
            name="list_board_cards",
            description="Get all cards on a board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board"
                    }
                },
                "required": ["board_id"]
            }
        ),
        Tool(
            name="create_card",
            description="Create a new card on a list",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "The ID of the list to create the card in"
                    },
                    "name": {
                        "type": "string",
                        "description": "The name/title of the card"
                    },
                    "desc": {
                        "type": "string",
                        "description": "The description of the card (optional)"
                    }
                },
                "required": ["list_id", "name"]
            }
        ),
        Tool(
            name="update_card",
            description="Update a card's properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "The ID of the card to update"
                    },
                    "name": {
                        "type": "string",
                        "description": "New name for the card (optional)"
                    },
                    "desc": {
                        "type": "string",
                        "description": "New description for the card (optional)"
                    },
                    "list_id": {
                        "type": "string",
                        "description": "Move card to this list ID (optional)"
                    }
                },
                "required": ["card_id"]
            }
        ),
        Tool(
            name="get_card",
            description="Get details about a specific card",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "The ID of the card"
                    }
                },
                "required": ["card_id"]
            }
        ),
        Tool(
            name="create_list",
            description="Create a new list on a board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board to create the list on"
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the list"
                    },
                    "pos": {
                        "type": "string",
                        "description": "Position of the list: 'top', 'bottom', or a positive number (optional, defaults to 'bottom')"
                    }
                },
                "required": ["board_id", "name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "list_boards":
            boards = make_trello_request("GET", "/members/me/boards")
            result = "\n".join([f"- {board['name']} (ID: {board['id']})" for board in boards])
            return [TextContent(type="text", text=f"Your Trello Boards:\n{result}")]
        
        elif name == "get_board":
            board = make_trello_request("GET", f"/boards/{arguments['board_id']}")
            return [TextContent(
                type="text",
                text=f"Board: {board['name']}\nID: {board['id']}\nURL: {board['url']}\nDescription: {board.get('desc', 'N/A')}"
            )]
        
        elif name == "list_board_lists":
            lists = make_trello_request("GET", f"/boards/{arguments['board_id']}/lists")
            result = "\n".join([f"- {lst['name']} (ID: {lst['id']})" for lst in lists])
            return [TextContent(type="text", text=f"Lists on board:\n{result}")]
        
        elif name == "list_board_cards":
            cards = make_trello_request("GET", f"/boards/{arguments['board_id']}/cards")
            result = "\n".join([f"- {card['name']} (ID: {card['id']}, List: {card['idList']})" for card in cards])
            return [TextContent(type="text", text=f"Cards on board:\n{result}")]
        
        elif name == "create_card":
            data = {
                "idList": arguments["list_id"],
                "name": arguments["name"]
            }
            if "desc" in arguments:
                data["desc"] = arguments["desc"]
            
            card = make_trello_request("POST", "/cards", data=data)
            return [TextContent(
                type="text",
                text=f"Created card: {card['name']}\nID: {card['id']}\nURL: {card['url']}"
            )]
        
        elif name == "update_card":
            data = {}
            if "name" in arguments:
                data["name"] = arguments["name"]
            if "desc" in arguments:
                data["desc"] = arguments["desc"]
            if "list_id" in arguments:
                data["idList"] = arguments["list_id"]
            
            card = make_trello_request("PUT", f"/cards/{arguments['card_id']}", data=data)
            return [TextContent(
                type="text",
                text=f"Updated card: {card['name']}\nID: {card['id']}\nURL: {card['url']}"
            )]
        
        elif name == "get_card":
            card = make_trello_request("GET", f"/cards/{arguments['card_id']}")
            return [TextContent(
                type="text",
                text=f"Card: {card['name']}\nID: {card['id']}\nDescription: {card.get('desc', 'N/A')}\nList ID: {card['idList']}\nURL: {card['url']}"
            )]
        
        elif name == "create_list":
            data = {
                "name": arguments["name"],
                "idBoard": arguments["board_id"]
            }
            if "pos" in arguments:
                data["pos"] = arguments["pos"]
            
            lst = make_trello_request("POST", "/lists", data=data)
            return [TextContent(
                type="text",
                text=f"Created list: {lst['name']}\nID: {lst['id']}\nBoard ID: {lst['idBoard']}"
            )]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"Trello API error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )
