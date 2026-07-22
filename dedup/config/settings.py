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
• Load definitions from json files in definitions folder

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

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from pathspec import PathSpec

# Load .env from workspace root
load_dotenv(override=True)

# --- Database definitions ---
DB_BACKEND = os.getenv("DEDUP_DB_BACKEND", "sqlite").lower()
if DB_BACKEND == "postgres" and os.getenv("DEDUP_DB_PG_URL", None):
    DB_PG_URL = os.getenv("DEDUP_DB_PG_URL")

# --- SQLite database path ---
DB_SQLITE_PATH = ""
if (
    "DEDUP_DB_SQLite_location" in os.environ
    and os.environ["DEDUP_DB_SQLite_location"].strip()
):
    # check if location exists, if not create it
    db_path = Path(os.environ["DEDUP_DB_SQLite_location"].strip())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DB_SQLITE_PATH = db_path.resolve()
else:
    # use default location in user's home directory
    home_dir = Path.home()
    default_db_path = home_dir / "dedup_data" / "index.db"
    default_db_path.parent.mkdir(parents=True, exist_ok=True)

    DB_SQLITE_PATH = default_db_path.resolve()

# --- Scan roots (collect all DEDUP_SCAN_ROOT_* variables) ---
SCAN_ROOTS = []
for key, value in os.environ.items():
    if key.startswith("DEDUP_SCAN_ROOT_") and value.strip():
        SCAN_ROOTS.append(Path(value.strip()))

# If none defined, fall back to empty list
if not SCAN_ROOTS:
    print("[config] WARNING: No DEDUP_SCAN_ROOT_* variables defined in .env")

# --- Hashing configuration ---
HASH_CHUNK_SIZE = 8 * 1024 * 1024
PARTIAL_HASH_BYTES = 1 * 1024 * 1024

BLAKE_AVAILABLE = False
HASH_ALGO = os.getenv("HASH_ALGO", "sha256")

if HASH_ALGO.lower() == "blake3":
    # Check if blake3 is available
    import importlib.util

    # Check availability once
    _spec = importlib.util.find_spec("blake3")
    if _spec is not None:
        BLAKE_AVAILABLE = True
    else:
        HASH_ALGO = "sha256"


# --- File type definitions ---
IMAGE_EXT = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".tiff",
    ".bmp",
    ".heic",
    ".svg",
    ".raw",
    ".psd",
    ".ai",
    ".indd",
    ".eps",
}
AUDIO_EXT = {
    ".mp3",
    ".flac",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".wma",
    ".alac",
    ".aiff",
    ".opus",
    ".amr",
    ".mid",
    ".midi",
}
VIDEO_EXT = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".wmv",
    ".webm",
    ".flv",
    ".m4v",
    ".3gp",
    ".mpeg",
    ".mpg",
    ".ts",
}
DOC_EXT = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".rtf",
    ".pages",
    ".numbers",
    ".key",
    ".csv",
    ".odt",
    ".ods",
    ".odp",
    ".epub",
    ".md",
    ".tex",
}

# definition locations
BASE_DIR = Path(__file__).resolve().parent
DEFINITIONS_DIR = BASE_DIR / "definitions"

IMAGE_EXTENSIONS_FILE = DEFINITIONS_DIR / "image_extensions.json"
AUDIO_EXTENSIONS_FILE = DEFINITIONS_DIR / "audio_extensions.json"
VIDEO_EXTENSIONS_FILE = DEFINITIONS_DIR / "video_extensions.json"
DOC_EXTENSIONS_FILE = DEFINITIONS_DIR / "document_extensions.json"
EXCLUDE_PATTERNS_FILE = DEFINITIONS_DIR / "exclude_patterns.txt"

# --- image
if IMAGE_EXTENSIONS_FILE.exists():
    with open(IMAGE_EXTENSIONS_FILE, "r") as f:
        IMAGE_DEFINITIONS = json.load(f)
        IMAGE_EXT.update(set(IMAGE_DEFINITIONS.keys()))
else:
    print(
        f"[config] WARNING: {IMAGE_EXTENSIONS_FILE} not found. Using default image extensions."
    )

