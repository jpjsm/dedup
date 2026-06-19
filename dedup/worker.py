"""
dedup.worker
============

Batch hashing worker for the deduplication pipeline (Slice 1).

This module pulls "new" files from the database, computes their full and
partial hashes, and updates their status. It operates in batches to
support long‑running workflows, incremental progress, and future
parallelization.

Responsibilities:
----------------
• Select a batch of unprocessed files from the database
• Compute full and partial hashes via dedup.hasher
• Update file records with:
      – hash_full
      – hash_partial
      – status ("hashed" or "error")
      – timestamps
• Return the number of processed files so the CLI can loop until done

Why a worker:
-------------
Separating hashing from scanning and hydration provides several benefits:

    • The pipeline can resume after interruption
    • Hashing can run in controlled batch sizes
    • Future slices can introduce:
          – multiprocessing
          – thread pools
          – GPU batch hashing
          – distributed hashing
    • The database always reflects consistent progress

Batching:
---------
The worker processes files in batches (default: 200). This prevents long
transactions, reduces memory pressure, and allows the CLI to provide
progress feedback.

Error handling:
---------------
If hashing fails (permissions, unreadable file, partial hydration, etc.),
the worker records the error message and marks the file as "error" so the
pipeline can continue without stalling.

Environment-driven configuration:
---------------------------------
Hashing behavior (algorithm, chunk sizes, partial hash size) is defined
in dedup.config and loaded by dedup.hasher. This keeps the worker simple
and focused on orchestration.

Related modules:
----------------
• [scanner](ca://s?q=Explain_dedup_scanner_module)
• [hasher](ca://s?q=Explain_dedup_hasher_module)
• [db](ca://s?q=Explain_dedup_db_module)
• [hydrate](ca://s?q=Explain_dedup_hydrate_module)
• [cli](ca://s?q=Explain_dedup_CLI_design)

This module forms the execution engine for Slice 1 and will evolve in
future slices to support parallel CPU hashing, GPU acceleration, and
content-aware hashing for images, audio, and video.
"""

from .db import fetch_unhashed, update_hash_result
from .hasher import hash_file


def process_batch(batch_size: int = 100):
    rows = fetch_unhashed(batch_size=batch_size)
    if not rows:
        return 0

    for row in rows:
        file_id = row["id"]
        path = row["path"]
        try:
            h_full, h_partial = hash_file(path)
            update_hash_result(file_id, h_full, h_partial, error=None)
        except Exception as e:
            update_hash_result(file_id, hash_full=None, hash_partial=None, error=str(e))
    return len(rows)
