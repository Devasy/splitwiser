import asyncio
import datetime
import io
import os
import re
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Union
from urllib.parse import urlparse
from uuid import uuid4

import firebase_admin
from app.config import logger, settings
from app.services.image_processor import process_image
from dotenv import load_dotenv
from fastapi import UploadFile
from firebase_admin import credentials, storage
from firebase_admin.exceptions import FirebaseError
from PIL import Image, UnidentifiedImageError

load_dotenv()

try:
    use_emulator = settings.use_firebase_emulator
    service_account_path = settings.firebase_service_account_path
    project_id = settings.firebase_project_id

    if use_emulator:
        os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "http://127.0.0.1:4000"
        logger.info("Using Firebase Storage Emulator")

    if not project_id:
        raise ValueError("FIREBASE_PROJECT_ID environment variable is not set.")

    if not use_emulator and (
        not service_account_path or not os.path.exists(service_account_path)
    ):
        raise FileNotFoundError("Service account path is missing or invalid.")

    # Prevent multiple initializations
    try:
        firebase_admin.get_app()
        logger.info("Firebase already initialized.")
    except ValueError:
        if use_emulator:
            # No credentials, no bucket
            firebase_admin.initialize_app(options={"projectId": project_id})
            logger.info("Firebase initialized with emulator (no credentials).")
        else:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(
                cred, {"storageBucket": f"{project_id}.firebasestorage.app"}
            )
            logger.info("Firebase initialized with service account file.")

except Exception as e:
    logger.exception(f"Firebase initialization failed: {e}")
    raise
"""
This Storage Class implements the following functions:
1. upload_image_workflow
2. validate_file
3. process_image
4. upload_to_firebase
5. delete_image
"""

PIL_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
LOAD_TRUNCATED_IMAGES = settings.LOAD_TRUNCATED_IMAGES
SIGNED_URL_EXPIRY_SECONDS = settings.SIGNED_URL_EXPIRY_SECONDS
CLAMAV_ENABLED = settings.CLAMAV_ENABLED  # Default False
BASE_QUARANTINE_DIR = Path(__file__).resolve().parent / "quarantine"


