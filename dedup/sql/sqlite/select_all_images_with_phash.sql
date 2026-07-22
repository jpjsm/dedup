SELECT id, phash
FROM files
WHERE object_type = 'image'
  AND phash IS NOT NULL;
