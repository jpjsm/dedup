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
        self.conn.commit()

    def query(self, query_name, *params):
        sql = self.loader.load(query_name)
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
