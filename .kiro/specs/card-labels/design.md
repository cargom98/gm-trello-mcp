# Design Document: Card Labels

## Overview

This design implements label management capabilities for the Trello MCP Server by adding five new MCP tools that interact with the Trello Labels API. The implementation follows the existing server architecture pattern, using the established `make_trello_request()` function for API calls and the MCP tool registration system.

All label operations will be implemented as new tool handlers in the existing `server.py` file, maintaining consistency with the current codebase structure.

## Architecture

The label management feature integrates seamlessly into the existing MCP server architecture:

```
MCP Client
    ↓
MCP Server (@app.call_tool)
    ↓
Tool Handler (label operations)
    ↓
make_trello_request()
    ↓
TrelloAuth (credentials)
    ↓
Trello API
```

No new classes or modules are required. All functionality is added to the existing `server.py` file following the established patterns for tool registration and execution.

## Components and Interfaces

### New MCP Tools

Five new tools will be added to the `@app.list_tools()` function:

#### 1. add_card_label

Adds a label to a card.

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "card_id": {
            "type": "string",
            "description": "The ID of the card"
        },
        "label_id": {
            "type": "string",
            "description": "The ID of the label to add"
        }
    },
    "required": ["card_id", "label_id"]
}
```

**API Endpoint:** `POST /cards/{card_id}/idLabels`

**Response Format:**
```
Added label to card: {card_name}
Label: {label_name} ({label_color})
Card ID: {card_id}
```

#### 2. remove_card_label

Removes a label from a card.

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "card_id": {
            "type": "string",
            "description": "The ID of the card"
        },
        "label_id": {
            "type": "string",
            "description": "The ID of the label to remove"
        }
    },
    "required": ["card_id", "label_id"]
}
```

**API Endpoint:** `DELETE /cards/{card_id}/idLabels/{label_id}`

**Response Format:**
```
Removed label from card
Card ID: {card_id}
Label ID: {label_id}
```

#### 3. list_card_labels

Lists all labels on a card.

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "card_id": {
            "type": "string",
            "description": "The ID of the card"
        }
    },
    "required": ["card_id"]
}
```

**API Endpoint:** `GET /cards/{card_id}/labels`

**Response Format:**
```
Labels on card:
- {label_name} (Color: {label_color}, ID: {label_id})
- {label_name} (Color: {label_color}, ID: {label_id})
```

#### 4. list_board_labels

Lists all available labels on a board.

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "board_id": {
            "type": "string",
            "description": "The ID of the board"
        }
    },
    "required": ["board_id"]
}
```

**API Endpoint:** `GET /boards/{board_id}/labels`

**Response Format:**
```
Available labels on board:
- {label_name} (Color: {label_color}, ID: {label_id})
- {label_name} (Color: {label_color}, ID: {label_id})
```

#### 5. filter_cards_by_label

Filters cards on a board by a specific label.

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "board_id": {
            "type": "string",
            "description": "The ID of the board"
        },
        "label_id": {
            "type": "string",
            "description": "The ID of the label to filter by"
        }
    },
    "required": ["board_id", "label_id"]
}
```

**API Endpoint:** `GET /boards/{board_id}/cards` with filter parameter

**Response Format:**
```
Cards with label {label_name}:
- {card_name} (ID: {card_id}, List: {list_id})
- {card_name} (ID: {card_id}, List: {list_id})
```

### Tool Handler Implementation

All tool handlers will be added to the existing `@app.call_tool()` function following this pattern:

```python
elif name == "add_card_label":
    data = {"value": arguments["label_id"]}
    result = make_trello_request("POST", f"/cards/{arguments['card_id']}/idLabels", data=data)
    # Format and return response
