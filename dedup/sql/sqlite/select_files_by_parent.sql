SELECT *
FROM files
WHERE parent_folder = ?
ORDER BY filename;
