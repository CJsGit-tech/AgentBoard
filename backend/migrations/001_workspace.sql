CREATE TABLE records (
  id text PRIMARY KEY,
  kind text NOT NULL CHECK (kind IN ('projects','milestones','roles','documents','tickets','runs')),
  project text NOT NULL,
  data jsonb NOT NULL,
  revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
  deleted boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX records_project_kind ON records(project,kind) WHERE NOT deleted;
CREATE TABLE activity (
  seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  at timestamptz NOT NULL DEFAULT clock_timestamp(),
  project text NOT NULL,
  actor text NOT NULL,
  action text NOT NULL,
  kind text NOT NULL,
  record text NOT NULL,
  name text NOT NULL,
  changes jsonb NOT NULL
);
CREATE INDEX activity_by_project ON activity(project,seq DESC);
