import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch
from uuid import UUID

import app.services.storage as storage_module
import pytest
from fastapi import UploadFile
from firebase_admin.exceptions import FirebaseError
from PIL import Image

"""# Apply monkeypatch as a fixture
@pytest.fixture(autouse=True)
def patch_firebase(monkeypatch):
    monkeypatch.setattr("app.services.storage.storage", object())
    monkeypatch.setattr("app.services.storage.project_id", "dummy-project")

    monkeypatch.setattr(storage_module, "uuid4", lambda: UUID("12345678123456781234567812345678"))

    yield """

from app.services.storage import FirebaseStorageService

service = FirebaseStorageService()


@pytest.fixture
def fixed_uuid(monkeypatch):
    monkeypatch.setattr(
        "app.services.storage.uuid4", lambda: UUID("12345678123456781234567812345678")
    )
    yield


def test_generate_secure_file_path_with_extension(fixed_uuid):
    result = service.generate_secure_file_path("user123", "users", "image.png")
    assert result.startswith("users/user123/12345678123456781234567812345678")
    assert result.endswith(".png")


def test_generate_secure_file_path_without_extension(fixed_uuid):
    result = service.generate_secure_file_path("user123", "users", "image")
    assert result.endswith(".webp")


def test_generate_secure_file_path_empty_entity(fixed_uuid):
    result = service.generate_secure_file_path("", "users", "image.png")
    assert result.startswith("users//12345678123456781234567812345678")
    assert result.endswith(".png")


def test_generate_secure_file_path_empty_folder(fixed_uuid):
    result = service.generate_secure_file_path("user123", "", "image.png")
    assert result.startswith("/user123/12345678123456781234567812345678")
    assert result.endswith(".png")


def test_generate_secure_file_path_empty_filename(fixed_uuid):
    result = service.generate_secure_file_path("user123", "users", "")
    assert result.endswith(".webp")


def test_generate_secure_file_path_none_filename(fixed_uuid):
    result = service.generate_secure_file_path("user123", "users", None)
    assert result.endswith(".webp")
    assert "12345678123456781234567812345678.webp" in result


def test_extract_path_from_url_normal():
    """Extracts path from a normal Firebase URL without suffix."""
    url = "https://dummy-project.firebasestorage.app/o/users%2Fuser123%2Ffile.webp?alt=media"
    result = service.extract_path_from_url(url)
    assert result == "o/users%2Fuser123%2Ffile.webp"


def test_extract_path_from_url_with_suffixes():
    """Removes _thumbnail.webp, _medium.webp, and _full.webp suffixes from URL."""
    for suffix in ["_thumbnail.webp", "_medium.webp", "_full.webp"]:
        url = f"https://dummy-project.firebasestorage.app/o/users%2Fuser123%2Ffile{suffix}?alt=media"
        result = service.extract_path_from_url(url)
        assert result == "o/users%2Fuser123%2Ffile"


def test_extract_path_from_url_already_clean():
    """Returns path unchanged if no bucket name or suffix is present."""
    url = "https://example.com/path/to/file.webp"
    result = service.extract_path_from_url(url)
    assert result == "path/to/file.webp"


def test_extract_path_from_url_malformed():
    """Handles malformed URLs gracefully by returning whatever path can be parsed."""
    url = "not a valid url"
    result = service.extract_path_from_url(url)
    # urlparse still returns a path string, even if malformed
    assert result == "not a valid url"


def test_extract_path_from_url_unexpected_suffix():
    """Leaves URL unchanged if suffix is not thumbnail/medium/full."""
    url = "https://dummy-project.firebasestorage.app/o/users%2Fuser123%2Ffile_large.webp?alt=media"
    result = service.extract_path_from_url(url)
    assert result == "o/users%2Fuser123%2Ffile_large.webp"


