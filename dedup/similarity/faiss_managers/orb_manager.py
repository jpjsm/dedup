# similarity/faiss_managers/orb_manager.py

import os
import numpy as np
import faiss
import threading

from dedup.config.settings import (
    IMAGE_BINARY_DIM,
    FAISS_IMAGE_BINARY_INDEX,
)


class ORBIndexManager:
    """
    FAISS index for ORB descriptors.
    Supports load(), save(), rebuild().
    """

    def __init__(self):
        self.dim = int(IMAGE_BINARY_DIM)
        self.path = FAISS_IMAGE_BINARY_INDEX.replace("image_binary", "image_orb")
        self.lock = threading.Lock()
        self.id_map = {}

        self._init_index()

    def _init_index(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)
        else:
            self.index = faiss.IndexFlatL2(self.dim)

    def load(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)

    def save(self):
        faiss.write_index(self.index, self.path)

    def rebuild(self, db):
        self.index = faiss.IndexFlatL2(self.dim)
        self.id_map.clear()

        rows = db.execute("select_all_images_with_orb")

        for file_id, orb_bytes in rows:
            vec = np.frombuffer(orb_bytes, dtype=np.uint8).astype(np.float32)
            self.add(file_id, vec)

    def add(self, file_id, orb_vec):
        vec = orb_vec.reshape(1, -1).astype(np.float32)

        with self.lock:
            faiss_id = self.index.ntotal
            self.index.add(vec)
            self.id_map[faiss_id] = file_id

    def search(self, orb_vec, k=10):
        vec = orb_vec.reshape(1, -1).astype(np.float32)

        with self.lock:
            distances, indices = self.index.search(vec, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.id_map[idx], float(dist)))

        return results
