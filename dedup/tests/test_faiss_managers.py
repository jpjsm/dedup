# dedup/tests/test_faiss_managers.py

import numpy as np
import os

from dedup.similarity.faiss_managers.phash_manager import PHashIndexManager
from dedup.similarity.faiss_managers.orb_manager import ORBIndexManager
from dedup.similarity.faiss_managers.clip_manager import CLIPIndexManager


def pretty(result):
    return {"ids": result[0], "distances": result[1]}


def test_faiss_managers():
    # --- 1. pHash manager ---
    ph = PHashIndexManager()

    vec1 = np.unpackbits(np.array([0b10101010] * 8, dtype=np.uint8)).astype(np.float32)
    vec2 = np.unpackbits(np.array([0b11110000] * 8, dtype=np.uint8)).astype(np.float32)

    ph.add(1, vec1)
    ph.add(2, vec2)

    res = ph.search(vec1)
    print("pHash search:", pretty(res))

    assert res[0][0] == 1  # nearest neighbor is itself

    # --- 2. ORB manager ---
    orb = ORBIndexManager()

    # ORB descriptors are 32 bytes → values 0–255
    orb_bytes1 = np.array([1] * 32, dtype=np.uint8)
    orb_bytes2 = np.array([2] * 32, dtype=np.uint8)

    orb1 = orb_bytes1.astype(np.float32)
    orb2 = orb_bytes2.astype(np.float32)

    orb.add(10, orb1)
    orb.add(20, orb2)

    res = orb.search(orb1)
    print("ORB search:", pretty(res))

    assert res[0][0] == 10

    # --- 3. CLIP manager ---
    clip = CLIPIndexManager()

    # realistic CLIP-like vectors: random float32, normalized
    clip1 = np.random.randn(512).astype(np.float32)
    clip2 = np.random.randn(512).astype(np.float32)

    # normalize like your pipeline does
    clip1 /= np.linalg.norm(clip1)
    clip2 /= np.linalg.norm(clip2)

    clip.add(100, clip1)
    clip.add(200, clip2)

    res = clip.search(clip1)
    print("CLIP search:", pretty(res))

    assert res[0][0] == 100

    # --- 4. Save + Load for all indexes ---
    print("[INFO] Testing save and load for all FAISS managers...")

    # pHash
    print("[INFO] Testing pHash save and load...")
    ph.save()
    assert os.path.exists(ph.path)

    ph2 = PHashIndexManager()
    ph2.load()
    res_ph2 = ph2.search(vec1)
    print("pHash search after reload:", pretty(res_ph2))
    assert res_ph2[0][0] == 1
    print("[INFO] pHash save and load test passed.")

    # ORB
    print("[INFO] Testing ORB save and load...")

    orb.save()
    assert os.path.exists(orb.path)

    orb2 = ORBIndexManager()
    orb2.load()
    res_orb2 = orb2.search(orb1)
    assert res_orb2[0][0] == 10
    print("[INFO] ORB save and load test passed.")

    # CLIP
    print("[INFO] Testing CLIP save and load...")

    clip.save()
    assert os.path.exists(clip.path)

    clip2 = CLIPIndexManager()
    clip2.load()
    res_clip2 = clip2.search(clip1)
    print("CLIP search after reload:", pretty(res_clip2))
    assert res_clip2[0][0] == 100
    print("[INFO] CLIP save and load test passed.")

    # Cleanup
    print("[INFO] Cleanup... removing indexes.")

    os.remove(ph.path)
    os.remove(orb.path)
    os.remove(clip.path)
    os.remove(ph.path + ".map")
    os.remove(orb.path + ".map")
    os.remove(clip.path + ".map")


if __name__ == "__main__":
    test_faiss_managers()
    print("Test completed")
