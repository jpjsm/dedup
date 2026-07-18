INSERT OR IGNORE INTO files (
    path, filename, filename_no_ext, extension,
    parent_folder, object_type, hash, size,
    created_at, modified_at, scanned_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