@pytest.mark.asyncio
async def test_validate_file_valid_png(monkeypatch):
    """Returns True for a valid PNG file under max size and pixel limit."""
    # Create a small in-memory PNG
    img_bytes = io.BytesIO()
    img = Image.new("RGB", (10, 10))
    img.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    # Mock UploadFile
    file = AsyncMock(spec=UploadFile)
    file.read.return_value = img_bytes
    file.seek.return_value = None

    # Patch limits
    monkeypatch.setattr(
        "app.services.storage.settings",
        type("obj", (), {"MAX_FILE_SIZE": 5 * 1024 * 1024}),
    )
    monkeypatch.setattr(
        "app.services.storage.settings",
        type("obj", (), {"MAX_FILE_SIZE": 5 * 1024 * 1024, "MAX_IMAGE_PIXELS": 10000}),
    )

    result = await service.validate_file(file)
    assert result is True


@pytest.mark.asyncio
async def test_validate_file_oversized(monkeypatch):
    """Returns False for files exceeding MAX_FILE_SIZE."""
    img_bytes = b"x" * (5 * 1024 * 1024)  # 5MB

    file = AsyncMock(spec=UploadFile)
    file.read.return_value = img_bytes
    file.seek.return_value = None

    monkeypatch.setattr(
        "app.services.storage.settings",
        type("obj", (), {"MAX_FILE_SIZE": 5 * 1024 * 1024}),
    )

    result = await service.validate_file(file)
    assert result is False


@pytest.mark.asyncio
async def test_validate_file_corrupt_image(monkeypatch):
    """Returns False if Pillow cannot identify the image (corrupt)."""
    file = AsyncMock(spec=UploadFile)
    file.read.return_value = b"not an image"
    file.seek.return_value = None

    result = await service.validate_file(file)
    assert result is False


@pytest.mark.asyncio
async def test_validate_file_unsupported_format(monkeypatch):
    """Returns False if image format is not JPEG/PNG/WebP."""
    # Create an image with BMP format (unsupported)
    img_bytes = io.BytesIO()
    img = Image.new("RGB", (10, 10))
    img.save(img_bytes, format="BMP")
    img_bytes = img_bytes.getvalue()

    file = AsyncMock(spec=UploadFile)
    file.read.return_value = img_bytes
    file.seek.return_value = None

    monkeypatch.setattr("app.services.storage.PIL_FORMAT_TO_MIME", {"BMP": "image/bmp"})

    result = await service.validate_file(file)
    assert result is False


@pytest.mark.asyncio
async def test_validate_file_too_many_pixels(monkeypatch):
    """Returns False if image width*height exceeds MAX_IMAGE_PIXELS."""
    img_bytes = io.BytesIO()
    img = Image.new("RGB", (200, 200))  # 40,000 pixels
    img.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    file = AsyncMock(spec=UploadFile)
    file.read.return_value = img_bytes
    file.seek.return_value = None

    monkeypatch.setattr("app.services.storage.MAX_IMAGE_PIXELS", 1000)

    result = await service.validate_file(file)
    assert result is False


@pytest.mark.asyncio
async def test_save_to_quarantine_uploadfile(monkeypatch):
    """Saves an UploadFile to the quarantine directory using a secure path."""
    file_content = b"dummy content"
    file = AsyncMock(spec=UploadFile)
    file.read.return_value = file_content

    # Patch generate_secure_file_path to return a fixed filename
    monkeypatch.setattr(
        service,
        "generate_secure_file_path",
        lambda *args, **kwargs: "folder/entity/file.webp",
    )

    # Patch BASE_QUARANTINE_DIR at the module level
    mock_path = MagicMock(spec=Path)
    mock_path.__truediv__.return_value = mock_path  # for /
    monkeypatch.setattr("app.services.storage.BASE_QUARANTINE_DIR", mock_path)
    mock_path.parent.mkdir.return_value = None

    m_open = mock_open()
    with patch("builtins.open", m_open):
        result = await service.save_to_quarantine(file, "folder", "entity", "file.webp")

    assert result == str(mock_path)
    m_open.assert_called_once_with(mock_path, "wb")
    m_open().write.assert_called_once_with(file_content)


