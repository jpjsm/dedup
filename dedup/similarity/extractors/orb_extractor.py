# similarity/extractors/orb_extractor.py

import cv2
import numpy as np


def extract_orb_descriptor(path: str) -> bytes:
    """
    Compute ORB descriptors for an image and return a fixed-size 32-byte vector.

    ORB normally produces many descriptors (each 32 bytes). For deduplication,
    we compute the mean descriptor, which is stable and works well for FAISS
    binary indexing.

    Returns:
        bytes: 32-byte mean ORB descriptor (uint8).
    """
    # Load image in grayscale (ORB works on grayscale)
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return bytes([0] * 32)

    # Create ORB extractor
    orb = cv2.ORB_create(nfeatures=500)

    # Compute keypoints + descriptors
    keypoints, descriptors = orb.detectAndCompute(img, None)

    if descriptors is None or len(descriptors) == 0:
        # No descriptors found (blank image, low contrast, etc.)
        return bytes([0] * 32)

    # Compute mean descriptor (32 bytes)
    mean_desc = descriptors.mean(axis=0).astype(np.uint8)

    return mean_desc.tobytes()
