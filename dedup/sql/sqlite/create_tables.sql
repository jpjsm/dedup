------------------------------------------------------------
-- 1. FILES TABLE (SQLite)
-- One row per file on disk
-- No similarity vectors stored here
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- POSIX-normalized absolute path
    path TEXT NOT NULL UNIQUE,

    -- File metadata
    filename TEXT NOT NULL,
    filename_no_ext TEXT NOT NULL,
    extension TEXT NOT NULL,
    parent_folder TEXT NOT NULL,

    -- Classification
    object_type TEXT NOT NULL CHECK (
        object_type IN ('image', 'audio', 'video', 'document', 'other')
    ),

    -- Content hash (SHA256, BLAKE3, etc.)
    hash TEXT NOT NULL,

    -- File size
    size INTEGER NOT NULL,

    -- Timestamps (stored as TEXT or INTEGER; here TEXT ISO8601)
    created_at TEXT DEFAULT (datetime('now')),
    modified_at TEXT,
    scanned_at TEXT DEFAULT (datetime('now')),

    -- FK to similarity table
    FOREIGN KEY (hash) REFERENCES similarity(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files (hash);
CREATE INDEX IF NOT EXISTS idx_files_object_type ON files (object_type);
CREATE INDEX IF NOT EXISTS idx_files_parent_folder ON files (parent_folder);



------------------------------------------------------------
-- 2. SIMILARITY TABLE (SQLite)
-- One row per unique content_hash
-- Stores multimodal vectors
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS similarity (
    content_hash TEXT PRIMARY KEY,      -- SHA256 or BLAKE3

    --------------------------------------------------------
    -- 1. Perceptual Hash (pHash)
    --------------------------------------------------------
    phash BLOB,                         -- 64-bit or 128-bit pHash

    --------------------------------------------------------
    -- 2. ORB Descriptor (binary feature vector)
    --------------------------------------------------------
    orb_descriptor BLOB,                -- flattened ORB descriptor

    --------------------------------------------------------
    -- 3. CLIP Embedding (semantic vector)
    --------------------------------------------------------
    clip_embedding BLOB,                -- float32 array

    --------------------------------------------------------
    -- Timestamps
    --------------------------------------------------------
    created_at TEXT DEFAULT (datetime('now'))
);



------------------------------------------------------------
-- 3. OPTIONAL: FAISS INDEX METADATA TABLE (SQLite)
-- Stores FAISS index positions for each modality
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS similarity_faiss (
    content_hash TEXT PRIMARY KEY,
    phash_index INTEGER,
    orb_index INTEGER,
    clip_index INTEGER,

    FOREIGN KEY (content_hash) REFERENCES similarity(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_similarity_faiss_phash ON similarity_faiss (phash_index);
CREATE INDEX IF NOT EXISTS idx_similarity_faiss_orb ON similarity_faiss (orb_index);
CREATE INDEX IF NOT EXISTS idx_similarity_faiss_clip ON similarity_faiss (clip_index);
