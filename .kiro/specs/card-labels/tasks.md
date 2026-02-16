# Implementation Plan: Card Labels

## Overview

This implementation adds five new MCP tools to the existing `trello_mcp_server/server.py` file for managing labels on Trello cards. All tools follow the established patterns for tool registration, API calls, and error handling.

## Tasks

- [x] 1. Add label tool definitions to @app.list_tools()
  - Add Tool definitions for all five label operations
  - Define input schemas with proper validation
  - Include descriptive documentation for each tool
  - _Requirements: 6.1_

- [x] 2. Implement add_card_label tool handler
  - [x] 2.1 Add handler in @app.call_tool() for "add_card_label"
    - Extract card_id and label_id from arguments
    - Call make_trello_request() with POST method to /cards/{card_id}/idLabels
    - Format response with card and label details
    - _Requirements: 1.1, 1.2, 6.2, 6.3, 6.4_
  
  - [ ]* 2.2 Write property test for label addition idempotence
    - **Property 1: Label Addition Idempotence**
    - **Validates: Requirements 1.3**

- [x] 3. Implement remove_card_label tool handler
  - [x] 3.1 Add handler in @app.call_tool() for "remove_card_label"
    - Extract card_id and label_id from arguments
    - Call make_trello_request() with DELETE method to /cards/{card_id}/idLabels/{label_id}
    - Format response with confirmation message
    - _Requirements: 2.1, 2.2, 6.2, 6.3, 6.4_
  
  - [ ]* 3.2 Write property test for label removal idempotence
    - **Property 2: Label Removal Idempotence**
    - **Validates: Requirements 2.3**

- [x] 4. Implement list_card_labels tool handler
  - [x] 4.1 Add handler in @app.call_tool() for "list_card_labels"
    - Extract card_id from arguments
    - Call make_trello_request() with GET method to /cards/{card_id}/labels
    - Format response as list of labels with name, color, and ID
    - Handle empty label list case
    - _Requirements: 3.1, 3.2, 3.3, 6.2, 6.3, 6.4_
  
  - [ ]* 4.2 Write property test for label list completeness
    - **Property 3: Label List Completeness**
    - **Validates: Requirements 3.1, 3.3**
  
  - [ ]* 4.3 Write unit test for empty label list
    - **Property 6: Empty List Handling**
    - **Validates: Requirements 3.2**

- [x] 5. Implement list_board_labels tool handler
  - [x] 5.1 Add handler in @app.call_tool() for "list_board_labels"
    - Extract board_id from arguments
    - Call make_trello_request() with GET method to /boards/{board_id}/labels
    - Format response as list of available labels with name, color, and ID
    - _Requirements: 4.1, 4.2, 6.2, 6.3, 6.4_
  
  - [ ]* 5.2 Write property test for board label availability
    - **Property 4: Board Label Availability**
    - **Validates: Requirements 4.1, 4.2**

- [x] 6. Implement filter_cards_by_label tool handler
  - [x] 6.1 Add handler in @app.call_tool() for "filter_cards_by_label"
    - Extract board_id and label_id from arguments
    - Call make_trello_request() with GET method to /boards/{board_id}/cards
    - Filter cards by checking if label_id is in card's idLabels array
    - Format response as list of cards with name, ID, and list ID
    - Handle empty results case
    - _Requirements: 5.1, 5.2, 5.3, 6.2, 6.3, 6.4_
  
  - [ ]* 6.2 Write property test for filter accuracy
    - **Property 5: Filter Accuracy**
    - **Validates: Requirements 5.1, 5.3**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 8. Write integration tests for label workflows
  - Test add label → list labels workflow
  - Test add multiple labels → filter by label workflow
  - Test remove label → list labels workflow
  - _Requirements: 1.1, 2.1, 3.1, 5.1_

- [ ]* 9. Write error handling tests
  - **Property 7: Invalid ID Error Handling**
  - Test invalid card IDs for all operations
  - Test invalid label IDs for all operations
  - Test authentication failures
  - **Validates: Requirements 1.4, 1.5, 2.4, 2.5, 3.4, 4.4, 5.4, 5.5, 8.1, 8.2, 8.3, 8.4, 8.5**

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All tool handlers follow the existing pattern in server.py
- Error handling is already implemented in the @app.call_tool() try-except block
- Authentication is handled automatically by make_trello_request()
- Each property test should run minimum 100 iterations
- Use pytest and Hypothesis for property-based testing
