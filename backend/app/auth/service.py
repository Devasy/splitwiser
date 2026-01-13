import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import firebase_admin
from app.auth.schemas import UserResponse
from app.auth.security import (
    create_refresh_token,
    generate_reset_token,
    get_password_hash,
    verify_password,
)
from app.config import settings
from app.database import get_database
from bson import ObjectId
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from pymongo.errors import DuplicateKeyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    if all(
        [
            settings.firebase_type,
            settings.firebase_project_id,
            settings.firebase_private_key_id,
            settings.firebase_private_key,
            settings.firebase_client_email,
        ]
    ):
        cred_dict = {
            "type": settings.firebase_type,
            "project_id": settings.firebase_project_id,
            "private_key_id": settings.firebase_private_key_id,
            "private_key": settings.firebase_private_key.replace("\\n", "\n"),
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
        pass

    def get_db(self):
        return get_database()

    async def create_user_with_email(
        self, email: str, password: str, name: str
    ) -> Dict[str, Any]:
        db = self.get_db()

        existing_user = await db.users.find_one({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        user_doc = {
            "email": email,
            "hashed_password": get_password_hash(password),
            "name": name,
            "avatar": None,
            "currency": "USD",
            "created_at": datetime.now(timezone.utc),
            "auth_provider": "email",
            "firebase_uid": None,
            "failed_login_attempts": 0,
            "lockout_until": None,
        }

        try:
            result = await db.users.insert_one(user_doc)
            user_doc["_id"] = str(result.inserted_id)

            refresh_token = await self._create_refresh_token_record(
                str(result.inserted_id)
            )

            return {"user": user_doc, "refresh_token": refresh_token}
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    async def authenticate_user_with_email(
        self, email: str, password: str
    ) -> Dict[str, Any]:
        db = self.get_db()

        user = await db.users.find_one({"email": email})

        if not user:
            logger.warning(f"Failed login attempt for non-existent user: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if user.get("lockout_until") and user["lockout_until"] > datetime.now(
            timezone.utc
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked. Please try again later.",
            )

        if not verify_password(password, user.get("hashed_password", "")):
            await self._handle_failed_login(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        await self._reset_failed_login_attempts(user)
        refresh_token = await self._create_refresh_token_record(str(user["_id"]))

        return {"user": user, "refresh_token": refresh_token}

    async def _handle_failed_login(self, user: Dict[str, Any]):
        db = self.get_db()
        new_attempts = user.get("failed_login_attempts", 0) + 1

        update_data = {"$set": {"failed_login_attempts": new_attempts}}

        if new_attempts >= MAX_FAILED_ATTEMPTS:
            lockout_until = datetime.now(timezone.utc) + LOCKOUT_DURATION
            update_data["$set"]["lockout_until"] = lockout_until
            logger.warning(f"Account for user {user['email']} has been locked.")

        await db.users.update_one({"_id": user["_id"]}, update_data)
        logger.warning(f"Failed login attempt for user: {user['email']}")

    async def _reset_failed_login_attempts(self, user: Dict[str, Any]):
        db = self.get_db()
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"failed_login_attempts": 0, "lockout_until": None}},
        )

    async def authenticate_with_google(self, id_token: str) -> Dict[str, Any]:
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
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

            user = await db.users.find_one(
                {"$or": [{"email": email}, {"firebase_uid": firebase_uid}]}
            )

            if user:
                update_data = {}
                if user.get("firebase_uid") != firebase_uid:
                    update_data["firebase_uid"] = firebase_uid
                if user.get("avatar") != picture and picture:
                    update_data["avatar"] = picture

                if update_data:

                    try:
                        await db.users.update_one(
                            {"_id": user["_id"]}, {"$set": update_data}
                        )
                        user.update(update_data)
                    except PyMongoError as e:
                        logger.warning("Failed to update user profile: %s", str(e))
            else:
                user_doc = {
                    "email": email,
                    "name": name,
                    "avatar": picture,
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

        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google ID token",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google authentication failed: {str(e)}",
            )

    async def refresh_access_token(self, refresh_token: str) -> str:
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

        user = await db.users.find_one({"_id": token_record["user_id"]})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        new_refresh_token = await self._create_refresh_token_record(str(user["_id"]))

        await db.refresh_tokens.update_one(
            {"_id": token_record["_id"]}, {"$set": {"revoked": True}}
        )

        return new_refresh_token

    async def verify_access_token(self, token: str) -> Dict[str, Any]:
        from app.auth.security import verify_token

        payload = verify_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        db = self.get_db()
        user = await db.users.find_one({"_id": ObjectId(user_id)})

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        return user

    async def request_password_reset(self, email: str) -> bool:
        db = self.get_db()

        user = await db.users.find_one({"email": email})
        if not user:
            return True

        reset_token = generate_reset_token()

        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry

        await db.password_resets.insert_one(
            {
                "user_id": user["_id"],
                "token": reset_token,
                "expires_at": reset_expires,
                "used": False,
                "created_at": datetime.utcnow(),
            }
        )

        logger.info(f"Password reset token for {email}: {reset_token}")
        logger.info(
            f"Reset link: https://yourapp.com/reset-password?token={reset_token}"
        )

        return True

    async def confirm_password_reset(self, reset_token: str, new_password: str) -> bool:
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        new_hash = get_password_hash(new_password)
        await db.users.update_one(
            {"_id": reset_record["user_id"]}, {"$set": {"hashed_password": new_hash}}
        )

        await db.password_resets.update_one(
            {"_id": reset_record["_id"]}, {"$set": {"used": True}}
        )

        await db.refresh_tokens.update_many(
            {"user_id": reset_record["user_id"]}, {"$set": {"revoked": True}}
        )

        return True

    async def _create_refresh_token_record(self, user_id: str) -> str:
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


auth_service = AuthService()
