"""Trello MCP Server implementation."""
import os
import json
import logging
import socket
import webbrowser
import secrets
import re
from pathlib import Path
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import functools
from mcp.server.fastmcp import FastMCP
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trello-mcp-server")

# Trello API configuration
TRELLO_API_BASE = "https://api.trello.com/1"
TOKEN_CACHE_FILE = Path.home() / ".trello_mcp_token.json"

mcp_server = FastMCP("trello-mcp-server")

# Global variable to store token from callback
_callback_token = None
_callback_event = None
_oauth_state = None


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
        global _callback_token, _callback_event, _oauth_state

        parsed = urlparse(self.path)

        # Check if token is in query params (from JavaScript callback)
        params = parse_qs(parsed.query)
        if 'token' in params:
            # Validate state parameter for CSRF protection
            received_state = params.get('state', [None])[0]
            if received_state != _oauth_state:
                logger.error("OAuth state mismatch - possible CSRF attack")
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = """
                <html>
                <head><title>Trello Authorization - Error</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h2 style="color: #c9372c;">✗ Authorization Failed</h2>
                    <p>Invalid authorization request. This may be a CSRF attack attempt.</p>
                    <p>Please close this window and try authenticating again.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
                return
            
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
        html = f"""
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

                if (token) {{
                    // Send token to server via query param with state for CSRF protection
                    fetch('/?token=' + encodeURIComponent(token) + '&state=' + encodeURIComponent('{_oauth_state}'))
                        .then(response => response.text())
                        .then(html => {{
                            document.open();
                            document.write(html);
                            document.close();
                        }})
                        .catch(err => {{
                            document.body.innerHTML = '<h2 style="color: #c9372c;">✗ Error</h2><p>Failed to send token to server: ' + err.message + '</p>';
                        }});
                }} else {{
                    document.body.innerHTML = '<h2 style="color: #c9372c;">✗ No Token Found</h2><p>No token was found in the URL. Please try the authorization process again.</p>';
                }}
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
        """Save token to cache file with secure permissions."""
        try:
            # Create file with secure permissions atomically
            # Use os.open to set permissions before writing
            fd = os.open(
                TOKEN_CACHE_FILE, 
                os.O_CREAT | os.O_WRONLY | os.O_TRUNC,
                0o600  # Secure permissions from creation
            )
            with os.fdopen(fd, 'w') as f:
                json.dump({'api_key': api_key, 'token': token}, f)
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
            # Validate return_url for security - only allow localhost
            parsed = urlparse(return_url)
            if parsed.hostname not in ['localhost', '127.0.0.1', None]:
                raise ValueError("Return URL must be localhost for security")
            
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
        global _callback_token, _callback_event, _oauth_state
        
        _callback_token = None
        _callback_event = threading.Event()
        # Generate CSRF protection state parameter
        _oauth_state = secrets.token_urlsafe(32)
        
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
                    logger.info(f"Token received: {token[:8]}...")
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

def validate_trello_id(id_value: str, id_type: str = "ID") -> str:
    """Validate Trello ID format for security.
    
    Args:
        id_value: The ID to validate
        id_type: Type of ID for error messages (e.g., "board ID", "card ID")
    
    Returns:
        The validated ID
        
    Raises:
        ValueError: If ID format is invalid
    """
    if not id_value:
        raise ValueError(f"{id_type} cannot be empty")
    
    # Trello IDs are 24-character hexadecimal strings or shorter alphanumeric strings
    # Allow alphanumeric characters and underscores, reasonable length
    if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', id_value):
        raise ValueError(f"Invalid {id_type} format. Must be alphanumeric (1-64 characters)")
    
    return id_value

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
    
    # Add timeout and explicit certificate verification for security
    response = requests.request(
        method, 
        url, 
        params=auth_params, 
        json=data,
        timeout=30,  # 30 second timeout
        verify=True  # Explicit SSL certificate verification
    )
    response.raise_for_status()
    return response.json()


