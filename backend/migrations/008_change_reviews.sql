CREATE TABLE change_reviews (
  id text PRIMARY KEY,
  project text NOT NULL REFERENCES records(id) ON DELETE CASCADE,
  subject text NOT NULL REFERENCES records(id) ON DELETE CASCADE,
  review_type text NOT NULL CHECK (review_type IN ('Document impact','Ticket scope')),
  operation text NOT NULL DEFAULT 'Edit' CHECK (operation IN ('Edit','Delete')),
  request text NOT NULL,
  signature text NOT NULL,
  snapshot jsonb NOT NULL,
  status text NOT NULL DEFAULT 'Pending',
  conclusion text,
  rationale text NOT NULL DEFAULT '',
  findings jsonb NOT NULL DEFAULT '[]',
  reviewer text,
  confirmation_note text,
  confirmed_by text,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  revision integer NOT NULL DEFAULT 1,
  superseded boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX one_current_change_review ON change_reviews(subject) WHERE NOT superseded;
CREATE INDEX change_reviews_project ON change_reviews(project,created_at DESC);
CREATE TABLE scope_baselines (
  document_id text PRIMARY KEY REFERENCES records(id) ON DELETE CASCADE,
  snapshot jsonb NOT NULL,
  review_id text NOT NULL REFERENCES change_reviews(id) ON DELETE CASCADE
);
