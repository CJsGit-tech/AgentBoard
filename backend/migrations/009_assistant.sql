-- Application-owned Assistant history. No credentials are stored in these tables.
CREATE TABLE assistant_conversations (
 id uuid PRIMARY KEY, project text NOT NULL REFERENCES records(id) ON DELETE CASCADE,
 title text NOT NULL, items jsonb NOT NULL DEFAULT '[]',
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE assistant_runs (
 id uuid PRIMARY KEY, conversation_id uuid NOT NULL REFERENCES assistant_conversations(id) ON DELETE CASCADE,
 project text NOT NULL REFERENCES records(id) ON DELETE CASCADE,
 request_id uuid NOT NULL, request_digest text NOT NULL,
 board_run_id text NOT NULL REFERENCES records(id) ON DELETE CASCADE,
 ticket_id text NOT NULL DEFAULT '', model text NOT NULL, mode text NOT NULL CHECK (mode IN ('Edit','Read only')),
 role_id text NOT NULL DEFAULT '', role_name text NOT NULL DEFAULT '', role_instructions text NOT NULL DEFAULT '',
 status text NOT NULL CHECK(status IN ('Queued','Running','Waiting for input','Blocked','Completed','Failed','Cancelled')),
 last_confirmed_step text NOT NULL DEFAULT 'Request saved', error text NOT NULL DEFAULT '',
 message text NOT NULL, checkout_key text NOT NULL DEFAULT '', workspace_config text NOT NULL DEFAULT '',
 restore_point jsonb, checks jsonb NOT NULL DEFAULT '[]', changed_files jsonb NOT NULL DEFAULT '[]',
 cancelled boolean NOT NULL DEFAULT false, lease_owner text, lease_until timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(conversation_id, request_id)
);
CREATE INDEX assistant_queue ON assistant_runs(status,created_at);
CREATE TABLE assistant_messages (
 id uuid PRIMARY KEY, conversation_id uuid NOT NULL REFERENCES assistant_conversations(id) ON DELETE CASCADE,
 run_id uuid REFERENCES assistant_runs(id) ON DELETE CASCADE, role text NOT NULL CHECK(role IN ('user','assistant')),
 content text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE assistant_events (
 run_id uuid NOT NULL REFERENCES assistant_runs(id) ON DELETE CASCADE,
 seq integer NOT NULL, type text NOT NULL, payload jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(run_id,seq)
);
CREATE TABLE assistant_tool_attempts (
 id uuid PRIMARY KEY, run_id uuid NOT NULL REFERENCES assistant_runs(id) ON DELETE CASCADE,
 name text NOT NULL, input_digest text NOT NULL, state text NOT NULL CHECK(state IN ('started','finished','failed','uncertain')),
 result jsonb, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE assistant_execution_configuration (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
 host_folder text NOT NULL, config_id text NOT NULL, updated_at timestamptz NOT NULL DEFAULT now()
);
