"""
dedup.cli
=========

Command‑line interface for Slice 1 of the deduplication pipeline.

This module provides operational commands for:

    • Initializing the SQLite database
    • Scanning configured directories for files
    • Hashing files (SHA‑256 or BLAKE3, depending on config)
    • Reporting exact duplicates
    • Hydrating OneDrive‑backed folders so files exist locally

Environment‑driven configuration:
--------------------------------
All paths and scan roots are loaded from `.env` via dedup.config.
This allows the project to run cleanly across Windows profiles,
multiple disks, and shared folder setups without hard‑coded paths.

Hydration:
----------
Windows OneDrive may store files as cloud‑only placeholders.
Cloud‑only files cannot be hashed or hardlinked. The `hydrate`
command walks all scan roots and forces local availability by
reading a small portion of each offline file. This triggers
OneDrive to download the file on demand.

Usage:
------
    python -m dedup.cli init-db
    python -m dedup.cli hydrate
    python -m dedup.cli scan
    python -m dedup.cli hash --batch 500
    python -m dedup.cli report-dups

This CLI is intentionally simple and forms the foundation for
future slices (parallel hashing, GPU hashing, metadata extraction,
image/audio/video similarity, etc.).
"""

import argparse
from .db import init_db
from .scanner import scan
from .worker import process_batch


def cmd_init_db(args):
    """Initialize the SQLite database and create required tables."""
    init_db()
    print("DB initialized.")


def cmd_scan(args):
    """Scan all configured roots and register files in the database."""
    scan()
    print("Scan complete.")


def cmd_hash(args):
    """
    Hash all unprocessed files in batches.

    Uses the hashing algorithm defined in the environment (HASH_ALGO),
    typically SHA‑256 or BLAKE3. Updates the database with full and
    partial hashes.
    """
    total = 0
    while True:
        n = process_batch(batch_size=args.batch)
        if n == 0:
            break
        total += n
        print(f"Hashed {total} files...", end="\r")
    print(f"\nHashing complete. Total: {total}")


def cmd_report_dups(args):
    """Report exact duplicates based on full hash matches."""
    from .db import get_conn

    with get_conn() as conn:
        cur = conn.execute("""
            SELECT hash_full, COUNT(*) as cnt
              FROM files
             WHERE status = 'hashed' AND hash_full IS NOT NULL
             GROUP BY hash_full
            HAVING cnt > 1
            ORDER BY cnt DESC
            """)
        for row in cur:
            print(f"{row['hash_full']} -> {row['cnt']} files")


def cmd_hydrate(args):
    """
    Ensure all files in scan roots are fully hydrated (local).

    OneDrive may store files as cloud‑only placeholders. Hydration
    forces local availability by reading a small portion of each
    offline file. This is required before hashing or creating
    hardlinks/junctions.
    """
    from .config import SCAN_ROOTS
    from .hydrate import hydrate_tree

    if not SCAN_ROOTS:
        print("No scan roots defined in .env (DEDUP_SCAN_ROOT_*).")
        return

    print("Starting hydration...")
    for root in SCAN_ROOTS:
        hydrate_tree(root)
    print("Hydration complete.")


def main():
    """Entry point for the dedup CLI."""
    parser = argparse.ArgumentParser(prog="dedup")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # init-db
    p_init = sub.add_parser("init-db", help="Initialize the database.")
    p_init.set_defaults(func=cmd_init_db)

    # hydrate
    p_hydrate = sub.add_parser("hydrate", help="Hydrate OneDrive-backed files.")
    p_hydrate.set_defaults(func=cmd_hydrate)

    # scan
    p_scan = sub.add_parser("scan", help="Scan directories and register files.")
    p_scan.set_defaults(func=cmd_scan)

    # hash
    p_hash = sub.add_parser("hash", help="Hash unprocessed files.")
    p_hash.add_argument("--batch", type=int, default=200)
    p_hash.set_defaults(func=cmd_hash)

    # report-dups
    p_dups = sub.add_parser("report-dups", help="Report exact duplicate files.")
    p_dups.set_defaults(func=cmd_report_dups)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
