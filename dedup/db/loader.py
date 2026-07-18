# dedup/db/loader.py
import pathlib


class SQLLoader:
    def __init__(self, backend: str):
        self.backend = backend
        self.base_path = pathlib.Path(__file__).parent.parent / "sql" / backend
        self.cache = {}

    def load(self, name: str) -> str:
        if name in self.cache:
            return self.cache[name]

        file_path = self.base_path / f"{name}.sql"
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()

        self.cache[name] = sql
        return sql
