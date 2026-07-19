# similarity/sqlite_similarity_adapter.py

import sqlite3
from similarity.similarity_adapter import SimilarityAdapter


class SQLiteSimilarityAdapter(SimilarityAdapter):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ------------------------------------------------------------
    # Image modality methods (required by SimilarityAdapter)
    # ------------------------------------------------------------

    def get_all_image_vectors(self):
        """
        Returns rows: (id, phash BLOB, clip_embedding BLOB)
        Only for object_type='image'
        """
        return self.conn.execute("""
            SELECT id, phash, clip_embedding
            FROM files
            WHERE object_type = 'image'
            ORDER BY id
            """).fetchall()

    def update_image_faiss_index(self, file_id, bin_idx, float_idx):
        """
        Stores FAISS index positions for image modality.
        """
        self.conn.execute(
            """
            UPDATE files
            SET faiss_index = ?, faiss_index_float = ?
            WHERE id = ?
            """,
            (bin_idx, float_idx, file_id),
        )
        self.conn.commit()

    def get_phash(self, file_id) -> tuple[bytes, ...] | None:
        """
        Returns the pHash BLOB for an image.
        """
        row = self.conn.execute(
            "SELECT phash FROM files WHERE id = ?", (file_id,)
        ).fetchone()
        return row[0]

    def get_image_embedding(self, file_id):
        """
        Returns the CLIP embedding BLOB for an image.
        """
        row = self.conn.execute(
            "SELECT clip_embedding FROM files WHERE id = ?", (file_id,)
        ).fetchone()
        return row[0]

    def lookup_files_by_image_index(self, faiss_indices, distances):
        """
        Maps FAISS index → file metadata.
        """
        placeholders = ",".join("?" for _ in faiss_indices)

        rows = self.conn.execute(
            f"""
            SELECT id, path, filename, parent_folder
            FROM files
            WHERE faiss_index IN ({placeholders})
            """,
            tuple(faiss_indices),
        ).fetchall()

        return [
            {
                "file_id": row[0],
                "path": row[1],
                "filename": row[2],
                "parent_folder": row[3],
                "distance": float(distances[i]),
            }
            for i, row in enumerate(rows)
        ]