# --- audio
if AUDIO_EXTENSIONS_FILE.exists():
    with open(AUDIO_EXTENSIONS_FILE, "r") as f:
        AUDIO_DEFINITIONS = json.load(f)
        AUDIO_EXT.update(set(AUDIO_DEFINITIONS.keys()))
else:
    print(
        f"[config] WARNING: {AUDIO_EXTENSIONS_FILE} not found. Using default audio extensions."
    )

# --- video
if VIDEO_EXTENSIONS_FILE.exists():
    with open(VIDEO_EXTENSIONS_FILE, "r") as f:
        VIDEO_DEFINITIONS = json.load(f)
        VIDEO_EXT.update(set(VIDEO_DEFINITIONS.keys()))
else:
    print(
        f"[config] WARNING: {VIDEO_EXTENSIONS_FILE} not found. Using default video extensions."
    )

# --- documents
if DOC_EXTENSIONS_FILE.exists():
    with open(DOC_EXTENSIONS_FILE, "r") as f:
        DOC_DEFINITIONS = json.load(f)
        DOC_EXT.update(set(DOC_DEFINITIONS.keys()))
else:
    print(
        f"[config] WARNING: {DOC_EXTENSIONS_FILE} not found. Using default document extensions."
    )

# --- exclude patterns
EXCLUDE_PATTERNS = [
    "# VSCode",
    ".vscode/",
    "# Python",
    "__pycache__/",
    ".py[codz]",
    "# SQLite",
    "index.db-journal",
    "# --- OneDrive sync placeholders ---",
    "# These appear as invisible GUID files and cannot be opened",
    ".*[0-9A-Fa-f-]{36}",
    "# --- Hidden/system files ---",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "# --- Git metadata ---",
    ".git/",
    ".gitignore",
    "# --- Windows metadata ---",
    "ehthumbs.db",
    "# executables and libraries",
    ".exe",
    ".dll ",
    ".lib ",
]
if EXCLUDE_PATTERNS_FILE.exists():
    with open(EXCLUDE_PATTERNS_FILE, "r") as f:
        EXCLUDE_PATTERNS = [line.strip() for line in f if line.strip()]
else:
    print(
        f"[config] WARNING: {EXCLUDE_PATTERNS_FILE} not found. Using default exclude patterns."
    )

EXCLUDE_SPEC = PathSpec.from_lines("gitwildmatch", EXCLUDE_PATTERNS)


# --- Similirity search (FAISS) ---
PHASH_BINARY_DIM = os.getenv("PHASH_BINARY_DIM", 64)
ORB_BINARY_DIM = os.getenv("ORB_BINARY_DIM", 32)
CLIP_BINARY_DIM = os.getenv("CLIP_BINARY_DIM", 512)

# AUDIO_BINARY_DIM = os.getenv("AUDIO_BINARY_DIM", 128)
# AUDIO_FLOAT_DIM = os.getenv("AUDIO_FLOAT_DIM", 256)

# VIDEO_BINARY_DIM = os.getenv("VIDEO_BINARY_DIM", 64)
# VIDEO_FLOAT_DIM = os.getenv("VIDEO_FLOAT_DIM", 512)

# DOCUMENT_FLOAT_DIM = os.getenv("DOCUMENT_FLOAT_DIM", 768)

# --- Similarity indexes (FAISS) ---
FAISS_PHASH_INDEX = os.getenv("FAISS_PHASH_INDEX", "./data/faiss/phash.index")
FAISS_ORB_INDEX = os.getenv("FAISS_ORB_INDEX", "./data/faiss/orb.index")
FAISS_CLIP_INDEX = os.getenv("FAISS_CLIP_INDEX", "./data/faiss/clip.index")

# FAISS_AUDIO_INDEX = os.getenv(
#     "FAISS_AUDIO_INDEX", "./data/faiss/audio_binary.index"
# )

# FAISS_VIDEO_INDEX = os.getenv(
#     "FAISS_VIDEO_INDEX", "./data/faiss/video_binary.index"
# )

# FAISS_DOCUMENT_INDEX = os.getenv(
#     "FAISS_DOCUMENT_INDEX", "./data/faiss/document_binary.index"
# )
