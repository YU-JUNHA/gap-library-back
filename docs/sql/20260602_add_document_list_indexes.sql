BEGIN;

CREATE INDEX IF NOT EXISTS ix_documents_created_at
ON documents (created_at);

CREATE INDEX IF NOT EXISTS ix_documents_category_id
ON documents (category_id);

CREATE INDEX IF NOT EXISTS ix_documents_owner_name
ON documents (owner_name);

CREATE INDEX IF NOT EXISTS ix_documents_search_tsv
ON documents
USING gin (
  to_tsvector(
    'simple',
    coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(content_text, '')
  )
);

COMMIT;
