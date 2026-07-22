# dedup/db/postgres.py
import psycopg2
from psycopg2.extras import DictCursor

from .base import DedupDB


class PostgresDB(DedupDB):
    def __init__(self, loader, url):
        super().__init__(loader)
        self.conn = psycopg2.connect(url)

    def execute(self, query_name, *params):
        sql = self.loader.load(query_name)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)

            # If SQL returns rows (SELECT or RETURNING)
            if cur.description is not None:
                rows = cur.fetchall()

                # If it's a RETURNING id, return the scalar
                if len(rows) == 1 and len(rows[0]) == 1:
                    self.conn.commit()
                    return rows[0][0]

                # Otherwise return all rows
                self.conn.commit()
                return rows

        # No rows returned → commit and return None
        self.conn.commit()
        return None

    def query(self, query_name, *params):
        sql = self.loader.load(query_name)

        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
