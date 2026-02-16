# Design Document: Card Members Management

## Overview

This feature adds three MCP tools to the Trello MCP Server for managing card member assignments: `add_card_member`, `remove_card_member`, and `list_card_members`. These tools integrate with the existing server architecture, using the established patterns for authentication, API calls, and error handling.

The implementation follows the existing codebase patterns:
- Tools are registered in the `list_tools()` function with JSON schema definitions
- Tool handlers are added to the `call_tool()` function dispatcher
- All API calls use the `make_trello_request()` function for authenticated requests
- Responses are returned as `TextContent` objects with formatted text

## Architecture

The card members feature integrates into the existing single-file architecture in `trello_mcp_server/server.py`. No new files or modules are required.

### Component Integration

```
MCP Client
    ↓
list_tools() - Registers add_card_member, remove_card_member, list_card_members
    ↓
call_tool() - Dispatches to appropriate handler
    ↓
make_trello_request() - Executes authenticated API call
    ↓
Trello API (/cards/{id}/idMembers)
```

### Trello API Endpoints

The implementation uses these Trello REST API endpoints:

1. **Add member to card**: `POST /cards/{id}/idMembers`
   - Parameters: `value` (member_id)
   - Returns: Array of member IDs on the card

2. **Remove member from card**: `DELETE /cards/{id}/idMembers/{idMember}`
   - Returns: Array of remaining member IDs

3. **Get card members**: `GET /cards/{id}/members`
   - Returns: Array of member objects with full details

## Components and Interfaces

### Tool Definitions

Three new tools are added to the `list_tools()` function:

**add_card_member**
```python
Tool(
    name="add_card_member",
    description="Add a member to a card",
    inputSchema={
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "The ID of the card"
            },
            "member_id": {
                "type": "string",
                "description": "The ID of the member to add"
            }
        },
        "required": ["card_id", "member_id"]
    }
)
```

**remove_card_member**
```python
Tool(
    name="remove_card_member",
    description="Remove a member from a card",
    inputSchema={
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "The ID of the card"
            },
            "member_id": {
                "type": "string",
                "description": "The ID of the member to remove"
            }
        },
        "required": ["card_id", "member_id"]
    }
)
```

**list_card_members**
```python
Tool(
    name="list_card_members",
    description="List all members assigned to a card",
    inputSchema={
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "The ID of the card"
            }
        },
        "required": ["card_id"]
    }
)
```

### Tool Handlers

Three new handlers are added to the `call_tool()` function:

**add_card_member handler**
```python
elif name == "add_card_member":
    data = {"value": arguments["member_id"]}
    make_trello_request("POST", f"/cards/{arguments['card_id']}/idMembers", data=data)
    return [TextContent(
        type="text",
        text=f"Added member {arguments['member_id']} to card {arguments['card_id']}"
    )]
```

**remove_card_member handler**
```python
elif name == "remove_card_member":
    make_trello_request("DELETE", f"/cards/{arguments['card_id']}/idMembers/{arguments['member_id']}")
    return [TextContent(
        type="text",
        text=f"Removed member {arguments['member_id']} from card {arguments['card_id']}"
    )]
```

**list_card_members handler**
```python
elif name == "list_card_members":
    members = make_trello_request("GET", f"/cards/{arguments['card_id']}/members")
    if not members:
        return [TextContent(type="text", text="No members assigned to this card")]
    result = "\n".join([f"- {member['fullName']} (@{member['username']}, ID: {member['id']})" for member in members])
    return [TextContent(type="text", text=f"Members on card:\n{result}")]
```

## Data Models

The implementation works with existing Trello API data structures. No new data models are required.

### Member Object (from Trello API)

```python
{
    "id": "string",              # Member ID
    "username": "string",        # Username (e.g., "johndoe")
    "fullName": "string",        # Full name (e.g., "John Doe")
    "initials": "string",        # Initials (e.g., "JD")
    "avatarUrl": "string"        # Avatar URL
}
```

