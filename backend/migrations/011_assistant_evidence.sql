ALTER TABLE assistant_runs ADD COLUMN evidence_document_id text REFERENCES records(id) ON DELETE SET NULL;
