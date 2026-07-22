# similarity/faiss_managers/clip_manager.py

import json
import os
import numpy as np
import faiss
import threading

from dedup.config.settings import (
    CLIP_BINARY_DIM,
    FAISS_CLIP_INDEX,
)


class CLIPIndexManager:
    """
    FAISS index for CLIP embeddings.
    Supports load(), save(), rebuild().
    """

    def __init__(self):
        self.dim = int(CLIP_BINARY_DIM)
        self.path = FAISS_CLIP_INDEX
        self.lock = threading.Lock()
        self.id_map = {}

        self._init_index()

    def _init_index(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)
        else:
            self.index = faiss.IndexFlatIP(self.dim)

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
        self.index = faiss.IndexFlatIP(self.dim)
        self.id_map.clear()

        rows = db.execute("select_all_images_with_clip")

        for file_id, clip_bytes in rows:
            vec = np.frombuffer(clip_bytes, dtype=np.float32)
            vec = vec / np.linalg.norm(vec)
            self.add(file_id, vec)

    def add(self, file_id, clip_vec):
        vec = clip_vec.reshape(1, -1).astype(np.float32)

        with self.lock:
            faiss_id = self.index.ntotal
            self.index.add(vec)
            self.id_map[faiss_id] = file_id

    def search(self, clip_vec, k=10):
        vec = clip_vec.reshape(1, -1).astype(np.float32)

        with self.lock:
            scores, indices = self.index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.id_map[idx], float(score)))

        return results