def handle_request_errors(func):
    """Decorator that wraps tool functions with standard Trello API error handling."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            return f"Validation Error: {str(e)}"
        except requests.exceptions.HTTPError as e:
            logger.error(f"Trello API error: {e}")
            logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
            if status_code == 401:
                return "Error: Authentication failed. Please check your credentials."
            elif status_code == 403:
                return "Error: Permission denied. You don't have access to this resource."
            elif status_code == 404:
                return "Error: Resource not found. Please check the ID."
            elif status_code == 429:
                return "Error: Rate limit exceeded. Please try again later."
            else:
                return f"Error: API request failed (status {status_code})."
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Trello API. Please check your network."
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "Error: An unexpected error occurred. Please try again."
    return wrapper


@mcp_server.tool()
@handle_request_errors
async def list_boards() -> str:
    """List all boards accessible to the authenticated user."""
    boards = make_trello_request("GET", "/members/me/boards")
    result = "\n".join([f"- {board['name']} (ID: {board['id']})" for board in boards])
    return f"Your Trello Boards:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def get_board(board_id: str) -> str:
    """Get details about a specific board."""
    validate_trello_id(board_id, "Board ID")
    board = make_trello_request("GET", f"/boards/{board_id}")
    return f"Board: {board['name']}\nID: {board['id']}\nURL: {board['url']}\nDescription: {board.get('desc', 'N/A')}"


@mcp_server.tool()
@handle_request_errors
async def list_board_lists(board_id: str) -> str:
    """Get all lists on a board."""
    validate_trello_id(board_id, "Board ID")
    lists = make_trello_request("GET", f"/boards/{board_id}/lists")
    result = "\n".join([f"- {lst['name']} (ID: {lst['id']})" for lst in lists])
    return f"Lists on board:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def list_board_cards(board_id: str) -> str:
    """Get all cards on a board."""
    validate_trello_id(board_id, "Board ID")
    cards = make_trello_request("GET", f"/boards/{board_id}/cards")
    result = "\n".join([f"- {card['name']} (ID: {card['id']}, List: {card['idList']})" for card in cards])
    return f"Cards on board:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def create_card(list_id: str, name: str, desc: Optional[str] = None) -> str:
    """Create a new card on a list."""
    validate_trello_id(list_id, "List ID")
    data = {"idList": list_id, "name": name}
    if desc is not None:
        data["desc"] = desc
    card = make_trello_request("POST", "/cards", data=data)
    return f"Created card: {card['name']}\nID: {card['id']}\nURL: {card['url']}"


@mcp_server.tool()
@handle_request_errors
async def update_card(card_id: str, name: Optional[str] = None, desc: Optional[str] = None, list_id: Optional[str] = None) -> str:
    """Update a card's properties."""
    validate_trello_id(card_id, "Card ID")
    data = {}
    if name is not None:
        data["name"] = name
    if desc is not None:
        data["desc"] = desc
    if list_id is not None:
        data["idList"] = list_id
    card = make_trello_request("PUT", f"/cards/{card_id}", data=data)
    return f"Updated card: {card['name']}\nID: {card['id']}\nURL: {card['url']}"


@mcp_server.tool()
@handle_request_errors
async def get_card(card_id: str) -> str:
    """Get details about a specific card."""
    validate_trello_id(card_id, "Card ID")
    card = make_trello_request("GET", f"/cards/{card_id}")
    return f"Card: {card['name']}\nID: {card['id']}\nDescription: {card.get('desc', 'N/A')}\nList ID: {card['idList']}\nURL: {card['url']}"


@mcp_server.tool()
@handle_request_errors
async def create_list(board_id: str, name: str, pos: Optional[str] = None) -> str:
    """Create a new list on a board."""
    validate_trello_id(board_id, "Board ID")
    data = {"name": name, "idBoard": board_id}
    if pos is not None:
        data["pos"] = pos
    lst = make_trello_request("POST", "/lists", data=data)
    return f"Created list: {lst['name']}\nID: {lst['id']}\nBoard ID: {lst['idBoard']}"


@mcp_server.tool()
@handle_request_errors
async def list_organizations() -> str:
    """List all organizations/workspaces the authenticated user belongs to."""
    orgs = make_trello_request("GET", "/members/me/organizations")
    result = "\n".join([f"- {org['displayName']} (ID: {org['id']}, Name: {org['name']})" for org in orgs])
    return f"Your Organizations/Workspaces:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def get_organization(org_id: str) -> str:
    """Get details about a specific organization/workspace."""
    validate_trello_id(org_id, "Organization ID")
    org = make_trello_request("GET", f"/organizations/{org_id}")
    return f"Organization: {org['displayName']}\nID: {org['id']}\nName: {org['name']}\nDescription: {org.get('desc', 'N/A')}\nURL: {org['url']}\nWebsite: {org.get('website', 'N/A')}"


