"""Trello MCP Server implementation."""
import os
import json
import logging
import socket
import webbrowser
from pathlib import Path
from typing import Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trello-mcp-server")

# Trello API configuration
TRELLO_API_BASE = "https://api.trello.com/1"
TOKEN_CACHE_FILE = Path.home() / ".trello_mcp_token.json"

app = Server("trello-mcp-server")

# Global variable to store token from callback
_callback_token = None
_callback_event = None


class ReuseAddrHTTPServer(HTTPServer):
    """HTTPServer that allows address reuse."""
    allow_reuse_address = True


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Trello."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        """Handle both initial request and callback with token."""
        global _callback_token, _callback_event

        parsed = urlparse(self.path)

        # Check if token is in query params (from JavaScript callback)
        params = parse_qs(parsed.query)
        if 'token' in params:
            _callback_token = params['token'][0]
            if _callback_event:
                _callback_event.set()

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>Trello Authorization - Success</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h2 style="color: #0079bf;">✓ Authorization Successful!</h2>
                <p>Your Trello token has been received and saved.</p>
                <p>You can close this window and return to Kiro.</p>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">The Trello MCP server is now ready to use.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return

        # Initial request - send HTML to extract token from URL fragment
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
        <html>
        <head><title>Trello Authorization</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h2 style="color: #0079bf;">Processing authorization...</h2>
            <p>Please wait while we capture your token...</p>
            <script>
                // Extract token from URL fragment (Trello redirects with #token=...)
                const hash = window.location.hash.substring(1);
                const params = new URLSearchParams(hash);
                const token = params.get('token');

                if (token) {
                    // Send token to server via query param
                    fetch('/?token=' + encodeURIComponent(token))
                        .then(response => response.text())
                        .then(html => {
                            document.open();
                            document.write(html);
                            document.close();
                        })
                        .catch(err => {
                            document.body.innerHTML = '<h2 style="color: #c9372c;">✗ Error</h2><p>Failed to send token to server: ' + err.message + '</p>';
                        });
                } else {
                    document.body.innerHTML = '<h2 style="color: #c9372c;">✗ No Token Found</h2><p>No token was found in the URL. Please try the authorization process again.</p>';
                }
            </script>
        </body>
        </html>
        """
        self.wfile.write(html.encode())




