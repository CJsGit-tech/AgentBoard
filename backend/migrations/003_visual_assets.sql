CREATE TABLE visual_assets (
    document_id text NOT NULL REFERENCES records(id),
    filename text NOT NULL,
    digest text NOT NULL,
    image bytea NOT NULL,
    PRIMARY KEY (document_id, filename)
);
