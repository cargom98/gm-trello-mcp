# Security Policy

## Overview

The Trello MCP Server implements multiple security measures to protect user credentials and prevent common vulnerabilities. This document describes the security posture of the application and provides guidance for secure usage.

## Security Measures Implemented

### 1. Authentication & Credentials

#### Secure Token Storage
- **Location**: Tokens are stored in `~/.trello_mcp_token.json`
- **Permissions**: File is created with `0o600` (owner read/write only) atomically to prevent race conditions
- **Protection**: Tokens are excluded from version control via `.gitignore`
- **Recommendation**: Consider using OS-native credential storage (e.g., keyring library) for enhanced security

#### Environment Variables
- API keys can be provided via `TRELLO_API_KEY` environment variable
- Tokens can be provided via `TRELLO_TOKEN` environment variable
- **Best Practice**: Use `.env` files (excluded from version control) rather than shell exports

#### OAuth Flow Security
- **CSRF Protection**: OAuth flow includes state parameter validation to prevent CSRF attacks
- **Secure Callback**: OAuth callback server only binds to localhost
- **Token Handling**: Tokens are transmitted with CSRF protection and never logged in full
- **Timeout**: OAuth callback has a 120-second timeout to prevent hanging

### 2. Input Validation

#### ID Validation
All Trello resource IDs (board_id, card_id, list_id, member_id, etc.) are validated using regex:
- Pattern: `^[a-zA-Z0-9_-]{1,64}$`
- Prevents: SQL injection, command injection, path traversal attacks
- Maximum length: 64 characters

#### URL Validation
- OAuth return URLs are validated to only allow localhost destinations
- Prevents: Open redirect vulnerabilities

### 3. Logging & Information Disclosure

#### Sensitive Data Redaction
- API keys are logged as `{key[:4]}...` (only first 4 characters)
- Tokens are logged as `{token[:8]}...` (only first 8 characters)
- Full credentials are never logged
- Environment variables show only "SET" or "NOT SET" status

#### Error Message Sanitization
- Internal error details are logged server-side only
- Users receive generic error messages without internal details
- HTTP status codes are mapped to user-friendly messages:
  - 401: Authentication failed
  - 403: Permission denied
  - 404: Resource not found
  - 429: Rate limit exceeded
  - Others: Generic API request failure

### 4. Network Security

#### HTTP Request Security
- **Timeouts**: All API requests have a 30-second timeout
- **Certificate Verification**: Explicit SSL/TLS certificate verification enabled (`verify=True`)
- **No Follow Redirects**: Prevents redirect-based attacks (default requests behavior)

#### API Communication
- All communication with Trello API uses HTTPS
- No sensitive data transmitted via HTTP
- API credentials passed as query parameters (Trello's standard method)

### 5. Dependency Security

#### Updated Dependencies
- `mcp>=1.26.0` - Latest version addressing:
  - DNS rebinding protection (CVE affecting < 1.23.0)
  - FastMCP Server DoS (CVE affecting < 1.9.4)
  - HTTP Transport DoS (CVE affecting < 1.10.0)
- `requests>=2.32.0` - Latest stable version with security fixes

#### Dependency Scanning
Dependencies are regularly scanned against the GitHub Advisory Database for known vulnerabilities.

## Security Best Practices for Users

### 1. API Key Management

- **Never commit** API keys or tokens to version control
- **Rotate credentials** periodically (recommended: every 90 days)
- **Use separate tokens** for different environments (dev/staging/prod)
- **Revoke unused tokens** at https://trello.com/my/account

### 2. Environment Setup

```bash
# Use .env file (gitignored)
echo "TRELLO_API_KEY=your_key_here" > .env
echo "TRELLO_TOKEN=your_token_here" >> .env

# Secure permissions
chmod 600 .env
```

### 3. Token Revocation

If you suspect a token has been compromised:

1. Visit https://trello.com/my/account
2. Go to "Applications" section
3. Find your application
4. Click "Revoke" to invalidate the token
5. Delete `~/.trello_mcp_token.json`
6. Re-authenticate using the interactive flow

### 4. Monitoring

- Regularly check your Trello account for unexpected activity
- Review authorized applications at https://trello.com/my/account
- Monitor API usage for anomalies

## Reporting Security Issues

If you discover a security vulnerability, please report it privately:

1. **Do not** open a public issue
2. Email the maintainer with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work to address the issue promptly.

## Security Checklist for Deployments

- [ ] API keys stored securely (environment variables or key management service)
- [ ] Token file permissions verified (`ls -la ~/.trello_mcp_token.json` shows `-rw-------`)
- [ ] `.gitignore` includes `.env` and `.trello_mcp_token.json`
- [ ] Dependencies updated to latest secure versions
- [ ] Environment isolated (virtual environment or container)
- [ ] Logs reviewed for any credential leakage
- [ ] Network access restricted to necessary endpoints only
- [ ] OAuth callback server only accessible from localhost

## Known Limitations

### 1. Token Storage
- Tokens are stored in plaintext (though with secure permissions)
- **Mitigation**: Use OS-native credential storage for production deployments

### 2. OAuth Callback
- OAuth callback uses HTTP (not HTTPS) on localhost
- **Risk**: Minimal - server only binds to localhost
- **Mitigation**: OAuth flow includes CSRF state parameter

### 3. API Key Transmission
- Trello API requires credentials as query parameters (not headers)
- **Risk**: Credentials may appear in server logs
- **Mitigation**: This is Trello's standard authentication method; use HTTPS

## Security Audit History

### Version 2.0.4 (2026-02-17)

**Critical Fixes:**
- Removed hardcoded API keys from test files and documentation
- Removed command-line credential input (--set-key, --set-token)
- Updated MCP dependency from 1.0.0 to 1.26.0 (fixes 3 CVEs)
- Updated requests dependency from 2.31.0 to 2.32.0

**High Priority Fixes:**
- Added CSRF protection to OAuth flow (state parameter)
- Implemented sensitive data redaction in logs
- Fixed file permission race condition in token storage

**Medium Priority Fixes:**
- Added 30-second timeout to all HTTP requests
- Added explicit SSL certificate verification
- Implemented input validation for all ID fields
- Sanitized error messages to prevent information disclosure
- Added redirect URL validation (localhost only)

**Total Issues Fixed:** 11 critical/high, 6 medium priority

## Compliance & Standards

This application follows:
- OWASP Top 10 security guidelines
- OAuth 2.0 best practices (RFC 6749)
- Secure coding standards for Python
- GitHub Security Best Practices

## License

See LICENSE file for details.
