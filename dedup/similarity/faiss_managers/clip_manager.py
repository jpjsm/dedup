# similarity/faiss_managers/clip_manager.py

import os
import numpy as np
import faiss
import threading

from dedup.config.settings import (
    IMAGE_FLOAT_DIM,
    FAISS_IMAGE_FLOAT_INDEX,
)


class CLIPIndexManager:
    """
    FAISS index for CLIP embeddings.
    Supports load(), save(), rebuild().
    """

    def __init__(self):
        self.dim = int(IMAGE_FLOAT_DIM)
        self.path = FAISS_IMAGE_FLOAT_INDEX
        self.lock = threading.Lock()
        self.id_map = {}

        self._init_index()

    def _init_index(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)
        else:
            self.index = faiss.IndexFlatIP(self.dim)

    def load(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)

    def save(self):
        faiss.write_index(self.index, self.path)

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
