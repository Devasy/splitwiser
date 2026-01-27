import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import firebase_admin
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    generate_reset_token,
    get_password_hash,
    verify_password,
)
from app.config import logger, settings
from app.database import get_database
from bson import ObjectId
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from jose import JWTError
from pymongo.errors import DuplicateKeyError, PyMongoError

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    # First, check if we have credentials in environment variables
    if all(
        [
            settings.firebase_type,
            settings.firebase_project_id,
            settings.firebase_private_key_id,
            settings.firebase_private_key,
            settings.firebase_client_email,
        ]
    ):
        # Create a credential dictionary from environment variables
        cred_dict = {
            "type": settings.firebase_type,
            "project_id": settings.firebase_project_id,
            "private_key_id": settings.firebase_private_key_id,
            "private_key": settings.firebase_private_key.replace(
                "\\n", "\n"
            ),  # Replace escaped newlines
            "client_email": settings.firebase_client_email,
            "client_id": settings.firebase_client_id,
            "auth_uri": settings.firebase_auth_uri,
            "token_uri": settings.firebase_token_uri,
            "auth_provider_x509_cert_url": settings.firebase_auth_provider_x509_cert_url,
            "client_x509_cert_url": settings.firebase_client_x509_cert_url,
        }
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(
            cred,
            {
                "projectId": settings.firebase_project_id,
            },
        )
        logger.info("Firebase initialized with credentials from environment variables")
    # Fall back to service account JSON file if env vars are not available
    elif os.path.exists(settings.firebase_service_account_path):
        cred = credentials.Certificate(settings.firebase_service_account_path)
        firebase_admin.initialize_app(
            cred,
            {
                "projectId": settings.firebase_project_id,
            },
        )
        logger.info("Firebase initialized with service account file")
    else:
        logger.warning("Firebase service account not found. Google auth will not work.")


