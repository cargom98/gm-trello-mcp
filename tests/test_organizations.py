#!/usr/bin/env python3
"""
Interactive test script for organization/workspace management tools.

Usage:
    python test_organizations.py                    # Interactive mode
    python test_organizations.py --org-id myteam    # Test specific org
"""

import asyncio
import sys
import os
# Add parent directory to path to import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import call_tool
from auth import TrelloAuth

async def test_list_organizations():
    """Test listing all organizations."""
    print("\n📋 Listing all organizations...")
    try:
        result = await call_tool("list_organizations", {})
        print(result[0].text)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_get_organization(org_id):
    """Test getting organization details."""
    print(f"\n🔍 Getting details for organization '{org_id}'...")
    try:
        result = await call_tool("get_organization", {"org_id": org_id})
        print(result[0].text)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_list_organization_boards(org_id):
    """Test listing organization boards."""
    print(f"\n📊 Listing boards in organization '{org_id}'...")
    try:
        result = await call_tool("list_organization_boards", {"org_id": org_id})
        print(result[0].text)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_list_organization_members(org_id):
    """Test listing organization members."""
    print(f"\n👥 Listing members in organization '{org_id}'...")
    try:
        result = await call_tool("list_organization_members", {"org_id": org_id})
        print(result[0].text)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def interactive_mode():
    """Run tests in interactive mode."""
    print("=" * 60)
    print("🧪 Trello Organization Tools - Interactive Test")
    print("=" * 60)
    
    # Check authentication
    auth = TrelloAuth()
    if not auth.is_authenticated():
        print("\n❌ Not authenticated!")
        print("Please run authentication first:")
        print("  python auth.py --interactive")
        return
    
    print("\n✅ Authentication verified")
    
    # Test 1: List organizations
    success = await test_list_organizations()
    if not success:
        print("\n⚠️  Cannot continue without organization list")
        return
    
    # Ask for org_id
    print("\n" + "-" * 60)
    org_id = input("\nEnter an organization ID or name to test (or press Enter to skip): ").strip()
    
    if not org_id:
        print("\n✅ Basic test completed!")
        return
    
    # Test remaining tools with the provided org_id
    await test_get_organization(org_id)
    await test_list_organization_boards(org_id)
    await test_list_organization_members(org_id)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("\nNote: Member management tools (add/remove) require admin permissions")
    print("      and are not included in this test to avoid accidental changes.")

async def automated_mode(org_id):
    """Run tests with a specific org_id."""
    print("=" * 60)
    print(f"🧪 Testing organization: {org_id}")
    print("=" * 60)
    
    # Check authentication
    auth = TrelloAuth()
    if not auth.is_authenticated():
        print("\n❌ Not authenticated!")
        print("Please run authentication first:")
        print("  python auth.py --interactive")
        return
    
    print("\n✅ Authentication verified")
    
    # Run all read-only tests
    await test_list_organizations()
    await test_get_organization(org_id)
    await test_list_organization_boards(org_id)
    await test_list_organization_members(org_id)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print(__doc__)
            return
        elif sys.argv[1] == "--org-id" and len(sys.argv) > 2:
            asyncio.run(automated_mode(sys.argv[2]))
        else:
            print("Invalid arguments. Use --help for usage information.")
    else:
        asyncio.run(interactive_mode())

if __name__ == "__main__":
    main()
