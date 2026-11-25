CREATE UNIQUE INDEX assistant_board_run ON assistant_runs(board_run_id);
CREATE INDEX assistant_project_runs ON assistant_runs(project,created_at DESC);
CREATE INDEX assistant_conversation_runs ON assistant_runs(conversation_id,created_at);
CREATE INDEX assistant_conversation_messages ON assistant_messages(conversation_id,created_at);
CREATE INDEX assistant_project_conversations ON assistant_conversations(project,updated_at DESC);
CREATE INDEX assistant_attempts_by_run ON assistant_tool_attempts(run_id,created_at);