class AuthService:
    def __init__(self):
        # Initializes the AuthService instance.
        pass

    def get_db(self):
        """
        Returns a database connection instance from the application's database module.
        """
        return get_database()

    async def create_user_with_email(
        self, email: str, password: str, name: str
    ) -> Dict[str, Any]:
        """
        Creates a new user account with the provided email, password, and name.

        Checks for existing users with the same email and raises an error if found. Stores the user with a hashed password and default profile fields, then generates and returns a refresh token along with the user data.

        Args:
            email: The user's email address.
            password: The user's plaintext password.
            name: The user's display name.

        Returns:
            A dictionary containing the created user document and a refresh token.

        Raises:
            HTTPException: If a user with the given email already exists.
        """
        db = self.get_db()

        # Check if user already exists
        existing_user = await db.users.find_one({"email": email})
        if existing_user:
            # Check if it's a placeholder from import
            if existing_user.get("isPlaceholder"):
                # Link this signup to the placeholder account
                logger.info(
                    f"Linking signup to placeholder account for user_id={existing_user['_id']}"
                )
                hashed_password = get_password_hash(password)
                await db.users.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "hashed_password": hashed_password,
                            "name": name,  # Update with new name if provided
                            "isPlaceholder": False,
                            "auth_provider": "email",
                            "activated_at": datetime.now(timezone.utc),
                        }
                    },
                )

                # Return the linked account
                # Update in-memory user object to match DB state
                existing_user["hashed_password"] = hashed_password
                existing_user["name"] = name
                existing_user["isPlaceholder"] = False
                existing_user["auth_provider"] = "email"
                existing_user["activated_at"] = datetime.now(timezone.utc)

                # Create refresh token
                refresh_token = await self._create_refresh_token_record(
                    str(existing_user["_id"])
                )

                return {"user": existing_user, "refresh_token": refresh_token}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists",
                )

        # Create user document
        user_doc = {
            "email": email,
            "hashed_password": get_password_hash(password),
            "name": name,
            "imageUrl": None,
            "currency": "USD",
            "created_at": datetime.now(timezone.utc),
            "auth_provider": "email",
            "firebase_uid": None,
        }

        try:
            result = await db.users.insert_one(user_doc)
            user_doc["_id"] = str(result.inserted_id)

            # Create refresh token
            refresh_token = await self._create_refresh_token_record(
                str(result.inserted_id)
            )

            return {"user": user_doc, "refresh_token": refresh_token}
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        except Exception as e:
            logger.exception("Unexpected error while creating user with email")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def authenticate_user_with_email(
        self, email: str, password: str
    ) -> Dict[str, Any]:
        """
        Authenticates a user using email and password credentials.

        Verifies the provided email and password against stored user data. If authentication succeeds, returns the user information and a new refresh token. Raises an HTTP 401 error if credentials are invalid.

        Returns:
            A dictionary containing the authenticated user and a new refresh token.
        """
        db = self.get_db()
        try:
            user = await db.users.find_one({"email": email})
        except PyMongoError as e:
            logger.error(f"Database error during user lookup: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

        if not user or not verify_password(password, user.get("hashed_password", "")):
            logger.info("Authentication failed due to invalid credentials.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Create new refresh token
        try:
            refresh_token = await self._create_refresh_token_record(str(user["_id"]))
        except Exception as e:
            logger.error(f"Failed to generate refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate refresh token",
            )
        return {"user": user, "refresh_token": refresh_token}

    async def authenticate_with_google(self, id_token: str) -> Dict[str, Any]:
        """
        Authenticates a user using a Google OAuth ID token, creating a new user if necessary.

        Verifies the provided Firebase ID token, retrieves or creates the corresponding user in the database, updates user information if needed, and issues a new refresh token. Raises an HTTP 400 error if the email is missing or if authentication fails, and HTTP 401 if the token is invalid.

        Args:
            id_token: The Firebase ID token obtained from Google OAuth.

        Returns:
            A dictionary containing the user data and a new refresh token.
        """
        try:
            # Verify the Firebase ID token
            try:
                decoded_token = firebase_auth.verify_id_token(id_token)
            except firebase_auth.InvalidIdTokenError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google ID token",
                )

            firebase_uid = decoded_token["uid"]
            email = decoded_token.get("email")
            name = decoded_token.get("name", email.split("@")[0] if email else "User")
            picture = decoded_token.get("picture")

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not provided by Google",
                )

            db = self.get_db()

            # Check if user exists
            try:
                user = await db.users.find_one(
                    {"$or": [{"email": email}, {"firebase_uid": firebase_uid}]}
                )
            except PyMongoError as e:
                logger.error("Database error while checking user: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )
            if user:
                # Check if this is a placeholder account from import
                if user.get("isPlaceholder"):
                    # Activate the placeholder account with Google credentials
                    logger.info(
                        f"Activating placeholder account via Google auth for user_id={user['_id']}"
                    )
                    update_data = {
                        "firebase_uid": firebase_uid,
                        "isPlaceholder": False,
                        "auth_provider": "google",
                        "name": name if name else user.get("name"),
                        "activated_at": datetime.now(timezone.utc),
                    }
                    if picture:
                        update_data["imageUrl"] = picture

                    try:
                        await db.users.update_one(
                            {"_id": user["_id"]}, {"$set": update_data}
                        )
                        user.update(update_data)
                    except PyMongoError as e:
                        logger.error(
                            "Failed to activate placeholder account for user_id=%s: %s",
                            user["_id"],
                            str(e),
                        )
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to activate account",
                        ) from e
                else:
                    # Regular user - update info if needed
                    update_data = {}
                    if user.get("firebase_uid") != firebase_uid:
                        update_data["firebase_uid"] = firebase_uid
                    if user.get("imageUrl") != picture and picture:
                        update_data["imageUrl"] = picture

                    if update_data:
                        try:
                            await db.users.update_one(
                                {"_id": user["_id"]}, {"$set": update_data}
                            )
                            user.update(update_data)
                        except PyMongoError as e:
                            logger.warning("Failed to update user profile: %s", str(e))
            else:
                # Create new user
                user_doc = {
                    "email": email,
                    "name": name,
                    "imageUrl": picture,
                    "currency": "USD",
                    "created_at": datetime.now(timezone.utc),
                    "auth_provider": "google",
                    "firebase_uid": firebase_uid,
                    "hashed_password": None,
                }
                try:
                    result = await db.users.insert_one(user_doc)
                    user_doc["_id"] = result.inserted_id
                    user = user_doc
                except PyMongoError as e:
                    logger.error("Failed to create new Google user: %s", str(e))
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create user",
                    )

            # Create refresh token
            try:
                refresh_token = await self._create_refresh_token_record(
                    str(user["_id"])
                )
            except Exception as e:
                logger.error(
                    "Failed to issue refresh token for Google login: %s", str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate refresh token",
                )

            return {"user": user, "refresh_token": refresh_token}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Unexpected error during Google authentication")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google authentication failed: {str(e)}",
            )

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Refreshes an access token by validating and rotating the provided refresh token.

        If the refresh token is valid and not expired, issues a new refresh token and revokes the old one. Raises an HTTP 401 error if the token is invalid, expired, or the associated user does not exist.

        Args:
            refresh_token: The refresh token string to validate and rotate.

        Returns:
            A new refresh token string.
        """
        db = self.get_db()

        # Find and validate refresh token
        try:
            token_record = await db.refresh_tokens.find_one(
                {
                    "token": refresh_token,
                    "revoked": False,
                    "expires_at": {"$gt": datetime.now(timezone.utc)},
                }
            )
        except PyMongoError as e:
            logger.error("Database error while validating refresh token: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Get user
        try:
            user = await db.users.find_one({"_id": token_record["user_id"]})
        except PyMongoError as e:
            logger.error("Error while fetching user: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        # Create new refresh token (token rotation)
        try:
            new_refresh_token = await self._create_refresh_token_record(
                str(user["_id"])
            )
        except Exception as e:
            logger.error("Failed to create new refresh token: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create refresh token",
            )

        # Revoke old token
        try:
            await db.refresh_tokens.update_one(
                {"_id": token_record["_id"]}, {"$set": {"revoked": True}}
            )
        except PyMongoError as e:
            logger.error("Failed to revoke old refresh token: %s", str(e))
        # No raise here since new token is safely issued

        return new_refresh_token

    async def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verifies an access token and retrieves the associated user.

        Args:
            token: The JWT access token to verify.

        Returns:
            The user document corresponding to the token's subject.

        Raises:
            HTTPException: If the token is invalid or the user does not exist.
        """
        from app.auth.security import verify_token

        try:
            payload = verify_token(token)
            user_id = payload.get("sub")
        except JWTError as e:
            logger.warning("JWT verification failed: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        db = self.get_db()

        try:
            user = await db.users.find_one({"_id": user_id})
        except Exception as e:
            logger.error("Error while verifying token: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        return user

    async def request_password_reset(self, email: str) -> bool:
        """
        Initiates a password reset process for the specified email address.

        If the user exists, generates a password reset token with a 1-hour expiration and stores it in the database. The reset token and link are logged for development purposes. Always returns True to avoid revealing whether the email is registered.
        """
        db = self.get_db()

        try:
            user = await db.users.find_one({"email": email})
        except PyMongoError as e:
            logger.error(
                f"Database error while fetching user by email {email}: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Internal server error during user lookup."
            )

        if not user:
            # Don't reveal if email exists or not
            return True

        # Generate reset token
        reset_token = generate_reset_token()
        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry

        try:
            # Store reset token
            await db.password_resets.insert_one(
                {
                    "user_id": user["_id"],
                    "token": reset_token,
                    "expires_at": reset_expires,
                    "used": False,
                    "created_at": datetime.utcnow(),
                }
            )
        except PyMongoError as e:
            logger.error(
                f"Database error while storing reset token for user {email}: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Internal server error during token storage."
            )

        # For development/free tier: just log the reset token
        # In production, you would send this via email
        logger.info(f"Password reset token for {email}: {reset_token[:6]}")
        logger.info(
            f"Reset link: https://yourapp.com/reset-password?token={reset_token}"
        )

        return True

    async def confirm_password_reset(self, reset_token: str, new_password: str) -> bool:
        """
        Confirms a password reset using a valid reset token and updates the user's password.

        Validates the reset token, updates the user's password, marks the token as used, and revokes all existing refresh tokens for the user to require re-authentication.

        Args:
            reset_token: The password reset token to validate.
            new_password: The new password to set for the user.

        Returns:
            True if the password reset is successful.

        Raises:
            HTTPException: If the reset token is invalid or expired.
        """
        db = self.get_db()

        try:
            # Find and validate reset token
            reset_record = await db.password_resets.find_one(
                {
                    "token": reset_token,
                    "used": False,
                    "expires_at": {"$gt": datetime.now(timezone.utc)},
                }
            )

            if not reset_record:
                logger.warning("Invalid or expired reset token")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token",
                )

            # Update user password
            new_hash = get_password_hash(new_password)
            await db.users.update_one(
                {"_id": reset_record["user_id"]},
                {"$set": {"hashed_password": new_hash}},
            )

            # Mark token as used
            await db.password_resets.update_one(
                {"_id": reset_record["_id"]}, {"$set": {"used": True}}
            )

            # Revoke all refresh tokens for this user (force re-login)
            await db.refresh_tokens.update_many(
                {"user_id": reset_record["user_id"]}, {"$set": {"revoked": True}}
            )
            logger.info(
                f"Password reset successful for user_id: {reset_record['user_id']}"
            )
            return True

        except HTTPException:
            raise  # Raising HTTPException to avoid logging again
        except Exception as e:
            logger.exception(f"Unexpected error during password reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during password reset",
            )

    async def _create_refresh_token_record(self, user_id: str) -> str:
        """
        Generates and stores a new refresh token for the specified user.

        Creates a refresh token with an expiration date and saves it in the database for token management and rotation.

        Args:
            user_id: The unique identifier of the user for whom the refresh token is created.

        Returns:
            The generated refresh token string.
        """
        db = self.get_db()

        refresh_token = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

        try:
            await db.refresh_tokens.insert_one(
                {
                    "token": refresh_token,
                    "user_id": (
                        ObjectId(user_id) if isinstance(user_id, str) else user_id
                    ),
                    "expires_at": expires_at,
                    "revoked": False,
                    "created_at": datetime.now(timezone.utc),
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to create refresh token for user_id: {user_id}. Error: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create refresh token: {str(e)}",
            )

        return refresh_token


# Create service instance
auth_service = AuthService()
