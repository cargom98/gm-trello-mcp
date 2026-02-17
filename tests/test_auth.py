#!/usr/bin/env python3
"""Test authentication check."""
import os
import sys

# Set the API key from environment or use placeholder
if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"

# Import after setting env var
# Add parent directory to path to import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import auth

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
