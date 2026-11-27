ALTER TABLE canvas_versions ADD COLUMN screen_count integer CHECK (screen_count > 0);