```

Each handler will:
1. Extract arguments from the `arguments` dictionary
2. Call `make_trello_request()` with appropriate method, endpoint, and data
3. Format the response as a TextContent object
4. Handle errors through the existing try-except block

## Data Models

### Label Object (from Trello API)

```python
{
    "id": str,           # Unique label identifier
    "idBoard": str,      # Board the label belongs to
    "name": str,         # Label name (may be empty string)
    "color": str,        # Color name (e.g., "green", "yellow", "red", "blue", "orange", "purple", "pink", "sky", "lime", "black")
}
```

### Card Object (relevant fields)

```python
{
    "id": str,           # Unique card identifier
    "name": str,         # Card name
    "idList": str,       # List the card belongs to
    "idLabels": [str],   # Array of label IDs attached to the card
    "labels": [Label]    # Array of full label objects
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Label Addition Idempotence

*For any* card and label, adding the same label multiple times should result in the label appearing exactly once on the card.

**Validates: Requirements 1.3**

### Property 2: Label Removal Idempotence

*For any* card and label, removing a label that is not on the card should succeed without error.

**Validates: Requirements 2.3**

### Property 3: Label List Completeness

*For any* card, the list of labels returned should match exactly the labels attached to that card in the Trello system.

**Validates: Requirements 3.1, 3.3**

### Property 4: Board Label Availability

*For any* board, all labels returned by list_board_labels should be valid labels that can be added to cards on that board.

**Validates: Requirements 4.1, 4.2**

### Property 5: Filter Accuracy

*For any* board and label, all cards returned by filter_cards_by_label should have that label attached, and no cards with that label should be omitted.

**Validates: Requirements 5.1, 5.3**

### Property 6: Empty List Handling

*For any* card with no labels, list_card_labels should return an empty list without error.

**Validates: Requirements 3.2**

### Property 7: Invalid ID Error Handling

*For any* invalid card ID or label ID, all label operations should return a descriptive error message rather than crashing.

**Validates: Requirements 1.4, 1.5, 2.4, 2.5, 3.4, 4.4, 5.4, 5.5**

### Property 8: Authentication Consistency

*For any* label operation, the authentication mechanism should be identical to existing tools, using the same TrelloAuth instance and make_trello_request() function.

**Validates: Requirements 7.1, 7.2, 7.3**

## Error Handling

All label operations follow the existing error handling pattern in `server.py`:

```python
try:
    # Tool operation
except requests.exceptions.HTTPError as e:
    logger.error(f"Trello API error: {e}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
except Exception as e:
    logger.error(f"Error executing tool {name}: {e}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
```

### Error Scenarios

1. **Invalid Card ID**: Trello API returns 404, handler returns "Error: 404 Client Error: Not Found"
2. **Invalid Label ID**: Trello API returns 400 or 404, handler returns appropriate error message
3. **Authentication Failure**: Handled by `make_trello_request()`, raises ValueError
4. **Network Errors**: Caught by HTTPError handler, logged and returned to user
5. **Unexpected Errors**: Caught by generic Exception handler, logged and returned to user

## Testing Strategy

### Unit Testing

Unit tests should verify specific examples and edge cases:

- **add_card_label**: Test adding a label to a card, verify response format
- **remove_card_label**: Test removing a label from a card, verify success
- **list_card_labels**: Test listing labels on a card with labels and without labels
- **list_board_labels**: Test listing board labels, verify all labels returned
- **filter_cards_by_label**: Test filtering cards, verify correct cards returned
- **Error cases**: Test invalid IDs, authentication failures, network errors

### Property-Based Testing

Property tests should verify universal properties across all inputs using a Python property-based testing library (e.g., Hypothesis):

- Each property test should run minimum 100 iterations
- Each test should be tagged with: **Feature: card-labels, Property {number}: {property_text}**
- Tests should generate random card IDs, label IDs, and board IDs
- Tests should verify properties hold across all generated inputs

**Property Test Examples:**

1. **Property 1 Test**: Generate random card/label pairs, add label twice, verify label appears once
2. **Property 2 Test**: Generate random card/label pairs, remove non-existent label, verify success
3. **Property 3 Test**: Generate random cards, list labels, verify completeness
4. **Property 5 Test**: Generate random board/label pairs, filter cards, verify all returned cards have the label

### Integration Testing

Integration tests should verify end-to-end workflows:

- Add a label to a card, then list labels on that card, verify label appears
- Add multiple labels to a card, filter by one label, verify card appears in results
- Remove a label from a card, then list labels, verify label is gone

### Test Configuration

- Use pytest as the test framework (consistent with existing tests)
- Configure Hypothesis to run 100 iterations per property test
- Mock Trello API responses for unit tests
- Use test fixtures for common setup (auth, card IDs, label IDs)
- Tag tests appropriately for selective execution
