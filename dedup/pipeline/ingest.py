# dedup/pipeline/ingest.py

from dedup.config.settings import (
    DB_BACKEND,
    DB_PG_URL,
    DB_SQLITE_PATH,
    SCAN_ROOTS,
)
from dedup.core.scanner import Scanner
from dedup.core.hasher import Hasher
from dedup.db.loader import SQLLoader
from dedup.db.postgres import PostgresDB
from dedup.db.sqlite import SQLiteDB


def get_db():
    loader = SQLLoader(DB_BACKEND)

    if DB_BACKEND == "postgres":
        return PostgresDB(loader, DB_PG_URL)
    else:
        return SQLiteDB(loader, str(DB_SQLITE_PATH))


def run_ingestion():
    """
    Scan all configured roots, hash files, and insert into DB.
    """
    if not SCAN_ROOTS:
        print("[ingest] No scan roots defined. Check DEDUP_SCAN_ROOT_* in .env")
        return

    db = get_db()
    scanner = Scanner(SCAN_ROOTS)
    hasher = Hasher()

    # Ensure tables exist
    db.execute("create_tables")

    count = 0

    for info in scanner.scan():
        hashes = hasher.hash_file(info.path)

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

        count += 1
        if count % 1000 == 0:
            print(f"[ingest] Processed {count} files...")

    print(f"[ingest] Completed. Total files processed: {count}")