@pytest.mark.asyncio
async def test_save_to_quarantine_bytes(monkeypatch):
    """Saves raw bytes to the quarantine directory using a secure path."""
    file_content = b"raw bytes content"

    monkeypatch.setattr(
        service,
        "generate_secure_file_path",
        lambda *args, **kwargs: "folder/entity/file.webp",
    )

    # Patch BASE_QUARANTINE_DIR at the module level
    mock_path = MagicMock(spec=Path)
    mock_path.__truediv__.return_value = mock_path
    monkeypatch.setattr("app.services.storage.BASE_QUARANTINE_DIR", mock_path)
    mock_path.parent.mkdir.return_value = None

    m_open = mock_open()
    with patch("builtins.open", m_open):
        result = await service.save_to_quarantine(
            file_content, "folder", "entity", "file.webp"
        )

    assert result == str(mock_path)
    m_open.assert_called_once_with(mock_path, "wb")
    m_open().write.assert_called_once_with(file_content)


@pytest.mark.asyncio
async def test_save_to_quarantine_invalid_type(monkeypatch):
    """Raises TypeError if file is neither UploadFile nor bytes."""
    monkeypatch.setattr(
        service, "generate_secure_file_path", lambda *a, **kw: "folder/entity/file.webp"
    )
    with pytest.raises(TypeError, match="Invalid file type"):
        await service.save_to_quarantine(12345, "folder", "entity", "file.webp")


@pytest.mark.asyncio
async def test_save_to_quarantine_read_failure(monkeypatch):
    """Raises exception if UploadFile.read() fails."""
    file = AsyncMock(spec=UploadFile)
    file.read.side_effect = Exception("Read failed")

    monkeypatch.setattr(
        service, "generate_secure_file_path", lambda *a, **kw: "folder/entity/file.webp"
    )
    monkeypatch.setattr(
        "app.services.storage.BASE_QUARANTINE_DIR", MagicMock(spec=Path)
    )

    with pytest.raises(Exception, match="Read failed"):
        await service.save_to_quarantine(file, "folder", "entity", "file.webp")


@pytest.mark.asyncio
async def test_save_to_quarantine_write_failure(monkeypatch):
    """Raises RuntimeError if writing file fails."""
    file_content = b"dummy content"
    file = AsyncMock(spec=UploadFile)
    file.read.return_value = file_content

    monkeypatch.setattr(
        service, "generate_secure_file_path", lambda *a, **kw: "folder/entity/file.webp"
    )
    mock_path = MagicMock(spec=Path)
    monkeypatch.setattr("app.services.storage.BASE_QUARANTINE_DIR", mock_path)
    mock_path.__truediv__.return_value = mock_path
    mock_path.parent.mkdir.return_value = None

    # Patch open to raise IOError
    m_open = mock_open()
    m_open.side_effect = IOError("Write failed")
    with patch("builtins.open", m_open):
        with pytest.raises(RuntimeError, match="Failed to save file to quarantine"):
            await service.save_to_quarantine(file, "folder", "entity", "file.webp")


@pytest.mark.asyncio
async def test_generate_signed_url_happy():
    """Returns the signed URL when blob.generate_signed_url succeeds."""
    blob = MagicMock()
    blob.generate_signed_url.return_value = "http://signed-url.com/file.webp"

    url = await service.generate_signed_url(blob, expires_seconds=60)
    assert url == "http://signed-url.com/file.webp"
    blob.generate_signed_url.assert_called_once()


@pytest.mark.asyncio
async def test_generate_signed_url_unhappy():
    """Raises RuntimeError if blob.generate_signed_url fails."""
    blob = MagicMock()
    blob.generate_signed_url.side_effect = Exception("Firebase error")

    with pytest.raises(RuntimeError, match="Failed to generate signed URL"):
        await service.generate_signed_url(blob, expires_seconds=60)
    blob.generate_signed_url.assert_called_once()