### API Request/Response Patterns

**Add Member Request**
```python
POST /cards/{card_id}/idMembers
data = {"value": member_id}
# Returns: ["member_id_1", "member_id_2", ...]
```

**Remove Member Request**
```python
DELETE /cards/{card_id}/idMembers/{member_id}
# Returns: ["member_id_1", "member_id_2", ...]
```

**List Members Request**
```python
GET /cards/{card_id}/members
# Returns: [{"id": "...", "fullName": "...", "username": "...", ...}, ...]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Add-then-list round trip

*For any* valid card and member, adding a member to a card then listing the card's members should include that member in the results.

**Validates: Requirements 1.1, 3.1**

### Property 2: Remove-then-list round trip

*For any* card with an assigned member, removing that member then listing the card's members should not include that member in the results.

**Validates: Requirements 2.1, 3.1**

### Property 3: Idempotent add operations

*For any* card and member, adding the same member to a card multiple times should not cause errors and should result in the member being assigned exactly once.

**Validates: Requirements 1.3**

### Property 4: Response includes required identifiers

*For any* add or remove operation, the response message should contain both the card_id and member_id that were operated on.

**Validates: Requirements 1.2, 7.3, 7.5**

### Property 5: Invalid card_id error handling

*For any* invalid or non-existent card_id, operations (add, remove, list) should return descriptive error messages rather than crashing.

**Validates: Requirements 1.4, 2.4, 3.4**

### Property 6: Invalid member_id error handling

*For any* invalid or non-existent member_id, add and remove operations should return descriptive error messages rather than crashing.

**Validates: Requirements 1.5, 2.5**

### Property 7: Member list format completeness

*For any* card with members, listing the members should include fullName, username, and id for each member in the formatted output.

**Validates: Requirements 3.3, 7.2**

### Property 8: Authentication error handling

*For any* operation when authentication credentials are invalid or missing, the tool should return a descriptive error message about authentication failure.

**Validates: Requirements 5.3**

### Property 9: API error handling

*For any* Trello API error response, the tool handler should catch the error, log it, and return a user-friendly error message.

**Validates: Requirements 6.1**

### Property 10: Parameter validation

*For any* tool call with missing required parameters, the tool should return a descriptive validation error indicating which parameters are required.

**Validates: Requirements 6.2**

## Error Handling

The implementation follows the existing error handling patterns in `server.py`:

### HTTP Errors

All tool handlers wrap API calls in try-except blocks:

```python
try:
    # API call
    result = make_trello_request(...)
    return [TextContent(...)]
