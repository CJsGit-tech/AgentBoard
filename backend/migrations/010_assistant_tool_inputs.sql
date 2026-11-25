-- Bounded non-secret tool metadata supports reconciliation without replay.
ALTER TABLE assistant_tool_attempts ADD COLUMN inputs jsonb NOT NULL DEFAULT '{}';
