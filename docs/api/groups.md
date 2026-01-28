# Group API Documentation

This document provides a complete and definitive specification for the API endpoints related to creating, managing, and interacting with groups. All endpoints require authentication.

---

## 1. Core Concepts & Business Logic

### **Group Roles**

* **`admin`**: Has full permissions to manage the group, including updating its details, deleting it, and managing its members (updating roles, removing users).
* **`member`**: Can participate in the group (e.g., add expenses) but cannot perform administrative actions.

### **Join Codes**

* When a group is created, a unique, 6-character alphanumeric **join code** is automatically generated. This code is case-insensitive and is the primary mechanism for new users to join a private group.

### **Database Collections**

* **`groups`**: Stores the core group documents, including name, currency, and a list of member sub-documents.
* **`users`**: Used to enrich member data, fetching details like names and emails to display in group member lists.
* **`settlements`**: Queried to perform safety checks, specifically to prevent a user from leaving a group or being removed if they have outstanding debts.

---

## 2. Group Management

These endpoints handle the core CRUD (Create, Read, Update, Delete) operations for groups. All endpoints are prefixed with `/groups`.

### **`POST /`**

Creates a new group.

* **Server-Side Logic**:
    1.  Generates a unique, random 6-character join code.
    2.  Creates a new group document in the `groups` collection.
    3.  The user who creates the group is automatically added as the first member with the `admin` role.
* **Request Body** (`GroupCreateRequest`):
    ```json
    {
      "name": "Trip to the Mountains",
      "currency": "EUR",
      "imageUrl": "https://example.com/mountains.png"
    }
    ```
* **Response** (`GroupResponse`):
    ```json
    {
      "id": "group_id_string",
      "name": "Trip to the Mountains",
      "currency": "EUR",
      "joinCode": "UNIQUE_JOIN_CODE",
      "createdBy": "user_id_of_creator",
      "createdAt": "2025-08-14T12:00:00Z",
      "imageUrl": "https://example.com/mountains.png",
      "members": [ /* ... list of GroupMemberWithDetails ... */ ]
    }
    ```

### **`GET /`**

Lists all groups that the current user is a member of.

* **Response** (`GroupListResponse`):
    ```json
    {
      "groups": [
        { /* ... GroupResponse object 1 ... */ },
        { /* ... GroupResponse object 2 ... */ }
      ]
    }
    ```

### **`GET /{group_id}`**

Retrieves the details for a single group, including its members.

* **Server-Side Logic**:
    1.  Verifies the current user is a member of the requested group.
    2.  Fetches the group document.
    3.  Enriches the `members` list by fetching the name, email, and image URL for each member from the `users` collection.
* **Response** (`GroupResponse`): Returns the full, enriched group object.

### **`PATCH /{group_id}`**

Updates a group's metadata.

* **Permissions**: Admin only.
* **Request Body** (`GroupUpdateRequest`):
    ```json
    {
      "name": "Awesome Trip to the Mountains"
    }
    ```
* **Response** (`GroupResponse`): Returns the complete, updated group object.

### **`DELETE /{group_id}`**

Deletes an entire group.

* **Permissions**: Admin only.
* **Response** (`DeleteGroupResponse`):
    ```json
    {
      "success": true,
      "message": "Group deleted successfully"
    }
    ```

---

## 3. Group Membership

### **`POST /join`**

Allows a user to join an existing group using a unique join code.

* **Server-Side Logic**:
    1.  Finds the group associated with the provided `joinCode`.
    2.  Checks to ensure the user is not already a member.
    3.  Adds the user to the group's `members` list with the default `member` role.
* **Request Body** (`JoinGroupRequest`):
    ```json
    {
      "joinCode": "UNIQUE_JOIN_CODE"
    }
    ```
* **Response** (`JoinGroupResponse`):
    ```json
    {
      "group": { /* ... GroupResponse object for the joined group ... */ }
    }
    ```

### **`POST /{group_id}/leave`**

Allows a user to leave a group.

* **Server-Side Logic**:
    1.  Verifies the user is a member of the group.
    2.  **Safety Check**: Queries the `settlements` collection to ensure the user has no `pending` debts. If they do, the request is rejected with a `400 Bad Request`.
    3.  **Safety Check**: Prevents the last admin from leaving the group, ensuring the group is not left without an administrator.
    4.  Removes the user from the group's `members` list.
* **Response** (`LeaveGroupResponse`):
    ```json
    {
      "success": true,
      "message": "Successfully left the group"
    }
    ```

### **`GET /{group_id}/members`**

Retrieves a detailed list of all members in a specific group.

* **Response**: A list of `GroupMemberWithDetails` objects, enriched with user information.
    ```json
    [
      {
        "userId": "user_id_1",
        "role": "admin",
        "joinedAt": "2025-08-14T12:00:00Z",
        "user": { "name": "Alice", "email": "alice@example.com", "imageUrl": null }
      }
    ]
    ```

### **`PATCH /{group_id}/members/{member_id}`**

Updates the role of a specific member within a group.

* **Permissions**: Admin only.
* **Safety Check**: Prevents an admin from demoting themselves if they are the only admin in the group.
* **Request Body** (`MemberRoleUpdateRequest`):
    ```json
    {
      "role": "admin"
    }
    ```
* **Response**: `{"message": "Member role updated to admin"}`

### **`DELETE /{group_id}/members/{member_id}`**

Removes a member from a group.

* **Permissions**: Admin only.
* **Server-Side Logic**:
    1.  Verifies the requesting user is an admin.
    2.  Ensures an admin is not trying to remove themselves (they must use the `/leave` endpoint instead).
    3.  **Safety Check**: Queries the `settlements` collection to ensure the member being removed has no `pending` debts. If they do, the request is rejected.
    4.  Removes the member from the group.
* **Response** (`RemoveMemberResponse`):
    ```json
    {
      "success": true,
      "message": "Member removed successfully"
    }
    

