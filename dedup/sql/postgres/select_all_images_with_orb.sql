SELECT id, orb_descriptor
FROM files
WHERE object_type = 'image'
  AND orb_descriptor IS NOT NULL;
