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

    -- similarity search
    phash BIT(64),
    faiss_index BIGINT,
    clip_embedding VECTOR(512),

    -- Timestamps (with timezone)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    modified_at TIMESTAMPTZ,
    scanned_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files (hash);
CREATE INDEX IF NOT EXISTS idx_files_object_type ON files (object_type);
CREATE INDEX IF NOT EXISTS idx_files_parent_folder ON files (parent_folder);
