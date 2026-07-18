import queue
import threading
from concurrent.futures import ThreadPoolExecutor

from dedup.config.settings import SCAN_ROOTS, DB_BACKEND, DB_PG_URL, DB_SQLITE_PATH
from dedup.core.scanner import Scanner
from dedup.core.hasher import Hasher
from dedup.db.loader import SQLLoader
from dedup.db.postgres import PostgresDB
from dedup.db.sqlite import SQLiteDB


def get_db():
    loader = SQLLoader(DB_BACKEND)
    if DB_BACKEND == "postgres":
        return PostgresDB(loader, DB_PG_URL)
    return SQLiteDB(loader, str(DB_SQLITE_PATH))


def insert_record(db, info, hashes):
    db.execute(
        "insert_file",
        info.path,
        info.filename,
        info.filename_no_ext,
        info.extension,
        info.parent_folder,
        info.object_type,
        hashes.full_hash,
        info.size,
        info.created_at,
        info.modified_at,
        info.scanned_at,
    )


def run_parallel_ingestion(max_workers: int = 8):
    """
    Parallel scan + hash + DB ingest using bounded queues.
    """

    if not SCAN_ROOTS:
        print(
            "[parallel_ingest] No scan roots defined. Check DEDUP_SCAN_ROOT_* in .env"
        )
        return

    db = get_db()
    db.execute("create_tables")

    scan_queue: queue.Queue = queue.Queue(maxsize=1000)
    db_queue: queue.Queue = queue.Queue(maxsize=1000)

    scanner = Scanner(SCAN_ROOTS)
    hasher = Hasher()

    # --- Scanner thread ---
    def scan_worker():
        for info in scanner.scan():
            scan_queue.put(info)
        scan_queue.put(None)  # poison pill

    # --- Hash workers (run in ThreadPoolExecutor) ---
    def hash_worker(info):
        hashes = hasher.hash_file(info.path)
        db_queue.put((info, hashes))

    # --- DB writer thread ---
    def db_worker():
        processed = 0
        while True:
            item = db_queue.get()
            if item is None:
                break
            info, hashes = item
            insert_record(db, info, hashes)
            processed += 1
            if processed % 1000 == 0:
                print(f"[parallel_ingest] DB: {processed} files ingested...")

        print(f"[parallel_ingest] Completed. Total files ingested: {processed}")

    # start scanner and DB writer
    threading.Thread(target=scan_worker, daemon=True).start()
    threading.Thread(target=db_worker, daemon=True).start()

    # hash worker pool
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while True:
            info = scan_queue.get()
            if info is None:
                break
            executor.submit(hash_worker, info)

    # signal DB writer to stop
    db_queue.put(None)
