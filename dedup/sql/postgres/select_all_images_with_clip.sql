SELECT id, clip_embedding
FROM files
WHERE object_type = 'image'
  AND clip_embedding IS NOT NULL;
