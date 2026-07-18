# dedup/core/classify.py

from dedup.config.settings import (
    IMAGE_EXT,
    AUDIO_EXT,
    VIDEO_EXT,
    DOC_EXT,
)


def classify_extension(ext: str) -> str:
    """
    Classify a file based on its extension using the canonical
    definitions loaded in settings.py (including JSON overrides).
    """
    ext = ext.lower()

    if ext in IMAGE_EXT:
        return "image"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in VIDEO_EXT:
        return "video"
    if ext in DOC_EXT:
        return "document"

    return "other"
