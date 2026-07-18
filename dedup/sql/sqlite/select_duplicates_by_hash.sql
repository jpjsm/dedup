SELECT hash as HASH, 
COUNT(*) AS dup_count, 
ARRAY_AGG(path) AS paths
FROM files
GROUP BY hash
HAVING COUNT(*) > 1;
