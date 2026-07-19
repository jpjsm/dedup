# similarity/extractors/phash_extractor.py

from PIL import Image
import imagehash
import numpy as np


def extract_phash(path: str) -> bytes:
    """
    Compute a perceptual hash (pHash) for an image and return it as packed bytes.

    Returns:
        bytes: 8-byte packed bitstring representing the 64-bit pHash.
    """
    img = Image.open(path)
    ph = imagehash.phash(img)  # 64-bit perceptual hash

    # imagehash gives you a 8x8 boolean matrix → convert to uint8 bits → pack into bytes
    packed = np.packbits(np.array(ph.hash, dtype=np.uint8))

    return packed.tobytes()  # exactly 8 bytes
