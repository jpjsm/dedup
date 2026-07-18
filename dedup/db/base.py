# dedup/db/base.py
class DedupDB:
    def __init__(self, loader):
        self.loader = loader

    def execute(self, query_name: str, *params):
        raise NotImplementedError

    def query(self, query_name: str, *params):
        raise NotImplementedError
