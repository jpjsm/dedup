# dedup/similarity/multimodal_similarity_engine.py

from similarity.faiss_managers.phash_manager import PHashIndexManager
from similarity.faiss_managers.orb_manager import ORBIndexManager
from similarity.faiss_managers.clip_manager import CLIPIndexManager


class MultimodalSimilarityEngine:
    """
    Orchestrates all modality-specific FAISS managers.
    Keeps FAISS logic out of the engine.
    Future modalities (audio, video, documents) plug in cleanly.
    """

    def __init__(self, db_adapter, config):
        self.db = db_adapter
        self.cfg = config

        # -----------------------------
        # Modality managers
        # -----------------------------
        self.images = {
            "phash": PHashIndexManager(),
            "orb": ORBIndexManager(),
            "clip": CLIPIndexManager(),
        }

        # Future-ready placeholders
        # self.audio = AudioIndexManager()
        # self.video = VideoIndexManager()
        # self.documents = DocumentIndexManager()

    # ------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------

    def load(self):
        # Each manager may implement load() if persistence is added later
        for mgr in self.images.values():
            if hasattr(mgr, "load"):
                mgr.load()

        # Future:
        # self.audio.load()
        # self.video.load()
        # self.documents.load()

    def save(self):
        for mgr in self.images.values():
            if hasattr(mgr, "save"):
                mgr.save()

        # Future:
        # self.audio.save()
        # self.video.save()
        # self.documents.save()

    # ------------------------------------------------------------
    # Image modality (delegation)
    # ------------------------------------------------------------

    def rebuild_images(self):
        """
        Rebuild all image indexes from DB.
        """
        for mgr in self.images.values():
            if hasattr(mgr, "rebuild"):
                mgr.rebuild(self.db)

    def add_image(self, file_id, phash_bits, orb_vector, clip_vector):
        """
        Add image vectors to all image modality indexes.
        """
        self.images["phash"].add(file_id, phash_bits)
        self.images["orb"].add(file_id, orb_vector)
        self.images["clip"].add(file_id, clip_vector)

    def search_image_by_phash(self, phash_bits, k=10):
        return self.images["phash"].search(phash_bits, k)

    def search_image_by_orb(self, orb_vector, k=10):
        return self.images["orb"].search(orb_vector, k)

    def search_image_by_clip(self, clip_vector, k=10):
        return self.images["clip"].search(clip_vector, k)