@pytest.mark.asyncio
async def test_upload_to_firebase_emulator(monkeypatch):
    """Returns emulator URLs when use_emulator=True."""
    monkeypatch.setattr(storage_module, "use_emulator", True)

    processed_images = {"thumbnail": b"thumb", "full": b"full"}
    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    monkeypatch.setattr(storage_module.storage, "bucket", lambda name: mock_bucket)
    monkeypatch.setattr(service, "get_bucket", lambda: "bucket_name")

    urls = await service.upload_to_firebase(processed_images, "file/path")

    for size in processed_images:
        assert size in urls
        assert urls[size].startswith("http://127.0.0.1:4000/storage/")

    assert mock_blob.upload_from_string.call_count == len(processed_images)


@pytest.mark.asyncio
async def test_upload_to_firebase_signed_url(monkeypatch):
    """Returns signed URLs when use_emulator=False."""
    monkeypatch.setattr(storage_module, "use_emulator", False)

    processed_images = {"thumbnail": b"thumb"}
    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    monkeypatch.setattr(storage_module.storage, "bucket", lambda name: mock_bucket)
    monkeypatch.setattr(service, "get_bucket", lambda: "bucket_name")
    monkeypatch.setattr(
        service, "generate_signed_url", AsyncMock(return_value="http://signed-url.com")
    )

    urls = await service.upload_to_firebase(processed_images, "file/path")

    assert urls["thumbnail"] == "http://signed-url.com"
    mock_blob.upload_from_string.assert_called_once_with(
        b"thumb", content_type="image/webp"
    )
    service.generate_signed_url.assert_awaited_once_with(
        mock_blob, expires_seconds=storage_module.SIGNED_URL_EXPIRY_SECONDS
    )


@pytest.mark.asyncio
async def test_upload_to_firebase_generate_signed_url_failure(monkeypatch):
    """Raises RuntimeError if generate_signed_url fails."""
    monkeypatch.setattr(storage_module, "use_emulator", False)

    processed_images = {"thumbnail": b"thumb"}
    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    monkeypatch.setattr(storage_module.storage, "bucket", lambda name: mock_bucket)
    monkeypatch.setattr(service, "get_bucket", lambda: "bucket_name")
    monkeypatch.setattr(
        service,
        "generate_signed_url",
        AsyncMock(side_effect=Exception("signed_url fail")),
    )

    with pytest.raises(RuntimeError, match="Failed to upload image to Firebase"):
        await service.upload_to_firebase(processed_images, "file/path")


@pytest.mark.asyncio
async def test_upload_to_firebase_upload_failure(monkeypatch):
    """Raises RuntimeError if blob.upload_from_string fails."""
    monkeypatch.setattr(storage_module, "use_emulator", True)

    processed_images = {"thumbnail": b"thumb"}
    mock_blob = MagicMock()
    mock_blob.upload_from_string.side_effect = Exception("upload fail")
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    monkeypatch.setattr(storage_module.storage, "bucket", lambda name: mock_bucket)
    monkeypatch.setattr(service, "get_bucket", lambda: "bucket_name")

    with pytest.raises(RuntimeError, match="Failed to upload image to Firebase"):
        await service.upload_to_firebase(processed_images, "file/path")


@pytest.mark.asyncio
async def test_upload_to_firebase_firebase_error(monkeypatch):
    """Raises FirebaseError if storage.bucket fails with FirebaseError."""
    monkeypatch.setattr(storage_module, "use_emulator", True)

    processed_images = {"thumbnail": b"thumb"}

    def raise_firebase_error(name):
        raise FirebaseError("unknown", "Firebase error")

    monkeypatch.setattr(storage_module.storage, "bucket", raise_firebase_error)
    monkeypatch.setattr(service, "get_bucket", lambda: "bucket_name")

    with pytest.raises(FirebaseError):
        await service.upload_to_firebase(processed_images, "file/path")


