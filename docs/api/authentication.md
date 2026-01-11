# Authentication Service

## Overview
The Authentication Service in Splitwiser handles secure user registration, login, and session management using JWT (JSON Web Tokens) with refresh token rotation for enhanced security. It supports multiple authentication providers, including email/password and Google OAuth.This documentation is based on the backend implementation in `/backend/app/auth`.

This document provides a complete and definitive specification for the authentication API endpoints, based on the final implementation code from `routes.py`, the data models from `schemas.py`, the cryptographic logic from `security.py`, the business logic from `service.py`, and the dependency logic from `dependencies.py`.

---

## 1. System Architecture & Core Concepts

### **Security & Token Generation**

* **Password Hashing**: User passwords are never stored in plaintext. They are securely hashed using the **bcrypt** algorithm.
* **Access Tokens (JWT)**: Short-lived (15 min) JSON Web Tokens signed with the HS256 algorithm. They contain the user's ID (`sub`), an expiration timestamp (`exp`), and a `type` claim set to `"access"`.
* **Refresh Tokens**: Long-lived (30 days), cryptographically secure random strings used to obtain new access tokens. They are stored in the database and rotated upon use for enhanced security.
* **Password Reset Tokens**: Secure random strings with a short expiry (1 hour) used to authorize password changes.

### **Database Collections**

The authentication system relies on three primary MongoDB collections:

1.  **`users`**: Stores core user profile information, including email, name, hashed password (for email-based auth), and the authentication provider (`email` or `google`).
2.  **`refresh_tokens`**: Tracks all active refresh tokens. Each record links a token to a `user_id`, includes an expiration date, and has a `revoked` flag to manage sessions.
3.  **`password_resets`**: Temporarily stores password reset tokens, linking them to a `user_id` with an expiration date and a `used` flag.

### **Firebase Integration**

* The **Firebase Admin SDK** is used exclusively on the server-side to verify Google ID tokens. The application is initialized using credentials from environment variables or a service account file.

---

## 2. Dependencies

The auth module relies on:
- `fastapi.security`: For OAuth2PasswordBearer .
- `pydantic`: For request/response schemas model.(pydantic model)
- `jose`: For JWT encoding/decoding.
- `passlib`: For password hashing.
- `MongoDB driver`: (e.g.,`pymongo`) for user storage.

---

## 3. Data Models and Schemas

### User Model (in `schemas.py`)
Represents a user in the database:

### **Usage Example**

```python

from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr #EmailStr to check the syntax of email 
    name: str
    imageUrl: Optional[str] = None  #Optional field 
    currency: str = "USD" 
    created_at: datetime
```

### Token Schemas (in `schemas.py`)

### **Usage Example**

```python
class TokenData(BaseModel):
    sub: str # The user's ID
```

---

## 4.API Endpoints

All endpoints are prefixed with `/auth` via an APIRouter in `routes.py`.

### **`POST /signup/email`**
**Description**: Registers a new user with their email, password, and name and returns authentication tokens and user information.

**Parameters**:
- Request Body (JSON):
  - `email`: string (required, valid email)
  - `password`: string (required)
  - `name` : string (required)

**Request BODY** (`EmailSignupRequest`):
```json
{
      "email": "user@example.com",
      "password": "a-strong-password", // min_length: 6
      "name": "John Doe" // min_length: 1
}
```

**Responses** (`AuthResponse`):
- Note: AuthResponse conatin another pydhantic model : `UserResponse`
- 201 Created: Successful registration.
  ```json
   {
      "access_token": "your_access_token_jwt",
      "refresh_token": "your_refresh_token",
      "user": {  
        "id": "mongodb_user_id",
        "email": "user@example.com",
        "name": "John Doe",
        "imageUrl": null,
        "currency": "USD",
        "created_at": "2025-08-12T18:49:48.000Z"
      }
    }
  ```
- 400 Bad Request: User already exists or invalid input.
- 422 Unprocessable Entity: Validation error (e.g., invalid email).

**Authentication**: None.

### **`POST /login/email`**
**Description**: Authenticates a user with email and password. Verifies credentials, generates JWT tokens, and adds a new session.

**Parameters**:
- Request Body (JSON):
  - `email`: string (required)
  - `password`: string (required)

