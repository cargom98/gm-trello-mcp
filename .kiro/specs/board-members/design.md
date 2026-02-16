# Design Document: Board Member Management

## Overview

This feature adds comprehensive board member management capabilities to the Trello MCP Server. It enables programmatic control over board memberships, including listing members, adding/removing members, updating permissions, and inviting new members via email.

The implementation follows the established patterns in the server:
- Tool registration via `@app.list_tools()` decorator
- Tool execution through `@app.call_tool()` dispatcher
- Authenticated API calls using `make_trello_request()`
- Error handling with descriptive TextContent responses

All operations interact with the Trello REST API at `https://api.trello.com/1` using OAuth 1.0a authentication managed by the `TrelloAuth` class.

## Architecture

### Component Overview

```
MCP Client
    ↓
MCP Server (@app.call_tool)
    ↓
Board Member Tools
    ↓
make_trello_request()
    ↓
TrelloAuth (API key + OAuth token)
    ↓
Trello REST API
```

### Tool Structure

The feature introduces five new MCP tools:

1. **list_board_members** - Retrieve all members of a board
2. **add_board_member** - Add an existing user to a board
3. **remove_board_member** - Remove a user from a board
4. **update_board_member** - Change a member's permission level
5. **invite_board_member** - Invite a new member via email

Each tool follows the standard pattern:
- Defined in `list_tools()` with JSON schema
- Implemented in `call_tool()` with error handling
- Uses `make_trello_request()` for API communication
- Returns `TextContent` with formatted results

## Components and Interfaces

### Tool Definitions

#### list_board_members

**Purpose:** Retrieve all members of a board with their permission levels

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

**API Endpoint:** `GET /boards/{board_id}/members`

**Query Parameters:**
- `fields`: "id,username,fullName"
- `member_fields`: "all"

**Response Format:**
```
Board Members:
- John Doe (@johndoe, ID: abc123, Permission: admin)
- Jane Smith (@janesmith, ID: def456, Permission: normal)
```

#### add_board_member

**Purpose:** Add an existing Trello user to a board

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "board_id": {
            "type": "string",
            "description": "The ID of the board"
        },
        "member_id": {
            "type": "string",
            "description": "The ID of the member to add"
        },
        "type": {
            "type": "string",
            "description": "Permission level: 'admin', 'normal', or 'observer' (optional, defaults to 'normal')"
        }
    },
    "required": ["board_id", "member_id"]
}
```

**API Endpoint:** `PUT /boards/{board_id}/members/{member_id}`

**Query Parameters:**
- `type`: Permission level (admin, normal, observer)

**Response Format:**
```
Added member to board: John Doe (@johndoe)
Permission: normal
```

#### remove_board_member

**Purpose:** Remove a member from a board

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "board_id": {
            "type": "string",
            "description": "The ID of the board"
        },
        "member_id": {
            "type": "string",
            "description": "The ID of the member to remove"
        }
    },
    "required": ["board_id", "member_id"]
}
```

**API Endpoint:** `DELETE /boards/{board_id}/members/{member_id}`

**Response Format:**
```
Removed member {member_id} from board
```

#### update_board_member

