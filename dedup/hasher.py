"""
dedup.hasher
============

File hashing utilities for the deduplication pipeline (Slice 1).

This module computes both full and partial hashes for files registered
in the database. The hashing algorithm is selected at runtime via the
environment variable HASH_ALGO, allowing seamless switching between:

    • SHA‑256  — stable, widely supported
    • BLAKE3   — extremely fast, parallel‑friendly, ideal for large datasets

Full hashes are used for exact duplicate detection. Partial hashes are
computed from the first and last N bytes of each file and may be used
in future slices for pre‑filtering, clustering, or similarity heuristics.

Design goals:
-------------
• Stream files in chunks to avoid memory spikes
• Support multi‑gigabyte files efficiently
• Keep the API simple (`hash_file(path) -> (full, partial)`)
• Allow future GPU acceleration without changing callers
• Integrate cleanly with the worker and database layers

Partial hashing:
----------------
Partial hashes combine the first and last N bytes of a file. This is
useful for quickly eliminating non‑duplicates before performing more
expensive comparisons. The number of bytes is configured via
PARTIAL_HASH_BYTES in dedup.config.

Environment‑driven configuration:
---------------------------------
The following values are loaded from dedup.config:

    HASH_ALGO          — "sha256" or "blake3"
    HASH_CHUNK_SIZE    — streaming chunk size
    PARTIAL_HASH_BYTES — size of prefix/suffix used for partial hash

This makes the hashing layer portable across Windows profiles, shared
folders, and OneDrive hydration workflows.

Related modules:
----------------
• [config](ca://s?q=Explain_dedup_config_module)
• [scanner](ca://s?q=Explain_dedup_scanner_module)
• [worker](ca://s?q=Explain_dedup_worker_module)
• [db](ca://s?q=Explain_dedup_db_module)
• [cli](ca://s?q=Explain_dedup_CLI_design)

Future slices will extend this module with GPU‑accelerated hashing,
batch hashing, and content‑aware hashing for images, audio, and video.
"""

import hashlib
from pathlib import Path
from .config import HASH_ALGO, HASH_CHUNK_SIZE, PARTIAL_HASH_BYTES

# Optional import for BLAKE3
try:
    from blake3 import blake3

    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False


def _get_hasher():
    algo = HASH_ALGO.lower()

    if algo == "sha256":
        return hashlib.sha256()

    if algo == "blake3":
        if not HAS_BLAKE3:
            raise RuntimeError(
                "HASH_ALGO=blake3 but the blake3 package is not installed"
            )
        return blake3()

    raise ValueError(f"Unsupported HASH_ALGO={HASH_ALGO}")


def hash_file(path: str) -> tuple[str, str | None]:
    p = Path(path)
    h_full = _get_hasher()
    size = p.stat().st_size

    first_bytes = b""
    last_bytes = b""

    # --- Read file and compute full hash ---
    with p.open("rb") as f:
        # First N bytes
        remaining_for_first = PARTIAL_HASH_BYTES
        while remaining_for_first > 0:
            chunk = f.read(min(HASH_CHUNK_SIZE, remaining_for_first))
            if not chunk:
                break
            first_bytes += chunk
            remaining_for_first -= len(chunk)
            h_full.update(chunk)

        # Middle of file
        while True:
            chunk = f.read(HASH_CHUNK_SIZE)
            if not chunk:
                break
            h_full.update(chunk)

    # --- Last N bytes for partial hash ---
    if size > PARTIAL_HASH_BYTES:
        with p.open("rb") as f:
            f.seek(max(0, size - PARTIAL_HASH_BYTES))
            last_bytes = f.read(PARTIAL_HASH_BYTES)

    # --- Compute partial hash ---
    h_partial = None
    if first_bytes or last_bytes:
        h_p = _get_hasher()
        h_p.update(first_bytes)
        h_p.update(last_bytes)
        h_partial = h_p.hexdigest()

    return h_full.hexdigest(), h_partial