@mcp_server.tool()
@handle_request_errors
async def list_organization_boards(org_id: str) -> str:
    """Get all boards in an organization/workspace."""
    validate_trello_id(org_id, "Organization ID")
    boards = make_trello_request("GET", f"/organizations/{org_id}/boards")
    result = "\n".join([f"- {board['name']} (ID: {board['id']})" for board in boards])
    return f"Boards in organization:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def list_organization_members(org_id: str) -> str:
    """Get all members of an organization/workspace."""
    validate_trello_id(org_id, "Organization ID")
    members = make_trello_request("GET", f"/organizations/{org_id}/members")
    result = "\n".join([f"- {member['fullName']} (@{member['username']}, ID: {member['id']})" for member in members])
    return f"Members in organization:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def add_organization_member(org_id: str, email: str, full_name: Optional[str] = None, type: Optional[str] = None) -> str:
    """Add a member to an organization/workspace."""
    validate_trello_id(org_id, "Organization ID")
    data = {"email": email}
    if full_name is not None:
        data["fullName"] = full_name
    if type is not None:
        data["type"] = type
    member = make_trello_request("PUT", f"/organizations/{org_id}/members", data=data)
    return f"Added member to organization: {member.get('fullName', email)}"


@mcp_server.tool()
@handle_request_errors
async def remove_organization_member(org_id: str, member_id: str) -> str:
    """Remove a member from an organization/workspace."""
    validate_trello_id(org_id, "Organization ID")
    validate_trello_id(member_id, "Member ID")
    make_trello_request("DELETE", f"/organizations/{org_id}/members/{member_id}")
    return f"Removed member {member_id} from organization"


@mcp_server.tool()
@handle_request_errors
async def add_card_label(card_id: str, label_id: str) -> str:
    """Add a label to a card."""
    validate_trello_id(card_id, "Card ID")
    validate_trello_id(label_id, "Label ID")
    data = {"value": label_id}
    make_trello_request("POST", f"/cards/{card_id}/idLabels", data=data)
    card = make_trello_request("GET", f"/cards/{card_id}")
    label_info = None
    for label in card.get('labels', []):
        if label['id'] == label_id:
            label_info = label
            break
    if label_info:
        label_name = label_info.get('name', 'Unnamed')
        label_color = label_info.get('color', 'none')
        return f"Added label to card: {card['name']}\nLabel: {label_name} ({label_color})\nCard ID: {card['id']}"
    else:
        return f"Added label to card: {card['name']}\nCard ID: {card['id']}"


@mcp_server.tool()
@handle_request_errors
async def remove_card_label(card_id: str, label_id: str) -> str:
    """Remove a label from a card."""
    validate_trello_id(card_id, "Card ID")
    validate_trello_id(label_id, "Label ID")
    make_trello_request("DELETE", f"/cards/{card_id}/idLabels/{label_id}")
    return f"Removed label from card\nCard ID: {card_id}\nLabel ID: {label_id}"


@mcp_server.tool()
@handle_request_errors
async def list_card_labels(card_id: str) -> str:
    """List all labels on a card."""
    validate_trello_id(card_id, "Card ID")
    labels = make_trello_request("GET", f"/cards/{card_id}/labels")
    if not labels:
        return "Labels on card:\n(No labels)"
    result = "\n".join([
        f"- {label.get('name', 'Unnamed')} (Color: {label.get('color', 'none')}, ID: {label['id']})"
        for label in labels
    ])
    return f"Labels on card:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def list_board_labels(board_id: str) -> str:
    """List all available labels on a board."""
    validate_trello_id(board_id, "Board ID")
    labels = make_trello_request("GET", f"/boards/{board_id}/labels")
    result = "\n".join([
        f"- {label.get('name', 'Unnamed')} (Color: {label.get('color', 'none')}, ID: {label['id']})"
        for label in labels
    ])
    return f"Available labels on board:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def filter_cards_by_label(board_id: str, label_id: str) -> str:
    """Filter cards on a board by a specific label."""
    validate_trello_id(board_id, "Board ID")
    validate_trello_id(label_id, "Label ID")
    cards = make_trello_request("GET", f"/boards/{board_id}/cards")
    filtered_cards = [card for card in cards if label_id in card.get('idLabels', [])]
    if not filtered_cards:
        labels = make_trello_request("GET", f"/boards/{board_id}/labels")
        label_name = "Unknown"
        for label in labels:
            if label['id'] == label_id:
                label_name = label.get('name', 'Unnamed')
                break
        return f"Cards with label {label_name}:\n(No cards found)"
    label_name = "Unknown"
    if filtered_cards:
        for label in filtered_cards[0].get('labels', []):
            if label['id'] == label_id:
                label_name = label.get('name', 'Unnamed')
                break
    result = "\n".join([
        f"- {card['name']} (ID: {card['id']}, List: {card['idList']})"
        for card in filtered_cards
    ])
    return f"Cards with label {label_name}:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def list_board_members(board_id: str) -> str:
    """List all members of a board with their permission levels."""
    validate_trello_id(board_id, "Board ID")
    members = make_trello_request("GET", f"/boards/{board_id}/members")
    result = "\n".join([
        f"- {member['fullName']} (@{member['username']}, ID: {member['id']}, Permission: {member.get('memberType', 'normal')})"
        for member in members
    ])
    return f"Board Members:\n{result}"


