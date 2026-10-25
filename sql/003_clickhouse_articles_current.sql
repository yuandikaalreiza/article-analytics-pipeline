-- Run against the configured ClickHouse database after Airbyte creates articles.
-- A normal view reads the latest data on every query; it stores no duplicate rows.
CREATE OR REPLACE VIEW articles_current AS
SELECT
    id,
    title,
    content,
    published_at,
    author_id,
    created_at,
    updated_at,
    deleted_at
FROM articles FINAL
WHERE _ab_cdc_deleted_at IS NULL;
