#!/usr/bin/env python3
"""Test authentication check."""
import os
import sys

# Set the API key
os.environ["TRELLO_API_KEY"] = "e9a94d46df7b6a1bb3bd0df25d125b47"

# Import after setting env var
from trello_mcp_server.server import auth

print("=" * 70)
print("AUTHENTICATION TEST")
print("=" * 70)
print()
print(f"API Key from env: {os.getenv('TRELLO_API_KEY')}")
print(f"Token from env: {os.getenv('TRELLO_TOKEN')}")
print()
print(f"Auth object API Key: {auth.api_key}")
print(f"Auth object Token: {auth.token}")
print()
print(f"Is authenticated: {auth.is_authenticated()}")
print()

if auth.is_authenticated():
    print("✓ Server would START (authenticated)")
else:
    print("✗ Server would FAIL (not authenticated)")
    print("   Authentication flow should trigger")

print("=" * 70)
