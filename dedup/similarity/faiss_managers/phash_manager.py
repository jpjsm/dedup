# similarity/faiss_managers/phash_manager.py

import json
import os
import numpy as np
import faiss
import threading

from dedup.config.settings import (
    PHASH_BINARY_DIM,
    FAISS_PHASH_INDEX,
)


class PHashIndexManager:
    """
    FAISS index for perceptual hash (pHash).
    Supports load(), save(), rebuild().
    """

    def __init__(self):
        self.dim = int(PHASH_BINARY_DIM)
        self.path = FAISS_PHASH_INDEX
        self.lock = threading.Lock()
        self.id_map = {}

        self._init_index()

    # ------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------

    def _init_index(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)
        else:
            self.index = faiss.IndexFlatL2(self.dim)

    # ------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------

    def load(self):
        # Load FAISS index only if it exists
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)

            # Only load id_map if the index exists
            map_path = self.path + ".map"
            if os.path.exists(map_path):
                with open(map_path, "r") as f:
                    self.id_map = {int(k): v for k, v in json.load(f).items()}
        else:
            # If index doesn't exist, start fresh
            self._init_index()
            self.id_map = {}

    def save(self):
        faiss.write_index(self.index, self.path)
        with open(self.path + ".map", "w") as f:
            json.dump(self.id_map, f)

    # ------------------------------------------------------------
    # Rebuild from DB
    # ------------------------------------------------------------

    def rebuild(self, db):
        """
        Rebuild index from DB rows.
        """
        self.index = faiss.IndexFlatL2(self.dim)
        self.id_map.clear()

        rows = db.execute("select_all_images_with_phash")

        for file_id, phash_bytes in rows:
            bits = np.unpackbits(np.frombuffer(phash_bytes, dtype=np.uint8)).astype(
                np.float32
            )
            self.add(file_id, bits)

    # ------------------------------------------------------------
    # Add + Search
    # ------------------------------------------------------------

    def add(self, file_id, phash_bits):
        vec = phash_bits.reshape(1, -1).astype(np.float32)

        with self.lock:
            faiss_id = self.index.ntotal
            self.index.add(vec)
            self.id_map[faiss_id] = file_id

    def search(self, phash_bits, k=10):
        vec = phash_bits.reshape(1, -1).astype(np.float32)

        with self.lock:
            distances, indices = self.index.search(vec, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.id_map[idx], float(dist)))

        return results