**Request Example**:
* **Request Body** (`EmailLoginRequest`):
    ```json
    {
      "email": "user@example.com",
      "password": "the-correct-password"
    }
    ```
* **Response** (`AuthResponse`): The response format is identical to the sign-up endpoint.

Error :
- 500  if authentication fails due to an unexpected error


### **`POST /login/google`**
**Description**: Handles Google OAuth login. Validates the Google ID token, creates or logs in the user, and returns Splitwiser access and refresh tokens. 

**Parameters**:
- Request Body (JSON):
  - `GoogleLoginRequest`: string (required, Google ID token)


* **Request Body** (`GoogleLoginRequest`):
    ```json
    {
      "id_token": "google_id_token_from_client"
    }
    ```
* **Response** (`AuthResponse`): The response format is identical to the sign-up endpoint.

- 500 If Google authentication fails.


### **`POST /refresh`**
**Description**: Refreshes the access token using a valid refresh token. Rotates the refresh token and updates the session.

**Parameters**:
- Request Body (JSON):
  - `RefreshTokenRequest`: string (required)

* **Request Body** (`RefreshTokenRequest`):
    ```json
    {
      "refresh_token": "the_valid_refresh_token"
    }
    ```

* **Response** (`TokenResponse`):
-   200 OK: New tokens issued.
    ```json
    {
      "access_token": "your_new_access_token",
      "refresh_token": "your_new_rotated_refresh_token"
    }
    ```
- 401 Unauthorized: Invalid or expired refresh token.

### **`POST /token/verify`**
**Description**: Verifies an access token and returns the corresponding user's information.
* **Request Body** (`TokenVerifyRequest`):
    ```json
    {
      "access_token": "the_access_token_to_verify"
    }
    ```
* **Response** (`UserResponse`):
    ```json
    {
      "id": "mongodb_user_id",
      "email": "user@example.com",
      "name": "John Doe",
      "imageUrl": "url_to_avatar_or_null",
      "currency": "USD",
      "created_at": "2025-08-12T18:49:48.000Z"
    }
    ```

### **`POST /password/reset/request`**
**Description**: Initiates the password reset process for a user.Initiates a password reset process by sending a reset link to the provided email address.

* **Request Body** (`PasswordResetRequest`):
    ```json
    {
      "email": "user-who-forgot-password@example.com"
    }
    ```
* **Response** (`SuccessResponse`):
    ```json
    {
      "success": true,
      "message": "If the email exists, a reset link has been sent"
    }
    ```
### **`POST /password/reset/confirm`**

Sets a new password for a user using a valid reset token.

* **Request Body** (`PasswordResetConfirm`):
    ```json
    {
      "reset_token": "the_token_from_the_reset_email",
      "new_password": "a_new_strong_password" // min_length: 6
    }
    ```
* **Response** (`SuccessResponse`):
    ```json
    {
      "success": true,
      "message": "Password has been reset successfully"
    }

- 400 Bad Request: Invalid or expired reset token.


## Authentication Flow

1. **Registration/Login**: User sends credentials to /signup or /login. Server validates, creates/hashes, and issues tokens.
2. **Protected Routes**: Use `Depends(get_current_user)` in FastAPI, which verifies the access token.
3. **Token Refresh**: Client monitors access token expiry and calls /refresh with refresh token.
4. **Rotation**: On refresh, new refresh token is issued, old one invalidated.
5. **Google OAuth**: Client gets Google token, sends to server. Server verifies with Google API, links to user.

## Error Codes

- 400: Bad request (e.g., duplicate email).
- 401: Unauthorized (invalid credentials/token).
- 403: Forbidden (inactive user).
- 422: Validation error (Pydantic errors).
- 500: Internal server error.

## Common Use Cases

- **New User Signup**: POST /auth/signup/email → Receive tokens → Use access token for API calls.
- **Existing User Login**:  POST /auth/login/email → Tokens.
- **Google Sign-In**: Integrate with Google SDK on frontend, send token to /auth/google/login.
- **Session Refresh**: When access token expires, use refresh token to get new pair.

## Security Considerations

- Store access tokens in memory (not localStorage for web).
- Regularly rotate secrets for JWT signing.

For more details on the overall API, see `micro-plan.md`.