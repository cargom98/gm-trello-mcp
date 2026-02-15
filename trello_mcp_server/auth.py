#!/usr/bin/env python3
"""Standalone authentication script for Trello MCP Server."""
import sys
import os
import json
from pathlib import Path

# Import from the server module
from trello_mcp_server.server import TrelloAuth, TOKEN_CACHE_FILE, logger


def main():
    """Run authentication flow."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Authenticate Trello MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Automatic authentication (recommended)
  python -m trello_mcp_server.auth --interactive
  
  # Manual authentication
  python -m trello_mcp_server.auth --manual
  
  # Check authentication status
  python -m trello_mcp_server.auth --check
  
  # Set credentials directly
  python -m trello_mcp_server.auth --set-key YOUR_KEY --set-token YOUR_TOKEN
        """
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive authentication with automatic browser opening'
    )
    
    parser.add_argument(
        '--manual', '-m',
        action='store_true',
        help='Manual authentication (generates URL for you to visit)'
    )
    
    parser.add_argument(
        '--check', '-c',
        action='store_true',
        help='Check current authentication status'
    )
    
    parser.add_argument(
        '--set-key',
        type=str,
        help='Set API key directly'
    )
    
    parser.add_argument(
        '--set-token',
        type=str,
        help='Set token directly'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='Port for OAuth callback (default: 8765)'
    )
    
    args = parser.parse_args()
    
    # Create auth instance
    auth = TrelloAuth()
    
    # Check authentication status
    if args.check:
        if auth.is_authenticated():
            api_key, _ = auth.get_credentials()
            print(f"✓ Authenticated with API key: {api_key[:8]}...")
            print(f"  Token cache: {TOKEN_CACHE_FILE}")
            return 0
        else:
            print("✗ Not authenticated")
            print("\nTo authenticate, run:")
            print("  python -m trello_mcp_server.auth --interactive")
            return 1
    
    # Set credentials directly
    if args.set_key and args.set_token:
        auth.set_credentials(args.set_key, args.set_token)
        print("✓ Credentials saved successfully!")
        print(f"  API Key: {args.set_key[:8]}...")
        print(f"  Token cache: {TOKEN_CACHE_FILE}")
        return 0
    elif args.set_key or args.set_token:
        print("✗ Error: Both --set-key and --set-token are required")
        return 1
    
    # Interactive authentication
    if args.interactive:
        print("=" * 70)
        print("TRELLO MCP SERVER - INTERACTIVE AUTHENTICATION")
        print("=" * 70)
        print()
        
        # Get API key
        api_key = input("Enter your Trello API key (from https://trello.com/app-key): ").strip()
        
        if not api_key:
            print("✗ Error: API key is required")
            return 1
        
        print()
        print("Opening browser for authorization...")
        print(f"A local server will start on port {args.port} to capture the token.")
        print("Click 'Allow' in your browser to authorize the app.")
        print()
        
        token = auth.authorize_interactive(api_key, port=args.port)
        
        if token:
            print()
            print("=" * 70)
            print("✓ AUTHENTICATION SUCCESSFUL!")
            print("=" * 70)
            print(f"  API Key: {api_key[:8]}...")
            print(f"  Token: {token[:16]}...")
            print(f"  Saved to: {TOKEN_CACHE_FILE}")
            print()
            print("You can now start the Trello MCP server.")
            print("=" * 70)
            return 0
        else:
            print()
            print("=" * 70)
            print("✗ AUTHENTICATION FAILED")
            print("=" * 70)
            print("The authorization timed out or was cancelled.")
            print()
            print("Try again with:")
            print("  python -m trello_mcp_server.auth --interactive")
            print()
            print("Or use manual authentication:")
            print("  python -m trello_mcp_server.auth --manual")
            print("=" * 70)
            return 1
    
    # Manual authentication
    if args.manual:
        print("=" * 70)
        print("TRELLO MCP SERVER - MANUAL AUTHENTICATION")
        print("=" * 70)
        print()
        
        # Get API key
        api_key = input("Enter your Trello API key (from https://trello.com/app-key): ").strip()
        
        if not api_key:
            print("✗ Error: API key is required")
            return 1
        
        # Generate auth URL
        auth_url = auth.get_auth_url(api_key)
        
        print()
        print("Visit this URL in your browser:")
        print()
        print(f"  {auth_url}")
        print()
        print("After clicking 'Allow', copy the token and paste it below.")
        print()
        
        token = input("Enter the token: ").strip()
        
        if not token:
            print("✗ Error: Token is required")
            return 1
        
        # Save credentials
        auth.set_credentials(api_key, token)
        
        print()
        print("=" * 70)
        print("✓ AUTHENTICATION SUCCESSFUL!")
        print("=" * 70)
        print(f"  API Key: {api_key[:8]}...")
        print(f"  Token: {token[:16]}...")
        print(f"  Saved to: {TOKEN_CACHE_FILE}")
        print()
        print("You can now start the Trello MCP server.")
        print("=" * 70)
        return 0
    
    # No action specified
    if not any([args.interactive, args.manual, args.check, args.set_key]):
        parser.print_help()
        print()
        print("Quick start:")
        print("  python -m trello_mcp_server.auth --interactive")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
