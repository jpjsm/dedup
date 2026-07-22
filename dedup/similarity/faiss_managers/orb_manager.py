# similarity/faiss_managers/orb_manager.py

import json
import os
import numpy as np
import faiss
import threading

from dedup.config.settings import (
    ORB_BINARY_DIM,
    FAISS_ORB_INDEX,
)


class ORBIndexManager:
    """
    FAISS index for ORB descriptors.
    Supports load(), save(), rebuild().
    """

    def __init__(self):
        self.dim = int(ORB_BINARY_DIM)
        self.path = FAISS_ORB_INDEX
        self.lock = threading.Lock()
        self.id_map = {}

        self._init_index()

    def _init_index(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)
        else:
            self.index = faiss.IndexFlatL2(self.dim)

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
