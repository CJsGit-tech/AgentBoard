-- Import complete, schema-compatible legacy assignments. Preserve unrecognized text.
WITH legacy AS (
    SELECT id, regexp_match(rtrim(data->>'description'), '(?:^|\n)Tags: ([a-z0-9]+(?:-[a-z0-9]+)*(?:, *[a-z0-9]+(?:-[a-z0-9]+)*)*)$') AS captured
    FROM records WHERE kind IN ('documents','tickets') AND NOT data ? 'tags'
), assignments AS (
    SELECT id, array_agg(DISTINCT tag ORDER BY tag) AS tags
    FROM legacy CROSS JOIN LATERAL regexp_split_to_table(captured[1], ', *') AS tag
    GROUP BY id HAVING max(length(tag)) <= 120 AND count(DISTINCT tag) <= 200
)
UPDATE records r SET data = r.data || jsonb_build_object('tags', a.tags, 'description',
    rtrim(regexp_replace(rtrim(r.data->>'description'), '(?:^|\n)Tags: [^\n]+$', '')))
FROM assignments a WHERE r.id=a.id;
