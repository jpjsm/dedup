# similarity/image_index_manager.py

import os
import faiss
import numpy as np

from dedup.config.settings import PHASH_BINARY_DIM, ORB_BINARY_DIM, CLIP_BINARY_DIM


class ImageIndexManager:
    """
    Handles FAISS index operations for the image modality.
    Keeps MultimodalSimilarityEngine clean and modality-agnostic.
    """

    def __init__(self):
        self.binary = None
        self.float = None

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------

    def _ensure_dir(self, path: str):
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _load_binary(self, path: str, dim: int):
        try:
            return faiss.read_index_binary(path)
        except Exception:
            return faiss.IndexBinaryFlat(dim)

    def _load_float(self, path: str, dim: int):
        try:
            return faiss.read_index(path)
        except Exception:
            return faiss.IndexFlatIP(dim)

    def _save_binary(self, index, path: str):
        self._ensure_dir(path)
        faiss.write_index_binary(index, path)

    def _save_float(self, index, path: str):
        self._ensure_dir(path)
        faiss.write_index(index, path)

    # ------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------

    def load(self):
        """
        Load image FAISS indexes from disk.
        Missing indexes are created empty.
        """
        self.binary = self._load_binary(
            FAISS_IMAGE_BINARY_INDEX,
            int(PHASH_BINARY_DIM),
        )
        self.float = self._load_float(
            FAISS_IMAGE_FLOAT_INDEX,
            int(IMAGE_FLOAT_DIM),
        )

    def save(self):
        """
        Persist image FAISS indexes to disk.
        """
        if self.binary is not None:
            self._save_binary(self.binary, FAISS_IMAGE_BINARY_INDEX)
        if self.float is not None:
            self._save_float(self.float, FAISS_IMAGE_FLOAT_INDEX)

    # ------------------------------------------------------------
    # Rebuild
    # ------------------------------------------------------------

    def rebuild(self, db):
        """
        Rebuild image FAISS indexes from DB.
        """
        rows = db.get_all_image_vectors()

        self.binary = faiss.IndexBinaryFlat(PHASH_BINARY_DIM)
        self.float = faiss.IndexFlatIP(IMAGE_FLOAT_DIM)

        for file_id, phash_blob, emb_blob in rows:
            phash_bits = np.frombuffer(phash_blob, dtype=np.uint8)
            emb = np.frombuffer(emb_blob, dtype=np.float32)

            bin_idx = self.binary.ntotal
            float_idx = self.float.ntotal

            self.binary.add(phash_bits.reshape(1, -1))
            self.float.add(emb.reshape(1, -1))

            db.update_image_faiss_index(file_id, bin_idx, float_idx)

        self.save()

    # ------------------------------------------------------------
    # Add
    # ------------------------------------------------------------

    def add(self, db, file_id, phash_bits: np.ndarray, embedding: np.ndarray):
        """
        Add a single image to FAISS indexes.
        """
        bin_idx = self.binary.ntotal
        float_idx = self.float.ntotal

        self.binary.add(phash_bits.reshape(1, -1))
        self.float.add(embedding.reshape(1, -1))

        db.update_image_faiss_index(file_id, bin_idx, float_idx)

    # ------------------------------------------------------------
    # Search
    # ------------------------------------------------------------

    def search_by_phash(self, db, file_id: int, k: int = 10):
        phash_blob = db.get_phash(file_id)
        phash_bits = np.frombuffer(phash_blob, dtype=np.uint8)

        D, I = self.binary.search(phash_bits.reshape(1, -1), k)
        return db.lookup_files_by_image_index(I[0], distances=D[0])

    def search_by_embedding(self, db, file_id: int, k: int = 10):
        emb_blob = db.get_image_embedding(file_id)
        emb = np.frombuffer(emb_blob, dtype=np.float32)

        D, I = self.float.search(emb.reshape(1, -1), k)
        return db.lookup_files_by_image_index(I[0], distances=D[0])
