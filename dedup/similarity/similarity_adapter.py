# similarity/similarity_adapter.py

from abc import ABC, abstractmethod
from typing import Any


class SimilarityAdapter(ABC):

    @abstractmethod
    def get_all_image_vectors(self) -> list[Any]: ...

    @abstractmethod
    def update_image_faiss_index(self, file_id, bin_idx, float_idx): ...

    @abstractmethod
    def get_phash(self, file_id) -> tuple[Any, ...] | None: ...

    @abstractmethod
    def get_image_embedding(self, file_id) -> tuple[Any, ...] | None: ...

    @abstractmethod
    def lookup_files_by_image_index(
        self, faiss_indices, distances
    ) -> list[dict[str, Any]]: ...
