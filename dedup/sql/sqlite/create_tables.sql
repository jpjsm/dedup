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
    object_type TEXT NOT NULL,

    -- Hashing
    hash TEXT NOT NULL,
    size INTEGER NOT NULL,

    -- Similarity fields
    phash BLOB,              -- 64-bit perceptual hash
    faiss_index INTEGER,     -- index position inside FAISS
    clip_embedding BLOB,     -- serialized float32[512] vector
    
    -- Timestamps stored as ISO-8601 TEXT
    created_at TEXT DEFAULT (datetime('now')),
    modified_at TEXT,
    scanned_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files (hash);
CREATE INDEX IF NOT EXISTS idx_files_object_type ON files (object_type);
CREATE INDEX IF NOT EXISTS idx_files_parent_folder ON files (parent_folder);