except requests.exceptions.HTTPError as e:
    logger.error(f"Trello API error: {e}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
except Exception as e:
    logger.error(f"Error executing tool {name}: {e}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
```

### Common Error Scenarios

1. **Invalid card_id**: Trello API returns 404, handler returns "Error: 404 Client Error: Not Found"
2. **Invalid member_id**: Trello API returns 400 or 404, handler returns appropriate error message
3. **Authentication failure**: `make_trello_request()` raises exception, caught by handler
4. **Network errors**: Requests library exceptions caught and logged
5. **Missing parameters**: MCP framework validates required parameters before calling handler

### Error Response Format

All errors return `TextContent` with format: `"Error: {error_description}"`

This maintains consistency with existing tools like `get_board`, `create_card`, etc.

## Testing Strategy

The card members feature requires both unit tests and property-based tests for comprehensive coverage.

### Unit Tests

Unit tests should cover specific examples and edge cases:

1. **Successful operations**:
   - Add a member to a card and verify success message
   - Remove a member from a card and verify success message
   - List members on a card with multiple members

2. **Edge cases**:
   - List members on a card with no members (empty list)
   - Remove a member not assigned to the card (graceful handling)
   - Add a member already assigned (idempotent behavior)

3. **Error conditions**:
   - Invalid card_id for each operation
   - Invalid member_id for add/remove operations
   - Network errors and API failures

4. **Integration**:
   - Verify tools are registered in `list_tools()`
   - Verify tool schemas have correct required/optional parameters
   - Verify handlers are properly wired in `call_tool()`

### Property-Based Tests

Property-based tests should verify universal correctness properties across many generated inputs. Each test should run a minimum of 100 iterations.

**Test Configuration**:
- Use `hypothesis` library for Python property-based testing
- Configure each test with `@given` decorators for input generation
- Tag each test with comments referencing design properties

**Property Test Implementation**:

1. **Property 1: Add-then-list round trip**
   - Generate random valid card_id and member_id
   - Call add_card_member
   - Call list_card_members
   - Assert member appears in list
   - Tag: `# Feature: card-members, Property 1: Add-then-list round trip`

2. **Property 2: Remove-then-list round trip**
   - Generate card with assigned member
   - Call remove_card_member
   - Call list_card_members
   - Assert member not in list
   - Tag: `# Feature: card-members, Property 2: Remove-then-list round trip`

3. **Property 3: Idempotent add operations**
   - Generate random card_id and member_id
   - Call add_card_member twice
   - Verify no errors and member assigned once
   - Tag: `# Feature: card-members, Property 3: Idempotent add operations`

4. **Property 4: Response includes required identifiers**
   - Generate random operations
   - Verify responses contain card_id and member_id
   - Tag: `# Feature: card-members, Property 4: Response includes required identifiers`

5. **Property 5: Invalid card_id error handling**
   - Generate invalid card_ids
   - Call each operation
   - Verify error messages returned
   - Tag: `# Feature: card-members, Property 5: Invalid card_id error handling`

6. **Property 6: Invalid member_id error handling**
   - Generate invalid member_ids
   - Call add/remove operations
   - Verify error messages returned
   - Tag: `# Feature: card-members, Property 6: Invalid member_id error handling`

7. **Property 7: Member list format completeness**
   - Generate cards with members
   - Call list_card_members
   - Verify output contains fullName, username, id for each member
   - Tag: `# Feature: card-members, Property 7: Member list format completeness`

8. **Property 8: Authentication error handling**
   - Simulate missing/invalid credentials
   - Call operations
   - Verify authentication error messages
   - Tag: `# Feature: card-members, Property 8: Authentication error handling`

9. **Property 9: API error handling**
   - Simulate various API errors
   - Verify errors are caught and logged
   - Verify user-friendly messages returned
   - Tag: `# Feature: card-members, Property 9: API error handling`

10. **Property 10: Parameter validation**
    - Call tools with missing parameters
    - Verify validation error messages
    - Tag: `# Feature: card-members, Property 10: Parameter validation`

### Test Organization

Tests should be organized in a new file: `test_card_members.py`

```python
# test_card_members.py
import pytest
from hypothesis import given, strategies as st
from trello_mcp_server.server import call_tool

# Unit tests
def test_add_card_member_success():
    """Test adding a member to a card"""
    # ...

def test_list_card_members_empty():
    """Test listing members on a card with no members"""
    # ...

# Property-based tests
@given(card_id=st.text(min_size=24, max_size=24), 
       member_id=st.text(min_size=24, max_size=24))
def test_add_then_list_round_trip(card_id, member_id):
    """
    Feature: card-members, Property 1: Add-then-list round trip
    For any valid card and member, adding then listing should include the member
    """
    # ...
```

### Testing Dependencies

- `pytest>=7.0.0` - Test framework
- `hypothesis>=6.0.0` - Property-based testing library
- `pytest-asyncio>=0.21.0` - Async test support
- `responses>=0.23.0` - HTTP mocking for API tests

### Manual Testing

For interactive verification, create `test_card_members.py` script:

```bash
python test_card_members.py --card-id <card_id> --member-id <member_id>
```

This allows developers to test against real Trello cards during development.
