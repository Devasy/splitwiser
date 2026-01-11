import imghdr
from io import BytesIO
from typing import Dict, Tuple

from app.config import logger
from PIL import Image, ImageFile, UnidentifiedImageError

# Optional watermark path
WATERMARK_PATH = None  # Example: "app/assets/watermark.png"

# Resize targets (square thumbnail + larger sizes)
RESIZE_CONFIG = {
    "thumbnail": (150, 150),
    "medium": (300, 300),
    "full": (800, 800),
}

# Defining image file restrictions
ImageFile.LOAD_TRUNCATED_IMAGES = False
Image.MAX_IMAGE_PIXELS = 50_00_000  # 50MB in worst case


def strip_exif(image: Image.Image) -> Image.Image:
    """
    Returns a copy of the image with EXIF metadata stripped.
    """
    clean_image = Image.new(image.mode, image.size)
    clean_image.putdata(list(image.getdata()))
    return clean_image


def validate_magic_bytes(file_content: bytes):
    """
    Validates the actual file type of image
    """
    fmt = imghdr.what(None, h=file_content)
    if fmt not in ["jpeg", "png", "webp"]:
        raise ValueError("Invalid or unsupported image type.")


def add_watermark(image: Image.Image, watermark: Image.Image) -> Image.Image:
    """
    Adds watermark (bottom-right). Image and watermark must be RGBA.
    """
    image = image.convert("RGBA")
    watermark = watermark.convert("RGBA")

    # Resize watermark if larger than image
    wm_width = min(watermark.width, int(image.width * 0.3))
    wm_height = int(watermark.height * (wm_width / watermark.width))
    watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)

    # Paste watermark at bottom-right
    position = (image.width - wm_width - 10, image.height - wm_height - 10)
    image.alpha_composite(watermark, dest=position)
    return image


def resize_image(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """
    Resize image while maintaining aspect ratio and padding to square if needed.
    """
    image.thumbnail(size, Image.Resampling.LANCZOS)

    # Pad to square if needed (for thumbnails)
    if size[0] == size[1]:
        padded = Image.new("RGB", size, (255, 255, 255))
        offset = ((size[0] - image.width) // 2, (size[1] - image.height) // 2)
        padded.paste(image, offset)
        return padded

    return image


async def process_image(file_content: bytes) -> Dict[str, bytes]:
    """
    Validates, processes, resizes, strips metadata, compresses to WebP,
    and optionally watermarks the image.
    Returns a dict of resized images in WebP format.
    """
    try:
        validate_magic_bytes(file_content)

        img = Image.open(BytesIO(file_content))
        img_format = img.format.upper()

        # Validate format
        if img_format not in ["JPEG", "PNG", "WEBP"]:
            raise ValueError(f"Unsupported image format: {img_format}")

        img = strip_exif(img)

        if WATERMARK_PATH:
            watermark = Image.open(WATERMARK_PATH)
        else:
            watermark = None

        results = {}

        for label, size in RESIZE_CONFIG.items():
            resized = resize_image(img.copy(), size)

            if watermark:
                resized = add_watermark(resized, watermark)

            # Save to memory in WebP format
            buffer = BytesIO()
            resized.save(
                buffer, format="WEBP", quality=85, method=6
            )  # High quality with compression
            buffer.seek(0)

            results[label] = buffer.read()

        return results

    except UnidentifiedImageError:
        logger.exception("Uploaded file is not a valid image.")
        raise ValueError("Invalid image content.")
    except Exception as e:
        logger.exception(f"Image processing error: {e}")
        raise RuntimeError("Image processing failed.")
