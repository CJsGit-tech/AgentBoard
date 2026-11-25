-- Invalidate workspace caches even when a purge removes only older activity.
CREATE TABLE workspace_purge_version (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    version bigint NOT NULL DEFAULT 0
);
INSERT INTO workspace_purge_version DEFAULT VALUES;
