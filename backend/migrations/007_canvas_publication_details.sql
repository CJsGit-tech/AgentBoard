ALTER TABLE canvas_versions
    ADD COLUMN change_note text,
    ADD COLUMN sources jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN publisher text;
