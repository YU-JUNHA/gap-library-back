BEGIN;

ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS content_path VARCHAR(1024);

UPDATE documents
SET content_path = 'documents/' || id || '.md'
WHERE content_path IS NULL;

ALTER TABLE documents
  ALTER COLUMN content_path SET NOT NULL;

COMMIT;
