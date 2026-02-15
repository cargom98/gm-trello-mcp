# Changelog

## [Unreleased]

### Added
- **Automatic OAuth Flow**: New `authorize_interactive` tool that automatically opens browser and captures token
  - Opens default browser to Trello authorization page
  - Starts local callback server (default port 8765)
  - Automatically captures and saves token when user clicks "Allow"
  - No manual copy-paste required
- Local HTTP server for OAuth callback handling
- JavaScript-based token extraction from URL fragment
- Configurable callback port for flexibility

### Changed
- Enhanced `get_auth_url` to support return_url parameter for OAuth callbacks
- Updated authentication documentation with three methods (automatic, manual, environment variables)
- Improved README with clearer authentication flow descriptions
- Enhanced error messages to guide users between automatic and manual methods

### Security
- Token cache file (`~/.trello_mcp_token.json`) added to .gitignore
- Removed credentials from mcp.json configuration files
- Maintained secure file permissions (600) for token cache
- OAuth callback server runs only during authentication (not persistent)

## [1.0.0] - Initial Release

### Added
- Trello MCP server implementation
- 8 core tools for board, list, and card management
- Token caching system with secure storage
- Manual authentication flow with `get_auth_url` and `set_token`
- Environment variable support for CI/CD
- Comprehensive documentation (README.md, AUTHENTICATION.md)
- Setup script for easy installation
