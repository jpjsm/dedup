UPDATE files
SET
    filename = ?,
    filename_no_ext = ?,
    extension = ?,
    parent_folder = ?,
    object_type = ?,
    hash = ?,
    size = ?,
    modified_at = ?,
    scanned_at = ?
WHERE id = ?;
