"""
dedup.db
========

Database layer for the deduplication pipeline (Slice 1).

This module encapsulates all interaction with the SQLite database used
to track files, hashing status, and duplicate detection. It provides:

    • A safe connection helper (`get_conn`)
    • Schema creation (`init_db`)
    • Convenience utilities for queries used by the scanner and hasher

Why SQLite:
-----------
SQLite is ideal for Slice 1 because it is:

    • Zero‑configuration
    • Fast for local workloads
    • Durable and ACID‑compliant
    • Easy to inspect manually
    • Perfect for millions of rows on a single machine

The schema is intentionally simple: one table (`files`) with indexes on
file size and full hash. This supports efficient duplicate detection and
incremental hashing.

Environment‑driven configuration:
---------------------------------
The database path is loaded from `.env` via dedup.config:

    DEDUP_DB=C:\\path\\to\\data\\index.db

This allows the project to run cleanly across Windows profiles, shared
folders, and OneDrive junction setups without hard‑coded paths.

Related modules:
----------------
• [config](ca://s?q=Explain_dedup_config_module)
• [scanner](ca://s?q=Explain_dedup_scanner_module)
• [hasher](ca://s?q=Explain_dedup_hasher_module)
• [cli](ca://s?q=Explain_dedup_CLI_design)

Future slices (parallel hashing, GPU hashing, metadata extraction, and
similarity search) will extend this module with additional tables and
indexes while preserving backward compatibility.
"""

import sqlite3
import time
from pathlib import Path
from .config import DB_PATH


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS files (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        path         TEXT NOT NULL UNIQUE,
        size_bytes   INTEGER NOT NULL,
        mtime        REAL NOT NULL,
        ctime        REAL NOT NULL,
        file_type    TEXT,
        status       TEXT NOT NULL,
        error_msg    TEXT,
        hash_full    TEXT,
        hash_partial TEXT,
        created_at   REAL NOT NULL,
        updated_at   REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_files_hash_full
        ON files(hash_full);
    CREATE INDEX IF NOT EXISTS idx_files_size
        ON files(size_bytes);
    """
    with get_conn() as conn:
        conn.executescript(schema)


def upsert_file(path: str, size: int, mtime: float, ctime: float, file_type: str):
    now = time.time()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO files (path, size_bytes, mtime, ctime, file_type,
                               status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'new', ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size_bytes = excluded.size_bytes,
                mtime      = excluded.mtime,
                ctime      = excluded.ctime,
                file_type  = excluded.file_type,
                updated_at = excluded.updated_at
            """,
            (path, size, mtime, ctime, file_type, now, now),
        )


def fetch_unhashed(batch_size: int = 1000):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT * FROM files WHERE status = 'new' LIMIT ?",
            (batch_size,),
        )
        return list(cur)


def update_hash_result(
    file_id: int, hash_full: str, hash_partial: str | None, error: str | None
):
    status = "hashed" if error is None else "error"
    now = time.time()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE files
               SET hash_full = ?,
                   hash_partial = ?,
                   status = ?,
                   error_msg = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (hash_full, hash_partial, status, error, now, file_id),
        )
