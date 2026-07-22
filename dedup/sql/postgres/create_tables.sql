------------------------------------------------------------
-- 1. FILES TABLE
-- One row per file on disk
-- No similarity vectors stored here
------------------------------------------------------------
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

    -- Content hash (SHA256, BLAKE3, etc.)
    hash TEXT NOT NULL,

    -- File size
    size BIGINT NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    modified_at TIMESTAMPTZ,
    scanned_at TIMESTAMPTZ DEFAULT NOW(),

    -- FK to similarity table
    FOREIGN KEY (hash) REFERENCES similarity(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files (hash);
CREATE INDEX IF NOT EXISTS idx_files_object_type ON files (object_type);
CREATE INDEX IF NOT EXISTS idx_files_parent_folder ON files (parent_folder);



------------------------------------------------------------
-- 2. SIMILARITY TABLE
-- One row per unique content_hash
-- Stores multimodal vectors
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS similarity (
    content_hash TEXT PRIMARY KEY,      -- SHA256 or BLAKE3

    --------------------------------------------------------
    -- 1. Perceptual Hash (pHash)
    --------------------------------------------------------
    phash BYTEA,                        -- 64-bit or 128-bit pHash

    --------------------------------------------------------
    -- 2. ORB Descriptor (binary feature vector)
    --------------------------------------------------------
    orb_descriptor BYTEA,               -- flattened ORB descriptor

    --------------------------------------------------------
    -- 3. CLIP Embedding (semantic vector)
    --------------------------------------------------------
    clip_embedding BYTEA,               -- float32 array

    --------------------------------------------------------
    -- Timestamps
    --------------------------------------------------------
    created_at TIMESTAMPTZ DEFAULT NOW()
);



------------------------------------------------------------
-- 3. OPTIONAL: FAISS INDEX METADATA TABLE
-- Stores FAISS index positions for each modality
-- Useful but not required
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS similarity_faiss (
    content_hash TEXT PRIMARY KEY REFERENCES similarity(content_hash),

    phash_index BIGINT,
    orb_index BIGINT,
    clip_index BIGINT
);

CREATE INDEX IF NOT EXISTS idx_similarity_faiss_phash ON similarity_faiss (phash_index);
CREATE INDEX IF NOT EXISTS idx_similarity_faiss_orb ON similarity_faiss (orb_index);
CREATE INDEX IF NOT EXISTS idx_similarity_faiss_clip ON similarity_faiss (clip_index);
