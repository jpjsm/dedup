"""
dedup.scanner
=============

Directory scanner for the deduplication pipeline (Slice 1).

This module walks all configured scan roots (defined in `.env` as
DEDUP_SCAN_ROOT_*) and registers every file into the SQLite database.
Each file is recorded with metadata such as:

    • Absolute path
    • File size
    • Modification and creation timestamps
    • File type (image, audio, video, document, other)
    • Initial status ("new")

The scanner does *not* compute hashes. It only discovers files and
populates the database so that the hashing worker can process them
incrementally.

Why a scanner:
--------------
Separating scanning from hashing allows the pipeline to:

    • Resume work after interruption
    • Track millions of files efficiently
    • Avoid re-hashing unchanged files
    • Support multi-root setups (OneDrive, shared folders, junctions)
    • Integrate hydration workflows before hashing

Environment-driven configuration:
--------------------------------
Scan roots are loaded from dedup.config, which reads `.env` entries:

    DEDUP_SCAN_ROOT_1=C:\\SharedData\\User1_OneDrive
    DEDUP_SCAN_ROOT_2=C:\\SharedData\\User2_OneDrive

This makes the scanner portable across Windows profiles, OneDrive
junctions, and multi-disk setups without hard-coded paths.

File type detection:
--------------------
Basic file type inference is performed using file extensions. Future
slices may replace this with MIME detection or content-based heuristics.

Related modules:
----------------
• [config](ca://s?q=Explain_dedup_config_module)
• [db](ca://s?q=Explain_dedup_db_module)
• [hasher](ca://s?q=Explain_dedup_hasher_module)
• [hydrate](ca://s?q=Explain_dedup_hydrate_module)
• [worker](ca://s?q=Explain_dedup_worker_module)
• [cli](ca://s?q=Explain_dedup_CLI_design)

This module forms the foundation for future slices such as parallel
scanning, file change detection, and metadata extraction.
"""

import os
import stat

from collections import defaultdict
from pathlib import Path

from .config import SCAN_ROOTS
from .db import upsert_file, get_conn

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".bmp", ".heic"}
AUDIO_EXT = {".mp3", ".flac", ".wav", ".m4a", ".aac", ".ogg"}
VIDEO_EXT = {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm"}
DOC_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf"}


def classify_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in VIDEO_EXT:
        return "video"
    if ext in DOC_EXT:
        return "doc"
    return "other"


def summarize_scan(scan_roots, db_conn):
    """
    Produce a per-root summary of file categories after scanning.
    """
    summary = {root: defaultdict(int) for root in scan_roots}

    cur = db_conn.execute("SELECT path, file_type FROM files")
    for row in cur:
        path = Path(row["path"])
        filetype = row["file_type"] or "other"

        # Find which scan root this file belongs to
        for root in scan_roots:
            if path.is_relative_to(root):
                summary[root][filetype] += 1
                summary[root]["total"] += 1
                break

    print("\nScan Summary\n============\n")
    for root in scan_roots:
        print(root)
        counts = summary[root]
        print(f"  Documents:   {counts.get('document', 0):>12,}")
        print(f"  Pictures:    {counts.get('image', 0):>12,}")
        print(f"  Videos:      {counts.get('video', 0):>12,}")
        print(f"  Audio:       {counts.get('audio', 0):>12,}")
        print(f"  Other:       {counts.get('other', 0):>12,}")
        print(f"  Total:       {counts.get('total', 0):>12,}\n")


def scan():
    for root in SCAN_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            for name in filenames:
                p = Path(dirpath) / name
                try:
                    st = p.stat()
                    if not stat.S_ISREG(st.st_mode):
                        continue
                    file_type = classify_type(p)
                    upsert_file(
                        path=str(p).strip(),
                        size=st.st_size,
                        mtime=st.st_mtime,
                        ctime=st.st_ctime,
                        file_type=file_type,
                    )
                except Exception as e:
                    # For Slice 1, we can log to stderr or a simple log file
                    print(f"[scan] error on {p}: {e}")

    with get_conn() as conn:
        summarize_scan(SCAN_ROOTS, conn)
