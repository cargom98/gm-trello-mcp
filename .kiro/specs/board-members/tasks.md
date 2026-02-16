# Implementation Plan: Board Member Management

## Overview

This implementation adds five new MCP tools for managing board members in the Trello MCP Server. The tools follow existing patterns in `trello_mcp_server/server.py` for tool registration, execution, and error handling. All tools use the existing `make_trello_request()` function for authenticated API calls and return `TextContent` responses.

## Tasks

- [x] 1. Add tool definitions to list_tools()
  - Add `list_board_members` tool definition with board_id parameter
  - Add `add_board_member` tool definition with board_id, member_id, and optional type parameter
  - Add `remove_board_member` tool definition with board_id and member_id parameters
  - Add `update_board_member` tool definition with board_id, member_id, and type parameters
  - Add `invite_board_member` tool definition with board_id, email, and optional type parameter
  - Include clear descriptions and JSON schemas for all parameters
  - _Requirements: 7.2, 7.3, 7.4_

- [ ] 2. Implement list_board_members tool
  - [x] 2.1 Add handler in call_tool() for "list_board_members"
    - Extract board_id from arguments
    - Call `make_trello_request("GET", f"/boards/{board_id}/members")`
    - Format response with member details (name, username, ID, permission)
    - Return TextContent with formatted member list
    - _Requirements: 1.1, 1.2, 1.5_

  - [ ]* 2.2 Write property test for list members complete data
    - **Property 1: List members returns complete data**
    - **Validates: Requirements 1.1, 1.2**

  - [ ]* 2.3 Write unit tests for list_board_members
    - Test successful member listing with valid board_id
    - Test error handling for invalid board_id
    - _Requirements: 1.1, 1.3_

- [ ] 3. Implement add_board_member tool
  - [x] 3.1 Add handler in call_tool() for "add_board_member"
    - Extract board_id, member_id from arguments
    - Extract optional type parameter (default to "normal")
    - Build query parameters with type
    - Call `make_trello_request("PUT", f"/boards/{board_id}/members/{member_id}", params={"type": type})`
    - Return TextContent with confirmation and member details
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 3.2 Write property test for add member with permission
    - **Property 3: Add member with permission**
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 3.3 Write unit tests for add_board_member
    - Test adding member with default "normal" permission
    - Test adding member with explicit "admin" permission
    - Test adding member with "observer" permission
    - Test error handling for invalid board_id or member_id
    - Test adding member who is already on board (idempotent)
    - _Requirements: 2.1, 2.3, 2.5, 2.6_

- [ ] 4. Implement remove_board_member tool
  - [x] 4.1 Add handler in call_tool() for "remove_board_member"
    - Extract board_id, member_id from arguments
    - Call `make_trello_request("DELETE", f"/boards/{board_id}/members/{member_id}")`
    - Return TextContent with confirmation
    - _Requirements: 3.1, 3.2_

  - [ ]* 4.2 Write property test for remove member effect
    - **Property 4: Remove member effect**
    - **Validates: Requirements 3.1**

  - [ ]* 4.3 Write unit tests for remove_board_member
    - Test successful member removal
    - Test error handling for invalid board_id or member_id
    - Test removing member not on board
    - Test attempting to remove last admin (should fail)
    - _Requirements: 3.1, 3.3, 3.4, 3.6_

- [ ] 5. Implement update_board_member tool
  - [x] 5.1 Add handler in call_tool() for "update_board_member"
    - Extract board_id, member_id, type from arguments
    - Validate type is one of: "admin", "normal", "observer"
    - If invalid, return validation error TextContent
    - Call `make_trello_request("PUT", f"/boards/{board_id}/members/{member_id}", params={"type": type})`
    - Return TextContent with confirmation and new permission level
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 5.2 Write property test for update permission effect
    - **Property 5: Update permission effect**
    - **Validates: Requirements 4.1**

  - [ ]* 5.3 Write property test for permission level validation
    - **Property 6: Permission level validation**
    - **Validates: Requirements 4.2, 4.6**

  - [ ]* 5.4 Write unit tests for update_board_member
    - Test updating member from "normal" to "admin"
    - Test updating member from "admin" to "observer"
    - Test validation error for invalid permission type
    - Test error handling for member not on board
    - Test attempting to downgrade last admin (should fail)
    - _Requirements: 4.1, 4.4, 4.6, 4.8_

- [ ] 6. Implement invite_board_member tool
  - [x] 6.1 Add handler in call_tool() for "invite_board_member"
    - Extract board_id, email from arguments
    - Extract optional type parameter (default to "normal")
    - Build query parameters with email and type
    - Call `make_trello_request("PUT", f"/boards/{board_id}/members", params={"email": email, "type": type})`
    - Return TextContent with confirmation
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 6.2 Write property test for invite member success
    - **Property 7: Invite member success**
    - **Validates: Requirements 5.1**

  - [ ]* 6.3 Write property test for email validation
    - **Property 8: Email validation**
    - **Validates: Requirements 5.5**

  - [ ]* 6.4 Write unit tests for invite_board_member
    - Test inviting member with default "normal" permission
    - Test inviting member with explicit "admin" permission
    - Test error handling for invalid email format
    - Test error handling for invalid board_id
    - Test inviting email that's already a board member
    - _Requirements: 5.1, 5.3, 5.5, 5.6, 5.8_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 8. Add comprehensive error handling tests
  - [ ]* 8.1 Write property test for invalid input error handling
    - **Property 9: Invalid input error handling**
    - **Validates: Requirements 1.3, 2.6, 3.4, 4.5, 5.6**

  - [ ]* 8.2 Write property test for API error propagation
    - **Property 10: API error propagation**
    - **Validates: Requirements 6.4, 8.1, 8.2, 8.3, 8.4**

  - [ ]* 8.3 Write property test for response format consistency
    - **Property 2: Response format consistency**
    - **Validates: Requirements 1.5**

  - [ ]* 8.4 Write unit tests for error scenarios
    - Test 404 error for non-existent board
    - Test 403 error for insufficient permissions
    - Test network error handling
    - Test error logging with logger.error()
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All tools follow the existing pattern in `server.py` for consistency
- Use `make_trello_request()` for all API calls (handles authentication automatically)
- All responses must be `TextContent` objects with formatted text
- Error handling follows existing pattern with try-except blocks in `call_tool()`
- Property tests should use `hypothesis` library with minimum 100 iterations
- Each property test must include a comment with feature name and property number
- Unit tests focus on specific examples and edge cases, not exhaustive input coverage
