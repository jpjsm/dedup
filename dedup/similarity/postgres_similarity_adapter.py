# similarity/postgres_similarity_adapter.py

import psycopg2
from similarity.similarity_adapter import SimilarityAdapter


class PostgresSimilarityAdapter(SimilarityAdapter):
    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn

    # ------------------------------------------------------------
    # Image modality methods (required by SimilarityAdapter)
    # ------------------------------------------------------------

    def get_all_image_vectors(self):
        """
        Returns rows: (id, phash BYTEA, clip_embedding BYTEA)
        Only for object_type='image'
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, phash, clip_embedding
                FROM files
                WHERE object_type = 'image'
                ORDER BY id
                """)
            return cur.fetchall()

    def update_image_faiss_index(self, file_id, bin_idx, float_idx):
        """
        Stores FAISS index positions for image modality.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE files
                SET faiss_index = %s,
                    faiss_index_float = %s
                WHERE id = %s
                """,
                (bin_idx, float_idx, file_id),
            )
        self.conn.commit()

    def get_phash(self, file_id):
        """
        Returns the pHash BYTEA for an image.
        """
        with self.conn.cursor() as cur:
            cur.execute("SELECT phash FROM files WHERE id = %s", (file_id,))
            return cur.fetchone()[0]

    def get_image_embedding(self, file_id):
        """
        Returns the CLIP embedding BYTEA for an image.
        """
        with self.conn.cursor() as cur:
            cur.execute("SELECT clip_embedding FROM files WHERE id = %s", (file_id,))
            return cur.fetchone()[0]

    def lookup_files_by_image_index(self, faiss_indices, distances):
        """
        Maps FAISS index → file metadata.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, path, filename, parent_folder
                FROM files
                WHERE faiss_index = ANY(%s)
                """,
                (faiss_indices,),
            )
            rows = cur.fetchall()

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
