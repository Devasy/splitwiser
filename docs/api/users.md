# User Profile API Documentation

This document provides a detailed specification for the API endpoints related to managing a user's own profile. All endpoints require authentication.

---

## 1. User Profile Management

These endpoints handle the retrieval, updating, and deletion of the currently authenticated user's profile. All endpoints are prefixed with `/users`.

### **`GET /me`**
Retrieves the complete profile information for the currently authenticated user.

* **Server-Side Logic**:
    1.  The user's ID is extracted from their authentication token.
    2.  The `users` collection in the database is queried to find the corresponding user document.
    3.  The raw database document is transformed into the public-facing `UserProfileResponse` format, ensuring fields like `_id` are correctly mapped to `id`.
* **Response** (`UserProfileResponse`):
    ```json
    {
      "id": "user_id_string",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "imageUrl": "https://example.com/path/to/avatar.png",
      "currency": "USD",
      "createdAt": "2025-08-12T10:00:00Z",
      "updatedAt": "2025-08-15T15:00:00Z"
    }
    ```

### **`PATCH /me`**
Updates the profile information for the currently authenticated user.

* **Server-Side Logic**:
    1.  The user's ID is extracted from their authentication token.
    2.  The system filters the incoming request body to ensure only allowed fields (`name`, `imageUrl`, `currency`) can be updated.
    3.  The `updated_at` timestamp is automatically set to the current time.
    4.  The user's document in the `users` collection is updated with the new information.
* **Request Body** (`UserProfileUpdateRequest`):
    ```json
    {
      "name": "Johnathan Doe",
      "imageUrl": "https://example.com/path/to/new_avatar.png"
    }
    ```
* **Response**: A dictionary containing the updated user object.
    ```json
    {
        "user": {
            "id": "user_id_string",
            "name": "Johnathan Doe",
            "email": "john.doe@example.com",
            "imageUrl": "https://example.com/path/to/new_avatar.png",
            "currency": "USD",
            "createdAt": "2025-08-12T10:00:00Z",
            "updatedAt": "2025-08-15T15:05:00Z"
        }
    }
    ```

### **`DELETE /me`**
Schedules the currently authenticated user's account for deletion.

* **Server-Side Logic**:
    1.  The user's ID is extracted from their authentication token.
    2.  The corresponding user document is permanently deleted from the `users` collection.
    *(Note: In a production system, this might be a "soft delete" where the user is marked as inactive, but the current implementation is a "hard delete".)*
* **Response** (`DeleteUserResponse`):
    ```json
    {
      "success": true,
      "message": "User account scheduled for deletion."
    }
    