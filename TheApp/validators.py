"""
Reusable validators for file/image fields.

Lives in its own module so Django migrations can import these without
pulling in the rest of ``TheApp.models``.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

IMAGE_MAX_BYTES = 8 * 1024 * 1024  # 8 MB
VIDEO_MAX_BYTES = 50 * 1024 * 1024  # 50 MB

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]
VIDEO_EXTENSIONS = ["mp4", "mov", "webm"]

image_extension_validator = FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)
video_extension_validator = FileExtensionValidator(allowed_extensions=VIDEO_EXTENSIONS)


def _safe_size(value):
    # Only fresh uploads need size-validation; for existing FieldFile values
    # whose underlying file is missing on disk, Django still runs validators
    # during full_clean(), and accessing `.size` raises FileNotFoundError
    # (uncatchable by Django -> 500). Treat unreadable files as "size unknown"
    # so we skip the check rather than crash the admin/save flow.
    try:
        return value.size
    except (FileNotFoundError, OSError):
        return None


def validate_image_size(value) -> None:
    """Reject uploaded images larger than :data:`IMAGE_MAX_BYTES`."""
    size = _safe_size(value)
    if size is None:
        return
    if size > IMAGE_MAX_BYTES:
        raise ValidationError(
            f"Image too large ({size // 1024} KB). Max is "
            f"{IMAGE_MAX_BYTES // 1024 // 1024} MB."
        )


def validate_video_size(value) -> None:
    """Reject uploaded videos larger than :data:`VIDEO_MAX_BYTES`."""
    size = _safe_size(value)
    if size is None:
        return
    if size > VIDEO_MAX_BYTES:
        raise ValidationError(
            f"Video too large ({size // 1024} KB). Max is "
            f"{VIDEO_MAX_BYTES // 1024 // 1024} MB."
        )
