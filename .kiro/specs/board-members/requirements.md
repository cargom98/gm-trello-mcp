# Requirements Document

## Introduction

This document specifies the requirements for board member management functionality in the Trello MCP Server. The feature enables programmatic management of board memberships, including listing members, adding/removing members, updating permissions, and inviting members via email.

## Glossary

- **Board**: A Trello board containing lists and cards
- **Member**: A Trello user who has access to a board
- **Board_Member**: A user with specific permissions on a board
- **Permission_Level**: The access level a member has (admin, normal, observer)
- **MCP_Server**: The Model Context Protocol server implementation
- **Trello_API**: The Trello REST API at https://api.trello.com/1
- **Tool**: An MCP tool that exposes functionality to clients
- **Board_ID**: Unique identifier for a Trello board
- **Member_ID**: Unique identifier for a Trello user
- **Email_Address**: Email address used to invite new members

## Requirements

### Requirement 1: List Board Members

**User Story:** As a developer, I want to retrieve all members of a board, so that I can see who has access and their permission levels.

#### Acceptance Criteria

1. WHEN a valid board ID is provided, THE MCP_Server SHALL return all members of that board
2. WHEN returning board members, THE MCP_Server SHALL include member ID, username, full name, and permission level for each member
3. WHEN the board ID is invalid, THE MCP_Server SHALL return a descriptive error message
4. WHEN the authenticated user lacks permission to view the board, THE MCP_Server SHALL return an authorization error
5. THE MCP_Server SHALL format the response as JSON within TextContent

### Requirement 2: Add Member to Board

**User Story:** As a developer, I want to add existing Trello users to a board, so that I can grant them access programmatically.

#### Acceptance Criteria

1. WHEN a valid board ID and member ID are provided, THE MCP_Server SHALL add the member to the board
2. WHEN adding a member, THE MCP_Server SHALL accept an optional permission level parameter (admin, normal, observer)
3. WHERE no permission level is specified, THE MCP_Server SHALL default to "normal" permission
4. WHEN the member is successfully added, THE MCP_Server SHALL return confirmation with the member's details
5. WHEN the member is already on the board, THE MCP_Server SHALL return an appropriate message
6. WHEN the board ID or member ID is invalid, THE MCP_Server SHALL return a descriptive error message
7. WHEN the authenticated user lacks admin permission on the board, THE MCP_Server SHALL return an authorization error

### Requirement 3: Remove Member from Board

**User Story:** As a developer, I want to remove members from a board, so that I can revoke access when needed.

#### Acceptance Criteria

1. WHEN a valid board ID and member ID are provided, THE MCP_Server SHALL remove the member from the board
2. WHEN the member is successfully removed, THE MCP_Server SHALL return confirmation
3. WHEN the member is not on the board, THE MCP_Server SHALL return an appropriate message
4. WHEN the board ID or member ID is invalid, THE MCP_Server SHALL return a descriptive error message
5. WHEN the authenticated user lacks admin permission on the board, THE MCP_Server SHALL return an authorization error
6. WHEN attempting to remove the last admin from a board, THE MCP_Server SHALL prevent the removal and return an error

### Requirement 4: Update Member Permission

**User Story:** As a developer, I want to change a member's permission level on a board, so that I can adjust their access rights.

#### Acceptance Criteria

1. WHEN a valid board ID, member ID, and permission level are provided, THE MCP_Server SHALL update the member's permission
2. WHEN the permission level is provided, THE MCP_Server SHALL validate it is one of: admin, normal, observer
3. WHEN the permission is successfully updated, THE MCP_Server SHALL return confirmation with the new permission level
4. WHEN the member is not on the board, THE MCP_Server SHALL return an error message
5. WHEN the board ID or member ID is invalid, THE MCP_Server SHALL return a descriptive error message
6. WHEN an invalid permission level is provided, THE MCP_Server SHALL return a validation error
7. WHEN the authenticated user lacks admin permission on the board, THE MCP_Server SHALL return an authorization error
8. WHEN attempting to change the last admin to a non-admin role, THE MCP_Server SHALL prevent the change and return an error

### Requirement 5: Invite Member via Email

**User Story:** As a developer, I want to invite new members to a board using their email address, so that I can grant access to users who may not be in the organization yet.

#### Acceptance Criteria

1. WHEN a valid board ID and email address are provided, THE MCP_Server SHALL send an invitation to that email
2. WHEN inviting a member, THE MCP_Server SHALL accept an optional permission level parameter (admin, normal, observer)
3. WHERE no permission level is specified, THE MCP_Server SHALL default to "normal" permission
4. WHEN the invitation is successfully sent, THE MCP_Server SHALL return confirmation
5. WHEN the email address is invalid, THE MCP_Server SHALL return a validation error
6. WHEN the board ID is invalid, THE MCP_Server SHALL return a descriptive error message
7. WHEN the authenticated user lacks admin permission on the board, THE MCP_Server SHALL return an authorization error
8. WHEN the email address already corresponds to a board member, THE MCP_Server SHALL return an appropriate message

### Requirement 6: API Integration

**User Story:** As a system component, I want to use the Trello API correctly, so that all operations work reliably.

#### Acceptance Criteria

1. THE MCP_Server SHALL use the make_trello_request function for all API calls
2. THE MCP_Server SHALL use the TrelloAuth class for authentication
3. WHEN making API requests, THE MCP_Server SHALL include the API key and OAuth token
4. WHEN the Trello API returns an error, THE MCP_Server SHALL propagate a descriptive error message
5. THE MCP_Server SHALL use the base URL https://api.trello.com/1 for all API calls

### Requirement 7: Tool Registration

**User Story:** As an MCP client, I want to discover available board member tools, so that I can use them programmatically.

#### Acceptance Criteria

1. THE MCP_Server SHALL register all board member tools using the @app.list_tools() decorator
2. WHEN a tool is registered, THE MCP_Server SHALL provide a clear description of its purpose
3. WHEN a tool is registered, THE MCP_Server SHALL define all required and optional parameters with types
4. WHEN a tool is registered, THE MCP_Server SHALL include parameter descriptions
5. THE MCP_Server SHALL handle tool execution through the @app.call_tool() dispatcher

### Requirement 8: Error Handling

**User Story:** As a developer, I want clear error messages, so that I can diagnose and fix issues quickly.

#### Acceptance Criteria

1. WHEN an API error occurs, THE MCP_Server SHALL return a TextContent response with error details
2. WHEN a validation error occurs, THE MCP_Server SHALL return a descriptive message indicating what was invalid
3. WHEN an authentication error occurs, THE MCP_Server SHALL return a message indicating insufficient permissions
4. WHEN a network error occurs, THE MCP_Server SHALL return a message indicating the connection issue
5. THE MCP_Server SHALL log errors using the logger.error() function
