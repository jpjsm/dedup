# dedup/similarity/multimodal_similarity_engine.py

from similarity.image_index_manager import ImageIndexManager


class MultimodalSimilarityEngine:
    """
    Orchestrates all modality-specific FAISS managers.
    Keeps FAISS logic out of the engine.
    """

    def __init__(self, db_adapter, config):
        self.db = db_adapter
        self.cfg = config

        # Modality managers
        self.images = ImageIndexManager()
        # self.audio = AudioIndexManager()
        # self.video = VideoIndexManager()
        # self.documents = DocumentIndexManager()

    # ------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------

    def load(self):
        self.images.load()
        # self.audio.load()
        # self.video.load()
        # self.documents.load()

    def save(self):
        self.images.save()
        # self.audio.save()
        # self.video.save()
        # self.documents.save()

    # ------------------------------------------------------------
    # Image modality (delegation)
    # ------------------------------------------------------------

    def rebuild_images(self):
        self.images.rebuild(self.db)

    def add_image(self, file_id, phash_bits, embedding):
        self.images.add(self.db, file_id, phash_bits, embedding)

    def search_image_by_phash(self, file_id, k=10):
        return self.images.search_by_phash(self.db, file_id, k)

    def search_image_by_embedding(self, file_id, k=10):
        return self.images.search_by_embedding(self.db, file_id, k)
