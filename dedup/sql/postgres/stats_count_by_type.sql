SELECT object_type, COUNT(*) AS type_count
FROM files
GROUP BY object_type
ORDER BY type_count DESC;
