"""
dedup.config
============

Centralized configuration loader for the deduplication pipeline (Slice 1).

This module reads all runtime configuration from environment variables,
typically provided via a `.env` file loaded by VS Code. This allows the
project to run cleanly across multiple Windows profiles, Miniforge
environments, and shared-folder setups without hard‑coded paths.

Responsibilities:
----------------
• Load `.env` using python‑dotenv
• Resolve the SQLite database path (DEDUP_DB)
• Collect all scan roots defined as DEDUP_SCAN_ROOT_*
• Provide hashing configuration (algorithm, chunk sizes)
• Expose values to other modules (scanner, hasher, worker, CLI)

Why environment‑driven config:
------------------------------
Windows user profiles, OneDrive folders, and shared NTFS junctions often
live on different paths. Hard‑coding these paths would make the pipeline
fragile. By using environment variables, the project remains portable and
safe across:

    • Multiple Windows accounts
    • OneDrive “keep local” hydration workflows
    • Shared folders with NTFS junctions
    • Miniforge/conda environments
    • Future GPU‑accelerated slices

Typical `.env` entries:
-----------------------
    DEDUP_DB=C:\\path\\to\\data\\index.db
    DEDUP_SCAN_ROOT_1=C:\\SharedData\\User1_OneDrive
    DEDUP_SCAN_ROOT_2=C:\\SharedData\\User2_OneDrive
    HASH_ALGO=blake3

These values are consumed by the scanner, hasher, and CLI commands.

Related modules:
----------------
• [scanner](ca://s?q=Explain_dedup_scanner_module)
• [hasher](ca://s?q=Explain_dedup_hasher_module)
• [hydrate](ca://s?q=Explain_dedup_hydrate_module)
• [cli](ca://s?q=Explain_dedup_CLI_design)

This module forms the foundation for all future slices, including
parallel hashing, GPU hashing, metadata extraction, and similarity search.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from workspace root
load_dotenv()

# --- Database path ---
DB_PATH = Path(os.getenv("DEDUP_DB", "data/index.db"))

# --- Scan roots (collect all DEDUP_SCAN_ROOT_* variables) ---
SCAN_ROOTS = []
for key, value in os.environ.items():
    if key.startswith("DEDUP_SCAN_ROOT_") and value.strip():
        SCAN_ROOTS.append(Path(value.strip()))

# If none defined, fall back to empty list
if not SCAN_ROOTS:
    print("[config] WARNING: No DEDUP_SCAN_ROOT_* variables defined in .env")

# --- Hashing configuration ---
HASH_ALGO = os.getenv("HASH_ALGO", "sha256")
HASH_CHUNK_SIZE = 8 * 1024 * 1024
PARTIAL_HASH_BYTES = 1 * 1024 * 1024
