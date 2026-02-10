from io import BytesIO

import pytest
from app.services import image_processor as ip
from PIL import Image


def make_test_image(fmt="PNG", size=(200, 100), color=(255, 0, 0)):
    """Utility to generate an in-memory test image."""
    img = Image.new("RGB", size, color)
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_strip_exif_returns_new_image():
    """strip_exif should return a new image with identical pixels but no metadata."""
    img = Image.new("RGB", (10, 10), (123, 222, 111))
    clean = ip.strip_exif(img)
    assert clean.size == img.size
    assert list(clean.getdata()) == list(img.getdata())
    assert clean is not img


@pytest.mark.parametrize("fmt", ["jpeg", "png", "webp"])
def test_validate_magic_bytes_valid(fmt):
    """validate_magic_bytes should pass for JPEG, PNG, and WebP formats."""
    content = make_test_image(fmt.upper())
    ip.validate_magic_bytes(content)  # should not raise


@pytest.mark.parametrize("content", [b"notanimage", make_test_image("GIF")])
def test_validate_magic_bytes_invalid(content):
    """validate_magic_bytes should raise ValueError for unsupported formats or random bytes."""
    with pytest.raises(ValueError, match="Invalid or unsupported image type"):
        ip.validate_magic_bytes(content)


def test_resize_image_square_padding():
    """resize_image should pad non-square images to square when requested."""
    img = Image.new("RGB", (100, 50), (0, 0, 255))
    resized = ip.resize_image(img, (150, 150))
    assert resized.size == (150, 150)
    center_pixel = resized.getpixel((75, 75))
    assert center_pixel == (0, 0, 255)


def test_add_watermark_places_watermark():
    """add_watermark should overlay watermark in bottom-right of image."""
    base = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    watermark = Image.new("RGBA", (50, 50), (0, 255, 0, 128))
    out = ip.add_watermark(base, watermark)
    px = out.getpixel((190, 190))
    assert px[1] > 200  # green applied


@pytest.mark.asyncio
async def test_process_image_happy_path():
    """process_image should return resized WebP images for valid input."""
    content = make_test_image("PNG", size=(400, 400))
    results = await ip.process_image(content)
    assert set(results.keys()) == {"thumbnail", "medium", "full"}
    assert all(len(data) > 0 for data in results.values())


@pytest.mark.asyncio
async def test_process_image_invalid_format():
    """process_image should raise RuntimeError for unsupported image formats (e.g. GIF)."""
    bad_content = make_test_image("GIF")
    with pytest.raises(RuntimeError, match="Image processing failed"):
        await ip.process_image(bad_content)


@pytest.mark.asyncio
async def test_process_image_corrupted_bytes():
    """process_image should raise RuntimeError when given corrupted bytes."""
    with pytest.raises(RuntimeError, match="Image processing failed."):
        await ip.process_image(b"notanimage")


@pytest.mark.asyncio
async def test_process_image_with_watermark(monkeypatch, tmp_path):
    """process_image should apply watermark if WATERMARK_PATH is set."""
    watermark_file = tmp_path / "wm.png"
    Image.new("RGBA", (30, 30), (0, 255, 0, 255)).save(watermark_file, "PNG")

    monkeypatch.setattr(ip, "WATERMARK_PATH", str(watermark_file))

    content = make_test_image("PNG", size=(300, 300), color=(255, 255, 255))
    results = await ip.process_image(content)

    img = Image.open(BytesIO(results["thumbnail"]))
    px = img.getpixel((140, 140))  # bottom-right area
    assert px != (255, 255, 255)  # watermark altered pixel

    monkeypatch.setattr(ip, "WATERMARK_PATH", None)  # reset global