**Purpose:** Update a member's permission level on a board

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "board_id": {
            "type": "string",
            "description": "The ID of the board"
        },
        "member_id": {
            "type": "string",
            "description": "The ID of the member to update"
        },
        "type": {
            "type": "string",
            "description": "New permission level: 'admin', 'normal', or 'observer'"
        }
    },
    "required": ["board_id", "member_id", "type"]
}
```

**API Endpoint:** `PUT /boards/{board_id}/members/{member_id}`

**Query Parameters:**
- `type`: New permission level (admin, normal, observer)

**Response Format:**
```
Updated member permission: John Doe (@johndoe)
New permission: admin
```

#### invite_board_member

**Purpose:** Invite a new member to a board via email

**Input Schema:**
```python
{
    "type": "object",
    "properties": {
        "board_id": {
            "type": "string",
            "description": "The ID of the board"
        },
        "email": {
            "type": "string",
            "description": "Email address of the person to invite"
        },
        "type": {
            "type": "string",
            "description": "Permission level: 'admin', 'normal', or 'observer' (optional, defaults to 'normal')"
        }
    },
    "required": ["board_id", "email"]
}
```

**API Endpoint:** `PUT /boards/{board_id}/members`

**Query Parameters:**
- `email`: Email address
- `type`: Permission level (admin, normal, observer)

**Response Format:**
```
Invited {email} to board
Permission: normal
```

### Implementation Pattern

All tools follow this execution pattern:

```python
elif name == "tool_name":
    # 1. Extract and validate arguments
    board_id = arguments["board_id"]
    
    # 2. Build API request parameters
    data = {}
    if "optional_param" in arguments:
        data["optional_param"] = arguments["optional_param"]
    
    # 3. Make authenticated API call
    result = make_trello_request("METHOD", f"/endpoint/{board_id}", data=data)
    
    # 4. Format and return response
    return [TextContent(
        type="text",
        text=f"Operation result: {formatted_output}"
    )]
```

### Error Handling

All tools use try-except blocks in `call_tool()`:

```python
try:
    # Tool implementation
