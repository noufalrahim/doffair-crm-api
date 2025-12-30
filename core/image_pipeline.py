from core.image_utils import compress_and_resize


def generate_variants(file_bytes: bytes):
    return {
        "original": compress_and_resize(
            file_bytes,
            max_size=1920,
            quality=85,
        ),
        "medium": compress_and_resize(
            file_bytes,
            max_size=800,
            quality=80,
        ),
        "thumbnail": compress_and_resize(
            file_bytes,
            max_size=300,
            quality=70,
        ),
    }
