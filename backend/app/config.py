import logging
import os
import time
from logging.config import dictConfig
from typing import Optional

from dotenv import load_dotenv
from PIL import Image, ImageFile
from pydantic import Field
from pydantic_settings import BaseSettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

load_dotenv()


class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "splitwiser"

    # JWT
    secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    # Firebase
    use_firebase_emulator: bool = Field(
        default=False, env="USE_FIREBASE_EMULATOR"
    )  # type:ignore
    firebase_project_id: Optional[str] = Field(
        default=None, env="FIREBASE_PROJECT_ID"
    )  # type:ignore
    firebase_service_account_path: str = Field(
        default="./firebase-service-account.json", env="FIREBASE_SERVICE_ACCOUNT_PATH"
    )  # type:ignore
    # Firebase service account credentials as environment variables
    firebase_type: Optional[str] = None
    firebase_private_key_id: Optional[str] = None
    firebase_private_key: Optional[str] = None
    firebase_client_email: Optional[str] = None
    firebase_client_id: Optional[str] = None
    firebase_auth_uri: Optional[str] = None
    firebase_token_uri: Optional[str] = None
    firebase_auth_provider_x509_cert_url: Optional[str] = None
    firebase_client_x509_cert_url: Optional[str] = None
    # Image validation configs
    LOAD_TRUNCATED_IMAGES: bool = False
    MAX_IMAGE_PIXELS: int = 50_00_000
    MAX_FILE_SIZE: int = 5 * 1024 * 1024
    SIGNED_URL_EXPIRY_SECONDS: int = Field(
        default=3600, env="SIGNED_URL_EXPIRY_SECONDS"
    )  # type:ignore
    CLAMAV_ENABLED: bool = False

    # App
    debug: bool = False

    # CORS - Add your frontend domain here for production
    allowed_origins: str = (
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://localhost:8081"
    )
    allow_all_origins: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

# centralized logging config
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("splitwiser")


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = logging.getLogger("splitwiser")

        logger.info(f"Incoming request: {request.method} {request.url}")

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"Response status: {response.status_code} for {request.method} {request.url}"
        )
        logger.info(f"Response time: {process_time:.2f} seconds")

        return response