@pytest.mark.asyncio
async def test_move_quarantine_to_public_success(monkeypatch, tmp_path):
    """Successfully moves a file from quarantine to public: processes image, uploads, and deletes local file."""
    # Create a dummy quarantine file
    quarantine_file = tmp_path / "file.webp"
    quarantine_file.write_bytes(b"dummy content")

    public_path = "public/folder/path"

    # Patch process_image and upload_to_firebase
    monkeypatch.setattr(
        service,
        "process_image",
        AsyncMock(return_value={"thumbnail": b"thumb", "full": b"full"}),
    )
    monkeypatch.setattr(
        service,
        "upload_to_firebase",
        AsyncMock(return_value={"thumbnail": "url_thumb", "full": "url_full"}),
    )

    urls = await service.move_quarantine_to_public(str(quarantine_file), public_path)

    # Assertions
    assert urls == {"thumbnail": "url_thumb", "full": "url_full"}
    assert not quarantine_file.exists()  # file should be deleted


@pytest.mark.asyncio
async def test_move_quarantine_to_public_file_missing(monkeypatch):
    """Raises ValueError if the quarantine file does not exist."""
    with pytest.raises(ValueError, match="Quarantine file not found"):
        await service.move_quarantine_to_public(
            "nonexistent_file.webp", "public/folder/path"
        )


@pytest.mark.asyncio
async def test_move_quarantine_to_public_process_failure(monkeypatch, tmp_path):
    """Raises RuntimeError if image processing fails; quarantine file remains on disk."""
    quarantine_file = tmp_path / "file.webp"
    quarantine_file.write_bytes(b"dummy content")

    # Patch process_image to raise an exception
    monkeypatch.setattr(
        service,
        "process_image",
        AsyncMock(side_effect=RuntimeError("Processing failed")),
    )

    with pytest.raises(RuntimeError, match="Processing failed"):
        await service.move_quarantine_to_public(
            str(quarantine_file), "public/folder/path"
        )

    # Quarantine file should still exist if processing fails
    assert quarantine_file.exists()


@pytest.mark.asyncio
async def test_move_quarantine_to_public_upload_failure(monkeypatch, tmp_path):
    """Raises RuntimeError if upload_to_firebase fails; quarantine file remains on disk."""
    quarantine_file = tmp_path / "file.webp"
    quarantine_file.write_bytes(b"dummy content")

    monkeypatch.setattr(
        service, "process_image", AsyncMock(return_value={"thumbnail": b"thumb"})
    )
    monkeypatch.setattr(
        service,
        "upload_to_firebase",
        AsyncMock(side_effect=RuntimeError("Upload failed")),
    )

    with pytest.raises(RuntimeError, match="Upload failed"):
        await service.move_quarantine_to_public(
            str(quarantine_file), "public/folder/path"
        )

    # Quarantine file should still exist if upload fails
    assert quarantine_file.exists()


@pytest.mark.asyncio
async def test_process_image_success(monkeypatch):
    """Returns processed image dictionary when image processing succeeds."""
    dummy_content = b"dummy image bytes"

    # Patch the actual process_image in image_processor.py
    monkeypatch.setattr(
        "app.services.storage.process_image",
        AsyncMock(
            return_value={"thumbnail": b"thumb", "medium": b"medium", "full": b"full"}
        ),
    )

    result = await service.process_image(dummy_content)

    assert result == {"thumbnail": b"thumb", "medium": b"medium", "full": b"full"}


@pytest.mark.asyncio
async def test_process_image_failure(monkeypatch):
    """Raises RuntimeError if the underlying image processing function fails."""
    dummy_content = b"dummy image bytes"

    # Patch the actual process_image to raise an exception
    monkeypatch.setattr(
        "app.services.storage.process_image",
        AsyncMock(side_effect=Exception("Some error")),
    )

    with pytest.raises(RuntimeError, match="Failed to process image."):
        await service.process_image(dummy_content)


