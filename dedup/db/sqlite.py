# dedup/db/sqlite.py
import sqlite3
from .base import DedupDB


class SQLiteDB(DedupDB):
    def __init__(self, loader, path):
        super().__init__(loader)
        self.conn = sqlite3.connect(path)

    def execute(self, query_name, *params):
        sql = self.loader.load(query_name)
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()

    def query(self, query_name, *params):
        sql = self.loader.load(query_name)
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
