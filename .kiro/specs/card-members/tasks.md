# Implementation Plan: Card Members Management

## Overview

This implementation adds three MCP tools for managing card member assignments in the Trello MCP Server. The tools (`add_card_member`, `remove_card_member`, `list_card_members`) follow existing patterns in `trello_mcp_server/server.py` for tool registration, API calls, and error handling. All changes are made to the single `server.py` file.

## Tasks

- [x] 1. Add tool definitions to list_tools() function
  - Add `add_card_member` tool with card_id and member_id parameters
  - Add `remove_card_member` tool with card_id and member_id parameters
  - Add `list_card_members` tool with card_id parameter
  - Include clear descriptions and JSON schema for each tool
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 2. Implement add_card_member handler
  - [x] 2.1 Add handler to call_tool() function
    - Create elif branch for "add_card_member"
    - Use make_trello_request() to POST to /cards/{card_id}/idMembers
    - Pass member_id as "value" in request data
    - Return TextContent with confirmation message including card_id and member_id
    - Wrap in try-except for error handling
    - _Requirements: 1.1, 1.2, 5.1, 5.5, 6.4, 6.5, 7.1, 7.3, 7.5_

  - [ ]* 2.2 Write property test for add-then-list round trip
    - **Property 1: Add-then-list round trip**
    - **Validates: Requirements 1.1, 3.1**

  - [ ]* 2.3 Write property test for idempotent add operations
    - **Property 3: Idempotent add operations**
    - **Validates: Requirements 1.3**

  - [ ]* 2.4 Write unit tests for add_card_member
    - Test successful member addition
    - Test invalid card_id error handling
    - Test invalid member_id error handling
    - _Requirements: 1.4, 1.5_

- [ ] 3. Implement remove_card_member handler
  - [x] 3.1 Add handler to call_tool() function
    - Create elif branch for "remove_card_member"
    - Use make_trello_request() to DELETE /cards/{card_id}/idMembers/{member_id}
    - Return TextContent with confirmation message including card_id and member_id
    - Wrap in try-except for error handling
    - _Requirements: 2.1, 2.2, 5.1, 5.5, 6.4, 6.5, 7.1, 7.3, 7.5_

  - [ ]* 3.2 Write property test for remove-then-list round trip
    - **Property 2: Remove-then-list round trip**
    - **Validates: Requirements 2.1, 3.1**

  - [ ]* 3.3 Write unit tests for remove_card_member
    - Test successful member removal
    - Test removing non-assigned member (edge case)
    - Test invalid card_id error handling
    - Test invalid member_id error handling
    - _Requirements: 2.3, 2.4, 2.5_

- [ ] 4. Implement list_card_members handler
  - [x] 4.1 Add handler to call_tool() function
    - Create elif branch for "list_card_members"
    - Use make_trello_request() to GET /cards/{card_id}/members
    - Handle empty member list with appropriate message
    - Format output as readable list with fullName, username, and id for each member
    - Return TextContent with formatted member list
    - Wrap in try-except for error handling
    - _Requirements: 3.1, 3.2, 3.3, 5.1, 5.5, 6.4, 6.5, 7.1, 7.2_

  - [ ]* 4.2 Write property test for member list format completeness
    - **Property 7: Member list format completeness**
    - **Validates: Requirements 3.3, 7.2**

  - [ ]* 4.3 Write unit tests for list_card_members
    - Test listing members on card with multiple members
    - Test listing members on card with no members (edge case)
    - Test invalid card_id error handling
    - _Requirements: 3.2, 3.4_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 6. Add comprehensive error handling tests
  - [ ]* 6.1 Write property test for response identifier inclusion
    - **Property 4: Response includes required identifiers**
    - **Validates: Requirements 1.2, 7.3, 7.5**

  - [ ]* 6.2 Write property test for invalid card_id error handling
    - **Property 5: Invalid card_id error handling**
    - **Validates: Requirements 1.4, 2.4, 3.4**

  - [ ]* 6.3 Write property test for invalid member_id error handling
    - **Property 6: Invalid member_id error handling**
    - **Validates: Requirements 1.5, 2.5**

  - [ ]* 6.4 Write property test for authentication error handling
    - **Property 8: Authentication error handling**
    - **Validates: Requirements 5.3**

  - [ ]* 6.5 Write property test for API error handling
    - **Property 9: API error handling**
    - **Validates: Requirements 6.1**

  - [ ]* 6.6 Write property test for parameter validation
    - **Property 10: Parameter validation**
    - **Validates: Requirements 6.2**

  - [ ]* 6.7 Write unit tests for network error handling
    - Test network errors are caught and handled gracefully
    - _Requirements: 6.3_

- [ ]* 7. Create interactive test script
  - Create test_card_members.py for manual testing
  - Support --card-id and --member-id command line arguments
  - Test all three operations against real Trello API
  - Display formatted results for verification

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All implementation happens in `trello_mcp_server/server.py`
- Tool definitions go in the `list_tools()` function (around line 268)
- Tool handlers go in the `call_tool()` function (around line 502)
- Follow existing patterns for error handling and response formatting
- Each property test should run minimum 100 iterations
- Use `hypothesis` library for property-based testing
- Tag each property test with feature name and property number