@mcp_server.tool()
@handle_request_errors
async def add_board_member(board_id: str, member_id: str, type: Optional[str] = None) -> str:
    """Add an existing Trello user to a board with specified permission level."""
    validate_trello_id(board_id, "Board ID")
    validate_trello_id(member_id, "Member ID")
    member_type = type if type is not None else "normal"
    params = {"type": member_type}
    make_trello_request("PUT", f"/boards/{board_id}/members/{member_id}", params=params)
    member = make_trello_request("GET", f"/members/{member_id}")
    return f"Added member to board: {member['fullName']} (@{member['username']})\nPermission: {member_type}"


@mcp_server.tool()
@handle_request_errors
async def remove_board_member(board_id: str, member_id: str) -> str:
    """Remove a member from a board."""
    validate_trello_id(board_id, "Board ID")
    validate_trello_id(member_id, "Member ID")
    make_trello_request("DELETE", f"/boards/{board_id}/members/{member_id}")
    return f"Removed member {member_id} from board"


@mcp_server.tool()
@handle_request_errors
async def update_board_member(board_id: str, member_id: str, type: str) -> str:
    """Update a member's permission level on a board."""
    validate_trello_id(board_id, "Board ID")
    validate_trello_id(member_id, "Member ID")
    valid_permissions = ["admin", "normal", "observer"]
    if type not in valid_permissions:
        return f"Error: Invalid permission type. Must be one of: {', '.join(valid_permissions)}"
    params = {"type": type}
    make_trello_request("PUT", f"/boards/{board_id}/members/{member_id}", params=params)
    member = make_trello_request("GET", f"/members/{member_id}")
    return f"Updated member permission: {member['fullName']} (@{member['username']})\nNew permission: {type}"


@mcp_server.tool()
@handle_request_errors
async def invite_board_member(board_id: str, email: str, type: Optional[str] = None) -> str:
    """Invite a new member to a board via email address."""
    validate_trello_id(board_id, "Board ID")
    member_type = type if type is not None else "normal"
    params = {"email": email, "type": member_type}
    make_trello_request("PUT", f"/boards/{board_id}/members", params=params)
    return f"Invited {email} to board\nPermission: {member_type}"


@mcp_server.tool()
@handle_request_errors
async def add_card_member(card_id: str, member_id: str) -> str:
    """Add a member to a card."""
    validate_trello_id(card_id, "Card ID")
    validate_trello_id(member_id, "Member ID")
    data = {"value": member_id}
    make_trello_request("POST", f"/cards/{card_id}/idMembers", data=data)
    return f"Added member {member_id} to card {card_id}"


@mcp_server.tool()
@handle_request_errors
async def remove_card_member(card_id: str, member_id: str) -> str:
    """Remove a member from a card."""
    validate_trello_id(card_id, "Card ID")
    validate_trello_id(member_id, "Member ID")
    make_trello_request("DELETE", f"/cards/{card_id}/idMembers/{member_id}")
    return f"Removed member {member_id} from card {card_id}"


@mcp_server.tool()
@handle_request_errors
async def list_card_members(card_id: str) -> str:
    """List all members assigned to a card."""
    validate_trello_id(card_id, "Card ID")
    members = make_trello_request("GET", f"/cards/{card_id}/members")
    if not members:
        return "No members assigned to this card"
    result = "\n".join([
        f"- {member['fullName']} (@{member['username']}, ID: {member['id']})"
        for member in members
    ])
    return f"Members on card:\n{result}"


async def main():
    """Run the server."""
    # Debug: Log startup
    logger.info("=" * 70)
    logger.info("TRELLO MCP SERVER STARTING")
    logger.info("=" * 70)
    logger.info(f"API Key from env: {'SET' if os.getenv('TRELLO_API_KEY') else 'NOT SET'}")
    logger.info(f"Token from env: {'SET' if os.getenv('TRELLO_TOKEN') else 'NOT SET'}")
    logger.info(f"Auth object API Key: {'SET' if auth.api_key else 'NOT SET'}")
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
        
        logger.info(f"Found API key: {api_key[:4]}...")
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
    
    await mcp_server.run_stdio_async()


def run():
    """Synchronous entry point for the CLI."""
    import asyncio
    asyncio.run(main())

if __name__ == "__main__":
    run()