class TrelloAuth:
    """Manage Trello authentication."""
    
    def __init__(self):
        self.api_key = os.getenv("TRELLO_API_KEY")
        self.token = os.getenv("TRELLO_TOKEN")
        # Only use env token if it's not empty
        if not self.token:
            self._load_cached_token()
    
    def _load_cached_token(self):
        """Load token from cache file if available."""
        if not self.token and TOKEN_CACHE_FILE.exists():
            try:
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    if not self.api_key:
                        self.api_key = data.get('api_key')
                    logger.info("Loaded cached Trello token")
            except Exception as e:
                logger.warning(f"Failed to load cached token: {e}")
    
    def _save_token(self, api_key: str, token: str):
        """Save token to cache file."""
        try:
            with open(TOKEN_CACHE_FILE, 'w') as f:
                json.dump({'api_key': api_key, 'token': token}, f)
            TOKEN_CACHE_FILE.chmod(0o600)  # Secure file permissions
            logger.info("Saved Trello token to cache")
        except Exception as e:
            logger.warning(f"Failed to save token: {e}")
    
    def set_credentials(self, api_key: str, token: str):
        """Set and cache credentials."""
        self.api_key = api_key
        self.token = token
        self._save_token(api_key, token)
    
    def get_auth_url(self, api_key: str, app_name: str = "Trello MCP Server", return_url: str = None) -> str:
        """Generate authorization URL for getting a token."""
        if return_url:
            return (
                f"https://trello.com/1/authorize?"
                f"expiration=never&"
                f"scope=read,write,account&"
                f"response_type=token&"
                f"return_url={return_url}&"
                f"key={api_key}"
            )
        else:
            return (
                f"https://trello.com/1/authorize?"
                f"expiration=never&"
                f"scope=read,write,account&"
                f"response_type=token&"
                f"key={api_key}"
            )
    
    def authorize_interactive(self, api_key: str, app_name: str = "Trello MCP Server", port: int = 8765) -> Optional[str]:
        """Start OAuth flow with automatic browser opening and token capture."""
        global _callback_token, _callback_event
        
        _callback_token = None
        _callback_event = threading.Event()
        
        server = None
        try:
            # Start local server
            logger.info(f"Starting local OAuth callback server on port {port}...")
            server = ReuseAddrHTTPServer(('localhost', port), OAuthCallbackHandler)
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            logger.info("OAuth callback server started successfully")
            
            # Generate auth URL with callback
            return_url = f"http://localhost:{port}"
            auth_url = self.get_auth_url(api_key, app_name, return_url)
            
            # Open browser
            logger.info(f"Authorization URL: {auth_url}")
            logger.info("Attempting to open browser...")
            
            try:
                webbrowser.open(auth_url)
                logger.info("Browser open command sent")
            except Exception as e:
                logger.error(f"Failed to open browser: {e}")
                logger.error(f"Please manually visit: {auth_url}")
            
            # Wait for callback (with timeout)
            logger.info("Waiting for authorization (timeout: 120 seconds)...")
            if _callback_event.wait(timeout=120):  # 2 minute timeout
                logger.info("Received authorization callback")
                token = _callback_token
                if token:
                    logger.info(f"Token received: {token[:16]}...")
                    self.set_credentials(api_key, token)
                    return token
                else:
                    logger.error("Callback received but no token found")
            else:
                logger.error("Authorization timeout - no response received within 120 seconds")
            
        except Exception as e:
            logger.error(f"Error during interactive authorization: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            # Always clean up the server
            if server:
                try:
                    server.shutdown()
                    server.server_close()
                    logger.info("OAuth callback server shut down")
                except Exception as e:
                    logger.warning(f"Error shutting down OAuth server: {e}")
        
        return None
    
    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        return bool(self.api_key and self.token)
    
    def get_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Get current credentials."""
        return self.api_key, self.token

auth = TrelloAuth()

def make_trello_request(method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
    """Make a request to the Trello API."""
    if not auth.is_authenticated():
        raise ValueError(
            "Not authenticated. Use 'authorize_interactive' for automatic authentication "
            "or 'get_auth_url' + 'set_token' for manual setup."
        )
    
    api_key, token = auth.get_credentials()
    url = f"{TRELLO_API_BASE}{endpoint}"
    auth_params = {
        "key": api_key,
        "token": token
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
        ),
        Tool(
            name="list_organizations",
            description="List all organizations/workspaces the authenticated user belongs to",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="get_organization",
            description="Get details about a specific organization/workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "The ID or name of the organization"
                    }
                },
                "required": ["org_id"]
            }
        ),
        Tool(
            name="list_organization_boards",
            description="Get all boards in an organization/workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "The ID or name of the organization"
                    }
                },
                "required": ["org_id"]
            }
        ),
        Tool(
            name="list_organization_members",
            description="Get all members of an organization/workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "The ID or name of the organization"
                    }
                },
                "required": ["org_id"]
            }
        ),
        Tool(
            name="add_organization_member",
            description="Add a member to an organization/workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "The ID or name of the organization"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address of the member to add"
                    },
                    "full_name": {
                        "type": "string",
                        "description": "Full name of the member (optional)"
                    },
                    "type": {
                        "type": "string",
                        "description": "Member type: 'normal' or 'admin' (optional, defaults to 'normal')"
                    }
                },
                "required": ["org_id", "email"]
            }
        ),
        Tool(
            name="remove_organization_member",
            description="Remove a member from an organization/workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {
                        "type": "string",
                        "description": "The ID or name of the organization"
                    },
                    "member_id": {
                        "type": "string",
                        "description": "The ID of the member to remove"
                    }
                },
                "required": ["org_id", "member_id"]
            }
        ),
        Tool(
            name="add_card_label",
            description="Add a label to a card",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "The ID of the card"
                    },
                    "label_id": {
                        "type": "string",
                        "description": "The ID of the label to add"
                    }
                },
                "required": ["card_id", "label_id"]
            }
        ),
        Tool(
            name="remove_card_label",
            description="Remove a label from a card",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "The ID of the card"
                    },
                    "label_id": {
                        "type": "string",
                        "description": "The ID of the label to remove"
                    }
                },
                "required": ["card_id", "label_id"]
            }
        ),
        Tool(
            name="list_card_labels",
            description="List all labels on a card",
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
            name="list_board_labels",
            description="List all available labels on a board",
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
            name="filter_cards_by_label",
            description="Filter cards on a board by a specific label",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board"
                    },
                    "label_id": {
                        "type": "string",
                        "description": "The ID of the label to filter by"
                    }
                },
                "required": ["board_id", "label_id"]
            }
        ),
        Tool(
            name="list_board_members",
            description="List all members of a board with their permission levels",
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
            name="add_board_member",
            description="Add an existing Trello user to a board with specified permission level",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board"
                    },
                    "member_id": {
                        "type": "string",
                        "description": "The ID of the member to add"
                    },
                    "type": {
                        "type": "string",
                        "description": "Permission level: 'admin', 'normal', or 'observer' (optional, defaults to 'normal')"
                    }
                },
                "required": ["board_id", "member_id"]
            }
        ),
        Tool(
            name="remove_board_member",
            description="Remove a member from a board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board"
                    },
                    "member_id": {
                        "type": "string",
                        "description": "The ID of the member to remove"
                    }
                },
                "required": ["board_id", "member_id"]
            }
        ),
        Tool(
            name="update_board_member",
            description="Update a member's permission level on a board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board"
                    },
                    "member_id": {
                        "type": "string",
                        "description": "The ID of the member to update"
                    },
                    "type": {
                        "type": "string",
                        "description": "New permission level: 'admin', 'normal', or 'observer'"
                    }
                },
                "required": ["board_id", "member_id", "type"]
            }
        ),
        Tool(
            name="invite_board_member",
            description="Invite a new member to a board via email address",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address of the person to invite"
                    },
                    "type": {
                        "type": "string",
                        "description": "Permission level: 'admin', 'normal', or 'observer' (optional, defaults to 'normal')"
                    }
                },
                "required": ["board_id", "email"]
            }
        ),
        Tool(
            name="add_card_member",
            description="Add a member to a card",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "The ID of the card"
                    },
                    "member_id": {
                        "type": "string",
                        "description": "The ID of the member to add"
                    }
                },
                "required": ["card_id", "member_id"]
            }
        ),
        Tool(
            name="remove_card_member",
            description="Remove a member from a card",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "The ID of the card"
                    },
                    "member_id": {
                        "type": "string",
                        "description": "The ID of the member to remove"
                    }
                },
                "required": ["card_id", "member_id"]
            }
        ),
        Tool(
            name="list_card_members",
            description="List all members assigned to a card",
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

        elif name == "list_board_members":
            board_id = arguments["board_id"]
            members = make_trello_request("GET", f"/boards/{board_id}/members")
            
            # Format response with member details (name, username, ID, permission)
            result = "\n".join([
                f"- {member['fullName']} (@{member['username']}, ID: {member['id']}, Permission: {member.get('memberType', 'normal')})"
                for member in members
            ])
            return [TextContent(type="text", text=f"Board Members:\n{result}")]

        elif name == "add_board_member":
            board_id = arguments["board_id"]
            member_id = arguments["member_id"]
            member_type = arguments.get("type", "normal")
            
            # Build query parameters with type
            params = {"type": member_type}
            
            # Call make_trello_request with PUT method
            result = make_trello_request("PUT", f"/boards/{board_id}/members/{member_id}", params=params)
            
            # Get member details for confirmation
            member = make_trello_request("GET", f"/members/{member_id}")
            
            return [TextContent(
                type="text",
                text=f"Added member to board: {member['fullName']} (@{member['username']})\nPermission: {member_type}"
            )]

        elif name == "remove_board_member":
            board_id = arguments["board_id"]
            member_id = arguments["member_id"]
            
            # Call make_trello_request with DELETE method
            make_trello_request("DELETE", f"/boards/{board_id}/members/{member_id}")
            
            return [TextContent(
                type="text",
                text=f"Removed member {member_id} from board"
            )]

        elif name == "update_board_member":
            board_id = arguments["board_id"]
            member_id = arguments["member_id"]
            member_type = arguments["type"]
            
            # Validate type is one of: "admin", "normal", "observer"
            valid_permissions = ["admin", "normal", "observer"]
            if member_type not in valid_permissions:
                return [TextContent(
                    type="text",
                    text=f"Error: Invalid permission type. Must be one of: {', '.join(valid_permissions)}"
                )]
            
            # Build query parameters with type
            params = {"type": member_type}
            
            # Call make_trello_request with PUT method
            make_trello_request("PUT", f"/boards/{board_id}/members/{member_id}", params=params)
            
            # Get member details for confirmation
            member = make_trello_request("GET", f"/members/{member_id}")
            
            return [TextContent(
                type="text",
                text=f"Updated member permission: {member['fullName']} (@{member['username']})\nNew permission: {member_type}"
            )]

        elif name == "invite_board_member":
            board_id = arguments["board_id"]
            email = arguments["email"]
            member_type = arguments.get("type", "normal")
            
            # Build query parameters with email and type
            params = {"email": email, "type": member_type}
            
            # Call make_trello_request with PUT method
            make_trello_request("PUT", f"/boards/{board_id}/members", params=params)
            
            return [TextContent(
                type="text",
                text=f"Invited {email} to board\nPermission: {member_type}"
            )]

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

        elif name == "list_organizations":
            orgs = make_trello_request("GET", "/members/me/organizations")
            result = "\n".join([f"- {org['displayName']} (ID: {org['id']}, Name: {org['name']})" for org in orgs])
            return [TextContent(type="text", text=f"Your Organizations/Workspaces:\n{result}")]

        elif name == "get_organization":
            org = make_trello_request("GET", f"/organizations/{arguments['org_id']}")
            return [TextContent(
                type="text",
                text=f"Organization: {org['displayName']}\nID: {org['id']}\nName: {org['name']}\nDescription: {org.get('desc', 'N/A')}\nURL: {org['url']}\nWebsite: {org.get('website', 'N/A')}"
            )]

        elif name == "list_organization_boards":
            boards = make_trello_request("GET", f"/organizations/{arguments['org_id']}/boards")
            result = "\n".join([f"- {board['name']} (ID: {board['id']})" for board in boards])
            return [TextContent(type="text", text=f"Boards in organization:\n{result}")]

        elif name == "list_organization_members":
            members = make_trello_request("GET", f"/organizations/{arguments['org_id']}/members")
            result = "\n".join([f"- {member['fullName']} (@{member['username']}, ID: {member['id']})" for member in members])
            return [TextContent(type="text", text=f"Members in organization:\n{result}")]

        elif name == "add_organization_member":
            data = {
                "email": arguments["email"]
            }
            if "full_name" in arguments:
                data["fullName"] = arguments["full_name"]
            if "type" in arguments:
                data["type"] = arguments["type"]

            member = make_trello_request("PUT", f"/organizations/{arguments['org_id']}/members", data=data)
            return [TextContent(
                type="text",
                text=f"Added member to organization: {member.get('fullName', arguments['email'])}"
            )]

        elif name == "remove_organization_member":
            make_trello_request("DELETE", f"/organizations/{arguments['org_id']}/members/{arguments['member_id']}")
            return [TextContent(
                type="text",
                text=f"Removed member {arguments['member_id']} from organization"
            )]

        elif name == "add_card_label":
            data = {"value": arguments["label_id"]}
            result = make_trello_request("POST", f"/cards/{arguments['card_id']}/idLabels", data=data)
            
            # Get card details to include in response
            card = make_trello_request("GET", f"/cards/{arguments['card_id']}")
            
            # Find the label details from the card's labels
            label_info = None
            for label in card.get('labels', []):
                if label['id'] == arguments['label_id']:
                    label_info = label
                    break
            
            if label_info:
                label_name = label_info.get('name', 'Unnamed')
                label_color = label_info.get('color', 'none')
                return [TextContent(
                    type="text",
                    text=f"Added label to card: {card['name']}\nLabel: {label_name} ({label_color})\nCard ID: {card['id']}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Added label to card: {card['name']}\nCard ID: {card['id']}"
                )]

        elif name == "remove_card_label":
            make_trello_request("DELETE", f"/cards/{arguments['card_id']}/idLabels/{arguments['label_id']}")
            return [TextContent(
                type="text",
                text=f"Removed label from card\nCard ID: {arguments['card_id']}\nLabel ID: {arguments['label_id']}"
            )]

        elif name == "list_card_labels":
            labels = make_trello_request("GET", f"/cards/{arguments['card_id']}/labels")
            
            # Handle empty label list case
            if not labels:
                return [TextContent(
                    type="text",
                    text="Labels on card:\n(No labels)"
                )]
            
            # Format response as list of labels with name, color, and ID
            result = "\n".join([
                f"- {label.get('name', 'Unnamed')} (Color: {label.get('color', 'none')}, ID: {label['id']})"
                for label in labels
            ])
            return [TextContent(type="text", text=f"Labels on card:\n{result}")]

        elif name == "list_board_labels":
            labels = make_trello_request("GET", f"/boards/{arguments['board_id']}/labels")
            
            # Format response as list of available labels with name, color, and ID
            result = "\n".join([
                f"- {label.get('name', 'Unnamed')} (Color: {label.get('color', 'none')}, ID: {label['id']})"
                for label in labels
            ])
            return [TextContent(type="text", text=f"Available labels on board:\n{result}")]

        elif name == "filter_cards_by_label":
            # Extract board_id and label_id from arguments
            board_id = arguments['board_id']
            label_id = arguments['label_id']
            
            # Call make_trello_request() with GET method to /boards/{board_id}/cards
            cards = make_trello_request("GET", f"/boards/{board_id}/cards")
            
            # Filter cards by checking if label_id is in card's idLabels array
            filtered_cards = [card for card in cards if label_id in card.get('idLabels', [])]
            
            # Handle empty results case
            if not filtered_cards:
                # Get label name for better user experience
                labels = make_trello_request("GET", f"/boards/{board_id}/labels")
                label_name = "Unknown"
                for label in labels:
                    if label['id'] == label_id:
                        label_name = label.get('name', 'Unnamed')
                        break
                
                return [TextContent(
                    type="text",
                    text=f"Cards with label {label_name}:\n(No cards found)"
                )]
            
            # Get label name for the response
            label_name = "Unknown"
            if filtered_cards:
                # Get label details from the first card's labels
                for label in filtered_cards[0].get('labels', []):
                    if label['id'] == label_id:
                        label_name = label.get('name', 'Unnamed')
                        break
            
            # Format response as list of cards with name, ID, and list ID
            result = "\n".join([
                f"- {card['name']} (ID: {card['id']}, List: {card['idList']})"
                for card in filtered_cards
            ])
            return [TextContent(type="text", text=f"Cards with label {label_name}:\n{result}")]

        elif name == "add_card_member":
            data = {"value": arguments["member_id"]}
            make_trello_request("POST", f"/cards/{arguments['card_id']}/idMembers", data=data)
            return [TextContent(
                type="text",
                text=f"Added member {arguments['member_id']} to card {arguments['card_id']}"
            )]

        elif name == "remove_card_member":
            make_trello_request("DELETE", f"/cards/{arguments['card_id']}/idMembers/{arguments['member_id']}")
            return [TextContent(
                type="text",
                text=f"Removed member {arguments['member_id']} from card {arguments['card_id']}"
            )]

        elif name == "list_card_members":
            members = make_trello_request("GET", f"/cards/{arguments['card_id']}/members")
            
            # Handle empty member list case
            if not members:
                return [TextContent(type="text", text="No members assigned to this card")]
            
            # Format response as list of members with fullName, username, and ID
            result = "\n".join([
                f"- {member['fullName']} (@{member['username']}, ID: {member['id']})"
                for member in members
            ])
            return [TextContent(type="text", text=f"Members on card:\n{result}")]

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
    # Debug: Log startup
    logger.info("=" * 70)
    logger.info("TRELLO MCP SERVER STARTING")
    logger.info("=" * 70)
    logger.info(f"API Key from env: {os.getenv('TRELLO_API_KEY', 'NOT SET')}")
    logger.info(f"Token from env: {os.getenv('TRELLO_TOKEN', 'NOT SET')}")
    logger.info(f"Auth object API Key: {auth.api_key}")
    logger.info(f"Auth object Token: {'SET' if auth.token else 'NOT SET'}")
    logger.info(f"Is authenticated: {auth.is_authenticated()}")
    logger.info("=" * 70)
    
    # Check authentication at startup
    if not auth.is_authenticated():
        logger.info("=" * 70)
        logger.info("AUTHENTICATION REQUIRED")
        logger.info("=" * 70)
        logger.info("")
        logger.info("No authentication found. Starting automatic authentication...")
        logger.info("")
        
        # Try to get API key from environment
        api_key = os.getenv("TRELLO_API_KEY")
        
        if not api_key:
            logger.error("TRELLO_API_KEY environment variable not set.")
            logger.error("")
            logger.error("Please set your API key in mcp.json:")
            logger.error('  "env": { "TRELLO_API_KEY": "your_api_key" }')
            logger.error("")
            logger.error("Get your API key from: https://trello.com/app-key")
            logger.error("=" * 70)
            raise SystemExit(1)
        
        logger.info(f"Found API key: {api_key[:8]}...")
        logger.info("Opening browser for authorization...")
        logger.info("Please click 'Allow' in your browser to authorize the app.")
        logger.info("")
        
        # Run interactive authentication
        token = auth.authorize_interactive(api_key)
        
        if not token:
            logger.error("")
            logger.error("=" * 70)
            logger.error("AUTHENTICATION FAILED")
            logger.error("=" * 70)
            logger.error("Authorization timed out or was cancelled.")
            logger.error("")
            logger.error("The browser should have opened. If not, you can:")
            logger.error("1. Check if a browser window opened in the background")
            logger.error("2. Use manual authentication:")
            logger.error("   python auth.py --interactive")
            logger.error("=" * 70)
            raise SystemExit(1)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ AUTHENTICATION SUCCESSFUL!")
        logger.info("=" * 70)
        logger.info(f"Credentials saved to: {TOKEN_CACHE_FILE}")
        logger.info("")
    
    logger.info(f"Starting Trello MCP server (authenticated with key: {auth.api_key[:8]}...)")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Synchronous entry point for the CLI."""
    import asyncio
    asyncio.run(main())
