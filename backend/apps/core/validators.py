"""
File upload validators for security.

These validators ensure uploaded files are safe and match their claimed types
by checking magic bytes (file signatures), file extensions, and file sizes.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Magic bytes for common image formats
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "jpeg",  # JPEG
    b"\x89PNG\r\n\x1a\n": "png",  # PNG
    b"GIF87a": "gif",  # GIF87a
    b"GIF89a": "gif",  # GIF89a
    b"RIFF": "webp",  # WebP (RIFF container)
    b"BM": "bmp",  # BMP
}

# Allowed image extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

# Maximum file sizes (in bytes)
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PHOTO_SIZE = 20 * 1024 * 1024  # 20 MB


def get_file_signature(file):
    """Read the first bytes of a file to determine its type."""
    # Save current position
    current_position = file.tell()
    file.seek(0)

    # Read first 12 bytes (enough for most signatures)
    header = file.read(12)

    # Reset file position
    file.seek(current_position)

    return header


def validate_image_magic_bytes(file):
    """
    Validate that file content matches an image format by checking magic bytes.

    This prevents attackers from uploading malicious files with fake extensions.
    """
    header = get_file_signature(file)

    # Check against known image signatures
    is_valid_image = False
    for signature in IMAGE_SIGNATURES:
        if header.startswith(signature):
            is_valid_image = True
            break

    # Special case for WebP (RIFF container with WEBP type)
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        is_valid_image = True

    if not is_valid_image:
        raise ValidationError(
            _("Invalid image file. The file content does not match a valid image format."),
            code="invalid_image_content",
        )


def validate_image_extension(file):
    """Validate that file has an allowed image extension."""
    import os

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            _("Invalid file extension '%(ext)s'. Allowed extensions: %(allowed)s"),
            code="invalid_extension",
            params={
                "ext": ext,
                "allowed": ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS)),
            },
        )


def validate_avatar_size(file):
    """Validate avatar file size (max 5 MB)."""
    if file.size > MAX_AVATAR_SIZE:
        raise ValidationError(
            _("Avatar file too large. Maximum size is %(max_size)s MB."),
            code="file_too_large",
            params={"max_size": MAX_AVATAR_SIZE // (1024 * 1024)},
        )


def validate_photo_size(file):
    """Validate photo file size (max 20 MB)."""
    if file.size > MAX_PHOTO_SIZE:
        raise ValidationError(
            _("Photo file too large. Maximum size is %(max_size)s MB."),
            code="file_too_large",
            params={"max_size": MAX_PHOTO_SIZE // (1024 * 1024)},
        )


def validate_avatar(file):
    """
    Comprehensive avatar validation.

    Validates:
    - File extension is an allowed image type
    - File content matches image magic bytes
    - File size is within limits
    """
    if file is None:
        return

    validate_image_extension(file)
    validate_image_magic_bytes(file)
    validate_avatar_size(file)


def validate_photo(file):
    """
    Comprehensive photo validation.

    Validates:
    - File extension is an allowed image type
    - File content matches image magic bytes
    - File size is within limits
    """
    if file is None:
        return

    validate_image_extension(file)
    validate_image_magic_bytes(file)
    validate_photo_size(file)
