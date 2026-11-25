CREATE TABLE canvas_versions (
    document_id text NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    version integer NOT NULL CHECK (version > 0),
    asset_key uuid NOT NULL UNIQUE,
    digest text NOT NULL,
    published_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (document_id, version)
);
CREATE TABLE canvas_files (
    asset_key uuid NOT NULL REFERENCES canvas_versions(asset_key) ON DELETE CASCADE,
    path text NOT NULL,
    content bytea NOT NULL,
    PRIMARY KEY (asset_key, path)
);
