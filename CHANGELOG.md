# Changelog

## [1.0.0] - 2024

### Added
- **Organization/Workspace Management**: Tools for managing Trello organizations
  - `list_organizations` - List all organizations/workspaces
  - `get_organization` - Get detailed organization information
  - `list_organization_boards` - Get all boards in an organization
  - `list_organization_members` - Get all members of an organization
  - `add_organization_member` - Add a member to an organization
  - `remove_organization_member` - Remove a member from an organization
- **Automatic OAuth Flow**: Browser-based authentication with automatic token capture
  - Opens browser to Trello authorization page
  - Local callback server (port 8765) captures token
  - No manual copy-paste required
- **Core Trello Tools**:
  - Board management (list, get details)
  - List management (list, create)
  - Card management (list, get, create, update, move)
- **Authentication System**:
  - Token caching in `~/.trello_mcp_token.json`
  - Secure file permissions (600)
  - Multiple auth methods (automatic, manual, environment variables)
- **Documentation**:
  - Comprehensive POWER.md for Kiro power users
  - Detailed authentication guide
  - Organization management guide
  - Developer quick start
- **Testing**: Test scripts for authentication and organization tools

### Security
- Token cache file automatically added to .gitignore
- Secure file permissions (600) on token cache
- API keys separate from tokens
- OAuth callback server runs only during authentication
