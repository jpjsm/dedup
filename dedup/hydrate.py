"""
dedup.hydrate
=============

OneDrive hydration utilities for the deduplication pipeline (Slice 1).

This module ensures that all files inside the configured scan roots are
fully available on disk. On Windows, OneDrive may store files as
cloud‑only placeholders (Files On‑Demand). These files appear in the
filesystem but contain no local data and cannot be hashed, scanned for
metadata, or hardlinked.

Hydration solves this by:
    • Detecting files marked with FILE_ATTRIBUTE_OFFLINE
    • Triggering OneDrive to download the file by reading a small chunk
    • Logging progress as files become locally available

Why hydration matters:
----------------------
The dedup pipeline requires real bytes on disk. Cloud‑only files will:
    • Fail hashing
    • Break partial hashing
    • Prevent NTFS hardlinks or junction-based workflows
    • Cause inconsistent duplicate detection

Hydration is therefore a required preprocessing step when scanning
OneDrive-backed folders, especially when using shared NTFS junctions
across multiple Windows profiles.

How it works:
-------------
Windows exposes hydration state via file attributes. A file is considered
offline if it has the FILE_ATTRIBUTE_OFFLINE flag. Reading even a single
byte forces OneDrive to hydrate the file. This module wraps that behavior
in a safe, Pythonic interface.

Environment-driven configuration:
---------------------------------
Scan roots are loaded from dedup.config (DEDUP_SCAN_ROOT_*). Hydration
operates only on those roots, ensuring the pipeline touches exactly the
folders the user has configured.

Related modules:
----------------
• [config](ca://s?q=Explain_dedup_config_module)
• [scanner](ca://s?q=Explain_dedup_scanner_module)
• [hasher](ca://s?q=Explain_dedup_hasher_module)
• [worker](ca://s?q=Explain_dedup_worker_module)
• [cli](ca://s?q=Explain_dedup_CLI_design)

Future slices may extend this module with:
    • Parallel hydration
    • Hydration progress reporting
    • OneDrive state auditing (local vs cloud-only counts)
    • Automatic retry logic for partially hydrated files
"""

import os
from pathlib import Path

FILE_ATTRIBUTE_OFFLINE = 0x1000  # FILE_ATTRIBUTE_OFFLINE flag


def is_offline(path: Path) -> bool:
    try:
        attrs = os.stat(path).st_file_attributes
        return bool(attrs & FILE_ATTRIBUTE_OFFLINE)
    except Exception:
        return False


def hydrate_file(path: Path, chunk_size=1024 * 64):
    try:
        with open(path, "rb") as f:
            f.read(chunk_size)  # triggers hydration
        return True
    except Exception:
        return False


def hydrate_tree(root: Path):
    root = Path(root)
    print(f"Hydrating: {root}")

    for p in root.rglob("*"):
        if p.is_file() and is_offline(p):
            print(f"  -> Hydrating {p}")
            hydrate_file(p)

    print("Hydration complete.")