except requests.exceptions.HTTPError as e:
    logger.error(f"Trello API error: {e}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
except Exception as e:
    logger.error(f"Error executing tool {name}: {e}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
```

Common error scenarios:
- **404 Not Found**: Invalid board_id or member_id
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions (not board admin)
- **400 Bad Request**: Invalid parameters (e.g., invalid permission type)

## Data Models

### Board Member Object

Returned by Trello API for board members:

```python
{
    "id": "string",              # Member ID
    "username": "string",        # Username (e.g., "johndoe")
    "fullName": "string",        # Full name (e.g., "John Doe")
    "memberType": "string"       # Permission level: "admin", "normal", "observer"
}
```

### Permission Levels

Valid values for the `type` parameter:

- **admin**: Full control over board (can add/remove members, change settings)
- **normal**: Can create and edit cards, move cards between lists
- **observer**: Read-only access to the board

### API Request/Response Patterns

#### GET /boards/{id}/members
**Request:** No body, query params for fields
**Response:** Array of member objects

#### PUT /boards/{id}/members/{memberId}
**Request:** Query param `type` for permission level
**Response:** Member object or success confirmation

#### DELETE /boards/{id}/members/{memberId}
**Request:** No body
**Response:** Empty or success confirmation

#### PUT /boards/{id}/members (invite)
**Request:** Query params `email` and `type`
**Response:** Success confirmation or error


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing the acceptance criteria, several properties can be consolidated:

- Properties 1.3, 2.6, 3.4, 4.5, and 5.6 all test error handling for invalid IDs - these can be combined into a single comprehensive property about invalid input handling
- Properties 2.4, 3.2, 4.3, and 5.4 all test response format for successful operations - these can be combined into a property about successful operation responses
- Properties 4.2 and 4.6 both test permission level validation - these are the same property stated differently
- Properties 8.1, 8.2, 8.3, and 8.4 all test error response format - these can be combined into a single property about error responses

The following properties provide unique validation value after consolidation:

### Property 1: List members returns complete data

*For any* valid board ID, when listing board members, the response should include member ID, username, full name, and permission level for each member.

**Validates: Requirements 1.1, 1.2**

### Property 2: Response format consistency

*For any* valid tool response, the result should be wrapped in TextContent with properly formatted text.

**Validates: Requirements 1.5**

### Property 3: Add member with permission

*For any* valid board ID, member ID, and permission level (admin, normal, observer), adding the member should result in that member appearing in the board's member list with the specified permission.

**Validates: Requirements 2.1, 2.2**

### Property 4: Remove member effect

*For any* valid board ID and member ID, after removing a member from the board, that member should no longer appear in the board's member list.

**Validates: Requirements 3.1**

### Property 5: Update permission effect

*For any* valid board ID, member ID, and new permission level, after updating the member's permission, querying the board members should show the member with the new permission level.

**Validates: Requirements 4.1**

### Property 6: Permission level validation

*For any* permission level value that is not one of "admin", "normal", or "observer", operations requiring a permission level should reject the value with a validation error.

**Validates: Requirements 4.2, 4.6**

### Property 7: Invite member success

*For any* valid board ID and properly formatted email address, inviting a member should complete successfully and return confirmation.

**Validates: Requirements 5.1**

### Property 8: Email validation

*For any* string that does not match valid email format (missing @, invalid domain, etc.), the invite operation should reject it with a validation error.

**Validates: Requirements 5.5**

### Property 9: Invalid input error handling

*For any* invalid board ID or member ID (non-existent, malformed), operations should return a descriptive error message indicating which ID is invalid.

**Validates: Requirements 1.3, 2.6, 3.4, 4.5, 5.6**

### Property 10: API error propagation

*For any* Trello API error response, the MCP server should return a TextContent response containing descriptive error details from the API.

**Validates: Requirements 6.4, 8.1, 8.2, 8.3, 8.4**

## Error Handling

### Error Categories

#### 1. Invalid Input Errors

**Scenario:** Invalid board_id, member_id, or malformed parameters

**Handling:**
- Trello API returns 404 Not Found or 400 Bad Request
- `make_trello_request()` raises `requests.exceptions.HTTPError`
- Caught in `call_tool()` try-except block
- Returns `TextContent` with error message: "Error: {API error details}"
- Logged via `logger.error()`

**Example:**
```python
try:
    result = make_trello_request("GET", f"/boards/invalid_id/members")
except requests.exceptions.HTTPError as e:
    logger.error(f"Trello API error: {e}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
```

#### 2. Validation Errors

**Scenario:** Invalid permission level or email format

**Handling:**
- For permission levels: Validate before API call
- For emails: Trello API validates and returns 400 Bad Request
- Return descriptive validation error message
- Logged via `logger.error()`

**Example:**
```python
valid_permissions = ["admin", "normal", "observer"]
if permission_type not in valid_permissions:
    return [TextContent(
        type="text",
        text=f"Error: Invalid permission type. Must be one of: {', '.join(valid_permissions)}"
    )]
```

#### 3. Authorization Errors

**Scenario:** User lacks admin permission on board

**Handling:**
- Trello API returns 401 Unauthorized or 403 Forbidden
- `make_trello_request()` raises `requests.exceptions.HTTPError`
- Caught in `call_tool()` try-except block
- Returns `TextContent` with authorization error message
- Logged via `logger.error()`

**Example Response:**
```
Error: 403 Forbidden - You do not have permission to modify this board
```

#### 4. Business Logic Errors

**Scenario:** Attempting to remove last admin, member already exists, etc.

**Handling:**
- Trello API enforces business rules
- Returns 400 Bad Request with descriptive message
- Propagated through standard error handling
- User receives clear explanation of why operation failed

#### 5. Network Errors

**Scenario:** Connection timeout, DNS failure, network unavailable

**Handling:**
- `requests` library raises connection exceptions
- Caught in `call_tool()` generic exception handler
- Returns `TextContent` with connection error message
- Logged via `logger.error()`

**Example:**
```python
except Exception as e:
    logger.error(f"Error executing tool {name}: {e}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
```

### Error Response Format

All errors follow consistent format:
```
Error: {descriptive message}
```

Examples:
- `Error: 404 Not Found - Board not found`
- `Error: Invalid permission type. Must be one of: admin, normal, observer`
- `Error: 403 Forbidden - Insufficient permissions to add members`
- `Error: Connection timeout - Unable to reach Trello API`

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs
- Both are complementary and necessary

### Unit Testing

Unit tests focus on:

1. **Specific Examples**
   - Adding a member with "normal" permission (default behavior)
   - Updating a member from "normal" to "admin"
   - Removing a specific member
   - Inviting a member with a specific email

2. **Edge Cases**
   - Adding a member who is already on the board (idempotent)
   - Removing a member who is not on the board
   - Attempting to remove the last admin (should fail)
   - Attempting to downgrade the last admin (should fail)
   - Inviting an email that's already a member

3. **Error Conditions**
   - Invalid board ID (404 error)
   - Invalid member ID (404 error)
   - Invalid permission type (validation error)
   - Invalid email format (validation error)
   - Insufficient permissions (403 error)

4. **Integration Points**
   - Tool registration in `list_tools()`
   - Tool execution through `call_tool()`
   - API calls through `make_trello_request()`
   - Response formatting as `TextContent`

### Property-Based Testing

**Library:** `hypothesis` for Python

**Configuration:** Minimum 100 iterations per property test

**Tag Format:** Each test must include a comment:
```python
# Feature: board-members, Property {number}: {property_text}
```

**Property Tests:**

1. **Property 1: List members returns complete data**
   - Generate: Random valid board IDs
   - Action: Call `list_board_members`
   - Verify: Response contains id, username, fullName, memberType for each member

2. **Property 2: Response format consistency**
   - Generate: Random valid tool calls
   - Action: Execute tool
   - Verify: Response is list of TextContent objects

3. **Property 3: Add member with permission**
   - Generate: Random board IDs, member IDs, permission levels
   - Action: Add member, then list members
   - Verify: Member appears with correct permission

4. **Property 4: Remove member effect**
   - Generate: Random board IDs, member IDs
   - Action: Remove member, then list members
   - Verify: Member no longer appears in list

5. **Property 5: Update permission effect**
   - Generate: Random board IDs, member IDs, new permissions
   - Action: Update permission, then list members
   - Verify: Member has new permission level

6. **Property 6: Permission level validation**
   - Generate: Random invalid permission strings
   - Action: Attempt to add/update with invalid permission
   - Verify: Returns validation error

7. **Property 7: Invite member success**
   - Generate: Random valid board IDs, valid email addresses
   - Action: Invite member
   - Verify: Returns success confirmation

8. **Property 8: Email validation**
   - Generate: Random invalid email strings
   - Action: Attempt to invite with invalid email
   - Verify: Returns validation error

9. **Property 9: Invalid input error handling**
   - Generate: Random invalid board/member IDs
   - Action: Attempt operations with invalid IDs
   - Verify: Returns descriptive error message

10. **Property 10: API error propagation**
    - Generate: Random API error scenarios
    - Action: Trigger API errors
    - Verify: Error details propagated in TextContent

### Test Implementation Notes

**Mocking Strategy:**
- Mock `make_trello_request()` to simulate API responses
- Mock Trello API error responses for error testing
- Use real API calls for integration tests (optional, requires test board)

**Test Data:**
- Use hypothesis strategies for generating valid/invalid inputs
- Board IDs: 24-character hex strings
- Member IDs: 24-character hex strings
- Emails: Valid/invalid email patterns
- Permissions: Valid set + random invalid strings

**Avoiding Excessive Unit Tests:**
- Don't write separate unit tests for every possible input combination
- Property tests handle comprehensive input coverage
- Unit tests focus on specific examples and integration points
- Aim for ~10-15 unit tests, not 50+

### Test File Structure

```python
# test_board_members.py

import pytest
from hypothesis import given, strategies as st
from trello_mcp_server.server import call_tool

# Unit Tests
def test_add_member_default_permission():
    """Test adding member with default 'normal' permission"""
    # Specific example test
    pass

def test_remove_last_admin_fails():
    """Test that removing last admin is prevented"""
    # Edge case test
    pass

# Property Tests
@given(
    board_id=st.text(min_size=24, max_size=24),
    member_id=st.text(min_size=24, max_size=24),
    permission=st.sampled_from(["admin", "normal", "observer"])
)
def test_property_add_member_with_permission(board_id, member_id, permission):
    """
    Feature: board-members, Property 3: Add member with permission
    For any valid board ID, member ID, and permission level,
    adding the member should result in that member appearing
    in the board's member list with the specified permission.
    """
    # Property test implementation
    pass
```

### Coverage Goals

- **Line coverage**: >90% for new code
- **Branch coverage**: >85% for error handling paths
- **Property coverage**: All 10 properties implemented as tests
- **Edge case coverage**: All identified edge cases tested
