ALTER TABLE activity ADD COLUMN editor_role text;
CREATE INDEX activity_latest_edit ON activity(record, seq DESC)
  WHERE action IN ('Created', 'Updated');