@pytest.mark.asyncio
async def test_delete_image_success(monkeypatch):
    """Deletes all image size variants successfully and returns True."""
    # Mock bucket and blob
    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    monkeypatch.setattr(service, "get_bucket", lambda: "bucket_name")
    monkeypatch.setattr(storage_module.storage, "bucket", lambda name: mock_bucket)

    result = await service.delete_image("folder/file")

    assert result is True
    assert mock_blob.delete.call_count == 3
    expected_calls = [
        f"folder/file_{size}.webp" for size in ["thumbnail", "medium", "full"]
    ]
    actual_calls = [call[0][0] for call in mock_bucket.blob.call_args_list]
    assert actual_calls == expected_calls


@pytest.mark.asyncio
async def test_delete_image_failure(monkeypatch):
    """Returns False if deleting images fails due to an exception."""
    monkeypatch.setattr(service, "get_bucket", lambda: "bucket_name")

    def raise_error(name):
        raise Exception("Firebase failure")

    monkeypatch.setattr(storage_module.storage, "bucket", raise_error)

    result = await service.delete_image("folder/file")

    assert result is False


@pytest.mark.asyncio
async def test_upload_image_workflow_success(monkeypatch, tmp_path):
    """Successfully validates, saves to quarantine, processes, and uploads an image."""
    dummy_file = UploadFile(
        filename="image.png", file=tmp_path.joinpath("dummy").open("wb+")
    )
    dummy_file.file.write(b"dummy content")
    dummy_file.file.seek(0)

    # Patch validate_file, save_to_quarantine, move_quarantine_to_public
    monkeypatch.setattr(service, "validate_file", AsyncMock(return_value=True))
    monkeypatch.setattr(
        service,
        "save_to_quarantine",
        AsyncMock(return_value=str(tmp_path / "quarantine_file.webp")),
    )
    monkeypatch.setattr(
        service,
        "move_quarantine_to_public",
        AsyncMock(return_value={"thumbnail": "url_thumb"}),
    )
    monkeypatch.setattr(
        service,
        "generate_secure_file_path",
        lambda entity_id, folder, filename: f"{folder}/{entity_id}/secure_id.png",
    )

    urls = await service.upload_image_workflow(dummy_file, "users", "user123")

    assert urls == {"thumbnail": "url_thumb"}
    service.validate_file.assert_awaited_once_with(dummy_file)
    service.save_to_quarantine.assert_awaited_once()
    service.move_quarantine_to_public.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_image_workflow_invalid_file(monkeypatch):
    """Raises RuntimeError when the file is invalid."""
    dummy_file = AsyncMock()
    dummy_file.read = AsyncMock(return_value=b"dummy content")

    monkeypatch.setattr(service, "validate_file", AsyncMock(return_value=False))

    with pytest.raises(RuntimeError, match="Image upload failed."):
        await service.upload_image_workflow(dummy_file, "users", "user123")


@pytest.mark.asyncio
async def test_upload_image_workflow_processing_failure(monkeypatch, tmp_path):
    """Raises RuntimeError if moving file from quarantine to public fails."""
    dummy_file = UploadFile(
        filename="image.png", file=tmp_path.joinpath("dummy").open("wb+")
    )
    dummy_file.file.write(b"dummy content")
    dummy_file.file.seek(0)

    monkeypatch.setattr(service, "validate_file", AsyncMock(return_value=True))
    monkeypatch.setattr(
        service,
        "save_to_quarantine",
        AsyncMock(return_value=str(tmp_path / "quarantine_file.webp")),
    )
    monkeypatch.setattr(
        service,
        "move_quarantine_to_public",
        AsyncMock(side_effect=RuntimeError("Upload failed")),
    )
    monkeypatch.setattr(
        service,
        "generate_secure_file_path",
        lambda entity_id, folder, filename: f"{folder}/{entity_id}/secure_id.png",
    )

    with pytest.raises(RuntimeError, match="Image upload failed."):
        await service.upload_image_workflow(dummy_file, "users", "user123")
