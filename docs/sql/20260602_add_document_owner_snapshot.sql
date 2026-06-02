BEGIN;

ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS owner_name VARCHAR(100),
  ADD COLUMN IF NOT EXISTS owner_avatar_url VARCHAR(1024);

UPDATE documents AS d
SET owner_name = u.name,
    owner_avatar_url = u.avatar_url
FROM users AS u
WHERE d.owner_id = u.id;

ALTER TABLE documents
  ALTER COLUMN owner_name SET NOT NULL;

COMMIT;
