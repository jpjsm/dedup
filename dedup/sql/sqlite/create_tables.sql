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

    -- Hashing
    hash TEXT NOT NULL,
    size INTEGER NOT NULL,

    ------------------------------------------------------------
    -- 1. Perceptual Hash (pHash)
    ------------------------------------------------------------
    phash BLOB,                 -- 8 bytes (64 bits packed)
    phash_faiss_index INTEGER, -- FAISS binary index position

    ------------------------------------------------------------
    -- 2. ORB Descriptor (binary feature vector)
    ------------------------------------------------------------
    orb_descriptor BLOB,        -- 32 bytes (mean ORB descriptor)
    orb_faiss_index INTEGER,    -- FAISS binary index position

    ------------------------------------------------------------
    -- 3. CLIP Embedding (semantic vector)
    ------------------------------------------------------------
    clip_embedding BLOB,        -- 512 floats (2048 bytes)
    clip_faiss_index INTEGER,   -- FAISS float index position

    ------------------------------------------------------------
    -- Timestamps
    ------------------------------------------------------------
    created_at TEXT DEFAULT (datetime('now')),
    modified_at TEXT,
    scanned_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files (hash);
CREATE INDEX IF NOT EXISTS idx_files_object_type ON files (object_type);
CREATE INDEX IF NOT EXISTS idx_files_parent_folder ON files (parent_folder);

CREATE INDEX IF NOT EXISTS idx_files_phash_faiss ON files (phash_faiss_index);
CREATE INDEX IF NOT EXISTS idx_files_orb_faiss ON files (orb_faiss_index);
CREATE INDEX IF NOT EXISTS idx_files_clip_faiss ON files (clip_faiss_index);
