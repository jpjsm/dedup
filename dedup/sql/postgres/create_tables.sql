CREATE TABLE IF NOT EXISTS files (
    id BIGSERIAL PRIMARY KEY,

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
    size BIGINT NOT NULL,

    ------------------------------------------------------------
    -- 1. Perceptual Hash (pHash)
    ------------------------------------------------------------
    phash BYTEA,                 -- 64-bit perceptual hash
    phash_faiss_index BIGINT,      -- FAISS binary index position

    ------------------------------------------------------------
    -- 2. ORB Descriptor (binary feature vector)
    ------------------------------------------------------------
    orb_descriptor BYTEA,          -- 32-byte ORB mean descriptor
    orb_faiss_index BIGINT,        -- FAISS binary index position

    ------------------------------------------------------------
    -- 3. CLIP Embedding (semantic vector)
    ------------------------------------------------------------
    clip_embedding BYTEA,    -- 512-dim float32 embedding
    clip_faiss_index BIGINT,       -- FAISS float index position

    ------------------------------------------------------------
    -- Timestamps (with timezone)
    ------------------------------------------------------------
    created_at TIMESTAMPTZ DEFAULT NOW(),
    modified_at TIMESTAMPTZ,
    scanned_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files (hash);
CREATE INDEX IF NOT EXISTS idx_files_object_type ON files (object_type);
CREATE INDEX IF NOT EXISTS idx_files_parent_folder ON files (parent_folder);

-- Optional: speed up similarity lookups
CREATE INDEX IF NOT EXISTS idx_files_phash_faiss ON files (phash_faiss_index);
CREATE INDEX IF NOT EXISTS idx_files_orb_faiss ON files (orb_faiss_index);
CREATE INDEX IF NOT EXISTS idx_files_clip_faiss ON files (clip_faiss_index);
