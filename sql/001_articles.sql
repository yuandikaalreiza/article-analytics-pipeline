-- Run explicitly with psql -v ON_ERROR_STOP=1; this script is not a migration.
BEGIN;

CREATE TABLE IF NOT EXISTS public.articles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    author_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,

    CONSTRAINT articles_author_id_positive
        CHECK (author_id > 0),
    CONSTRAINT articles_created_before_publication
        CHECK (created_at <= published_at),
    CONSTRAINT articles_updated_after_publication
        CHECK (published_at <= updated_at),
    CONSTRAINT articles_deleted_within_lifecycle
        CHECK (
            deleted_at IS NULL
            OR (published_at <= deleted_at AND deleted_at <= updated_at)
        )
);

COMMIT;
