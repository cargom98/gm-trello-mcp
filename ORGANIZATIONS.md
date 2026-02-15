# Organization/Workspace Management

This document describes how to use the organization/workspace management tools in the Trello MCP server.

## Overview

Organizations (also called Workspaces in Trello) allow teams to collaborate on multiple boards. These tools let you manage organizations, their boards, and members programmatically.

## Available Tools

### list_organizations

List all organizations/workspaces you belong to.

**Parameters:** None

**Example:**
```
Use the list_organizations tool to see all your workspaces
```

**Response:**
```
Your Organizations/Workspaces:
- My Team Workspace (ID: 5f8a1b2c3d4e5f6g7h8i9j0k, Name: myteam)
- Personal Projects (ID: 1a2b3c4d5e6f7g8h9i0j1k2l, Name: personal)
```

### get_organization

Get detailed information about a specific organization.

**Parameters:**
- `org_id` (required): The ID or name of the organization

**Example:**
```
Get details for organization "myteam"
```

**Response:**
```
Organization: My Team Workspace
ID: 5f8a1b2c3d4e5f6g7h8i9j0k
Name: myteam
Description: Our team's collaborative workspace
URL: https://trello.com/myteam
Website: https://example.com
```

### list_organization_boards

Get all boards in an organization.

**Parameters:**
- `org_id` (required): The ID or name of the organization

**Example:**
```
List all boards in organization "myteam"
```

**Response:**
```
Boards in organization:
- Sprint Planning (ID: 1a2b3c4d5e6f7g8h)
- Product Roadmap (ID: 2b3c4d5e6f7g8h9i)
- Bug Tracking (ID: 3c4d5e6f7g8h9i0j)
```

### list_organization_members

Get all members of an organization.

**Parameters:**
- `org_id` (required): The ID or name of the organization

**Example:**
```
List all members in organization "myteam"
```

**Response:**
```
Members in organization:
- John Doe (@johndoe, ID: 5a6b7c8d9e0f1g2h)
- Jane Smith (@janesmith, ID: 6b7c8d9e0f1g2h3i)
- Bob Wilson (@bobwilson, ID: 7c8d9e0f1g2h3i4j)
```

### add_organization_member

Add a new member to an organization.

**Parameters:**
- `org_id` (required): The ID or name of the organization
- `email` (required): Email address of the member to add
- `full_name` (optional): Full name of the member
- `type` (optional): Member type - 'normal' or 'admin' (defaults to 'normal')

**Example:**
```
Add member with email "newuser@example.com" to organization "myteam"
```

**Response:**
```
Added member to organization: New User
```

**Note:** Requires admin permissions in the organization.

### remove_organization_member

Remove a member from an organization.

**Parameters:**
- `org_id` (required): The ID or name of the organization
- `member_id` (required): The ID of the member to remove

**Example:**
```
Remove member "5a6b7c8d9e0f1g2h" from organization "myteam"
```

**Response:**
```
Removed member 5a6b7c8d9e0f1g2h from organization
```

**Note:** Requires admin permissions in the organization.

## Common Workflows

### Workflow 1: Audit Organization Membership

```
1. List all organizations
2. For each organization, list members
3. Review member list for access control
```

### Workflow 2: Onboard New Team Member

```
1. List organizations to find the right workspace
2. Add the new member using their email
3. List organization boards to share relevant board links
```

### Workflow 3: Organization Board Overview

```
1. List all organizations
2. For each organization, list all boards
3. Get details for specific boards of interest
```

### Workflow 4: Remove Departing Team Member

```
1. List organization members to find the member ID
2. Remove the member from the organization
3. Verify removal by listing members again
```

## Permissions

- **Viewing organizations, boards, and members**: Available to all organization members
- **Adding members**: Requires admin permissions in the organization
- **Removing members**: Requires admin permissions in the organization

## Tips

- You can use either the organization ID or the organization name (short name) for `org_id`
- Organization names are case-sensitive
- When adding members, they will receive an email invitation
- Removing a member removes their access to all boards in the organization
- Use `list_organizations` first to get the correct org_id for other operations

## Error Handling

Common errors you might encounter:

- **"Organization not found"**: Check that the org_id is correct
- **"Insufficient permissions"**: You need admin access for member management
- **"Member already exists"**: The email is already a member of the organization
- **"Invalid email"**: The email format is incorrect

## API Rate Limits

Trello API has rate limits. If you're making many requests:
- Add delays between requests
- Batch operations when possible
- Cache organization and member lists locally
