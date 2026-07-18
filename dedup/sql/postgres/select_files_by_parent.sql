SELECT *
FROM files
WHERE parent_folder = $1
ORDER BY filename;
