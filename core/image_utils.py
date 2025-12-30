from PIL import Image
import io

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def compress_and_resize(
    file_bytes: bytes,
    max_size: int,
    quality: int,
) -> bytes:
    """
    Resize image so max(width, height) == max_size
    and compress to JPEG.
    """
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")

    image.thumbnail((max_size, max_size))

    output = io.BytesIO()
    image.save(
        output,
        format="JPEG",
        quality=quality,
        optimize=True,
    )

    return output.getvalue()


def validate_image(content_type: str):
    print(content_type)
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Unsupported image type")