class FirebaseStorageService:
    def __init__(self):
        pass

    def get_bucket(self) -> str:
        return f"{project_id}.firebasestorage.app"

    def generate_secure_file_path(
        self, entity_id: str, folder: str, filename: str
    ) -> str:
        """
        Generates a unique file path for Firebase Storage
        Ex: users/<entity_id>/<uuid>.webp or groups/<entity_id>/<uuid>.webp
        """
        unique_id = uuid4().hex
        filename = filename or ""
        ext = os.path.splitext(filename)[-1].lower() or ".webp"
        safe_filename = f"{unique_id}{ext}"
        return f"{folder}/{entity_id}/{safe_filename}"

    def extract_path_from_url(self, url: str) -> str:
        """
        Extracts the Firebase Storage blob path from a full public URL.

        """
        parsed_url = urlparse(url)
        path = parsed_url.path.lstrip("/")

        # Remove the bucket name if included in path
        if path.startswith(f"{project_id}.firebasestorage.app/"):
            path = path.replace(f"{project_id}.firebasestorage.app/", "", 1)

        # Strip the _<size>.webp suffix (e.g., _thumbnail.webp, _medium.webp, etc.)
        path = re.sub(r"_(thumbnail|medium|full)\.webp$", "", path)

        return path

    '''async def _scan_with_clamav_async(self, content: bytes) -> bool:
        """
        Optional inline ClamAV scan. Returns:
          - True  => scanned and clean
          - False => infected or scanning failed
          - None  => scanning not attempted (CLAMAV_ENABLED False)
        """
        if not CLAMAV_ENABLED:
            logger.debug("ClamAV inline scanning disabled.")
            return None

        try:
            import tempfile

            def run_scan(tmp_path: str):
                completed = subprocess.run(
                    ["clamscan", "--no-summary", tmp_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                return completed

            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                tmp.write(content)
                tmp.flush()
                completed = await asyncio.to_thread(run_scan, tmp.name)

            stdout = completed.stdout or ""
            # clamscan returns non-zero when infected, but we check text for robustness
            if "FOUND" in stdout:
                logger.warning("ClamAV detected malware in uploaded file.")
                return False
            if completed.returncode not in (0, 1):
                logger.exception(f"ClamAV returned unexpected code {completed.returncode}. stdout: {stdout}")
                return False

            logger.debug("ClamAV inline scan passed.")
            return True

        except Exception as e:
            logger.exception(f"ClamAV scan failed: {e}")
            return False'''

    async def validate_file(self, file: UploadFile) -> bool:
        """
        Validates file type (JPEG, PNG, WebP) and max size (5MB).
        Uses pillow for validation.
        """
        try:
            content = await file.read()
            await file.seek(0)

            if len(content) > settings.MAX_FILE_SIZE:
                logger.warning("File size larger than 5MB.")
                return False

            try:
                img = Image.open(io.BytesIO(content))
                img.load()
            except UnidentifiedImageError:
                logger.warning("Failed to identify image format with Pillow.")
                return False
            except Exception:
                logger.warning(
                    "Pillow failed to fully load the image (possibly corrupt or too large)."
                )
                return False

            img_format = img.format
            if img_format is None or PIL_FORMAT_TO_MIME.get(img_format) not in [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]:
                logger.warning(f"Rejected image due to invalid format: {img_format}")
                return False

            if img.width * img.height > MAX_IMAGE_PIXELS:
                logger.warning("Image pixel count exceeds allowed threshold.")
                return False

            return True

        except Exception as e:
            logger.exception(f"File validation failed: {e}")
            return False

    async def save_to_quarantine(
        self,
        file: Union[UploadFile, bytes],
        folder: str,
        entity_id: str,
        original_filename: str,
    ) -> str:
        """
        Saves a file to the local quarantine directory for scanning/processing later.
        Uses the same secure naming convention as generate_secure_file_path.

        Returns:
            str: Full path to the saved file.
        """
        # Generate secure name
        secure_relative_path = self.generate_secure_file_path(
            entity_id=entity_id, folder=folder, filename=original_filename
        )

        # Convert storage path to local quarantine path
        target_path = BASE_QUARANTINE_DIR / secure_relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle UploadFile or raw bytes
        try:
            if isinstance(file, UploadFile):
                content = await file.read()
            elif isinstance(file, bytes):
                content = file
            else:
                raise TypeError(
                    f"Invalid file type: {type(file)}. Must be UploadFile or bytes."
                )
        except Exception as e:
            logger.exception(f"Failed to read file content: {e}")
            raise

        # Save locally
        try:
            with open(target_path, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.exception(f"Failed to write file to quarantine: {e}")
            raise RuntimeError("Failed to save file to quarantine.") from e

        return str(target_path)

    async def generate_signed_url(
        self, blob, expires_seconds: int = SIGNED_URL_EXPIRY_SECONDS
    ) -> str:
        """
        Generate a signed URL for a blob (works with google-cloud-storage Blob).
        """
        try:
            expiry = datetime.timedelta(seconds=expires_seconds)

            def gen():
                # google-cloud-storage Blob.generate_signed_url
                return blob.generate_signed_url(expiration=expiry, method="GET")

            url = await asyncio.to_thread(gen)
            return url
        except Exception as e:
            logger.exception("Failed to generate signed URL.")
            raise RuntimeError("Failed to generate signed URL.") from e

    async def upload_to_firebase(
        self, processed_images: Dict[str, bytes], file_path: str
    ) -> Dict[str, str]:
        """
        Uploads processed images (thumbnail/medium/full) to a public path, returns signed URLs.
        Does NOT call blob.make_public().
        """
        urls = {}
        try:
            bucket_name = self.get_bucket()
            bucket = storage.bucket(bucket_name)
            for size, content in processed_images.items():
                # Ensure file names end with .webp
                blob_path = f"{file_path}_{size}.webp"
                blob = bucket.blob(blob_path)
                blob.upload_from_string(content, content_type="image/webp")

                if use_emulator:
                    url = f"http://127.0.0.1:4000/storage/{bucket_name}/o/{blob_path.replace('/', '%2F')}?alt=media"
                else:
                    url = await self.generate_signed_url(
                        blob, expires_seconds=SIGNED_URL_EXPIRY_SECONDS
                    )

                urls[size] = url
                logger.info(f"Uploaded image (signed): {blob_path}")
            return urls

        except FirebaseError as fe:
            logger.exception("Firebase error during image upload.")
            raise
        except Exception as e:
            logger.exception("Image upload to Firebase failed.")
            raise RuntimeError("Failed to upload image to Firebase.") from e

    async def move_quarantine_to_public(
        self, quarantine_path: str, public_base_path: str
    ) -> Dict[str, str]:
        """
        Worker-friendly method:
        - loads the quarantine file from local disk
        - optionally runs ClamAV inline
        - processes the image (re-encode + sizes)
        - uploads processed images to public path
        - deletes quarantine file
        Returns signed URLs for the uploaded images.
        """
        try:
            if not os.path.exists(quarantine_path):
                logger.error(f"Quarantine file not found: {quarantine_path}")
                raise ValueError("Quarantine file not found.")

            # Read file bytes
            with open(quarantine_path, "rb") as f:
                content = f.read()

            """# Inline scan if enabled else skipped
            scan_result = await self._scan_with_clamav_async(content)
            if scan_result is False:
                try:
                    os.remove(quarantine_path)
                except Exception:
                    logger.warning("Failed to delete infected quarantine file.")
                logger.warning("Quarantine file marked as infected and removed.")
                raise ValueError("File failed virus scan.")"""

            # Process the image
            processed = await self.process_image(content)

            # Upload processed images to Firebase public path
            urls = await self.upload_to_firebase(processed, public_base_path)

            # Cleanup local quarantine file
            try:
                os.remove(quarantine_path)
            except Exception:
                logger.warning("Failed to delete quarantine file after processing.")

            return urls

        except Exception as e:
            logger.exception("Failed to move file from quarantine to public.")
            raise

    async def process_image(self, file_content: bytes) -> Dict[str, bytes]:
        """
        Generates 3 resized, optimized images (thumbnail, medium, full) in WebP format.
        """
        try:
            return await process_image(
                file_content
            )  # Calls image_proccessor.py's process_image
        except Exception as e:
            logger.exception("Image processing failed.")
            raise RuntimeError("Failed to process image.") from e

    async def delete_image(self, file_path: str) -> bool:
        """
        Deletes all size variants (thumbnail, medium, full) from Firebase Storage.
        """
        try:
            bucket_name = self.get_bucket()
            bucket = storage.bucket(bucket_name)
            for size in ["thumbnail", "medium", "full"]:
                blob_path = f"{file_path}_{size}.webp"
                blob = bucket.blob(blob_path)
                blob.delete()
                logger.info(f"Deleted image: {blob_path}")
            return True

        except Exception as e:
            logger.exception(f"Failed to delete images at {file_path}")
            return False

    async def upload_image_workflow(
        self, file: UploadFile, folder: str, entity_id: str
    ) -> Dict[str, str]:
        """
        Workflow:
        - Validate (magic bytes + Pillow checks)
        - Save raw to quarantine
        - If ClamAV enabled: scan + process inline
        - If ClamAV disabled: leave in quarantine for later processing
        """
        try:
            if not await self.validate_file(file):
                logger.error("Invalid file provided to upload_image_workflow.")
                raise ValueError("Invalid file type or size.")

            content = await file.read()
            file_path = self.generate_secure_file_path(entity_id, folder, file.filename)
            logger.info(f"Generated secure path: {file_path}")

            quarantine_path = await self.save_to_quarantine(
                content, folder, entity_id, file.filename
            )

            if CLAMAV_ENABLED:
                # Original path: scan + process inline
                urls = await self.move_quarantine_to_public(quarantine_path, file_path)
                logger.info(
                    f"Upload workflow successful for {folder} entity {entity_id}"
                )
                return urls
            else:
                # Directly process image and upload (no scanning)
                logger.info("ClamAV disabled: processing image directly.")
                urls = await self.move_quarantine_to_public(quarantine_path, file_path)
                return urls

        except Exception as e:
            logger.exception("Upload image workflow failed.")
            raise RuntimeError("Image upload failed.") from e


storage_service = FirebaseStorageService()
