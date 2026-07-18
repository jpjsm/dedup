UPDATE files
SET
    filename = $2,
    filename_no_ext = $3,
    extension = $4,
    parent_folder = $5,
    object_type = $6,
    hash = $7,
    size = $8,
    modified_at = $9,
    scanned_at = $10
WHERE id = $1;
