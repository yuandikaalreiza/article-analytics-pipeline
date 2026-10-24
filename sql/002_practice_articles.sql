-- Run with psql -X -v ON_ERROR_STOP=1 -f -.
-- Leaves two labeled rows for inspection. Run once per fresh practice dataset.
BEGIN;

-- A deliberate error stops a repeated run before it changes existing rows.
SELECT 1 / CASE WHEN NOT EXISTS (
    SELECT 1 FROM public.articles WHERE title LIKE '[practice step 5]%'
) THEN 1 ELSE 0 END AS practice_dataset_is_new;

-- INSERT: explicit historical timestamps satisfy the lifecycle rules.
INSERT INTO public.articles (
    title, content, published_at, author_id, created_at, updated_at
) VALUES (
    '[practice step 5] Persistence article',
    'A historical practice article for the PostgreSQL learning milestone.',
    '2016-01-01 01:00:00+00', 1,
    '2016-01-01 00:00:00+00', '2016-01-01 01:00:00+00'
)
RETURNING id, created_at, updated_at
\gset active_

-- UPDATE: explicitly advance updated_at and preserve the identity/creation time.
UPDATE public.articles
SET content = 'Updated practice article retained for persistence verification.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = :active_id
RETURNING id, created_at, updated_at
\gset updated_

SELECT json_build_object(
    'update_preserved_id', :active_id = :updated_id,
    'update_preserved_created_at',
        :'active_created_at'::timestamptz = :'updated_created_at'::timestamptz,
    'update_advanced_updated_at',
        :'updated_updated_at'::timestamptz > :'active_updated_at'::timestamptz
);

-- SOFT DELETE: retain the row and set deletion/update timestamps together.
INSERT INTO public.articles (title, content, published_at, author_id)
VALUES ('[practice step 5] Soft-deleted article',
        'This row remains available when soft-deleted.', CURRENT_TIMESTAMP, 2)
RETURNING id
\gset soft_

UPDATE public.articles
SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
WHERE id = :soft_id;

SELECT json_build_object('soft_delete_retained_row', count(*) = 1)
FROM public.articles
WHERE id = :soft_id AND deleted_at IS NOT NULL AND deleted_at = updated_at;

-- HARD DELETE: permanently remove only the newly inserted practice row.
INSERT INTO public.articles (title, content, published_at, author_id)
VALUES ('[practice step 5] Hard-delete article',
        'This row is intentionally removed.', CURRENT_TIMESTAMP, 3)
RETURNING id
\gset hard_

DELETE FROM public.articles WHERE id = :hard_id;
SELECT json_build_object('hard_delete_removed_row', count(*) = 0)
FROM public.articles WHERE id = :hard_id;

COMMIT;

-- ROLLBACK: undo an insert, an update, and a delete in one transaction.
BEGIN;
INSERT INTO public.articles (title, content, published_at, author_id)
VALUES ('[practice step 5] Rolled-back article',
        'This insert must not be committed.', CURRENT_TIMESTAMP, 4)
RETURNING id
\gset rollback_

UPDATE public.articles SET content = 'This update must be rolled back.'
WHERE id = :active_id;
DELETE FROM public.articles WHERE id = :soft_id;
ROLLBACK;

SELECT json_build_object(
    'rollback_removed_insert',
        NOT EXISTS (SELECT 1 FROM public.articles WHERE id = :rollback_id),
    'rollback_restored_update',
        EXISTS (SELECT 1 FROM public.articles WHERE id = :active_id
                AND content = 'Updated practice article retained for persistence verification.'),
    'rollback_restored_delete',
        EXISTS (SELECT 1 FROM public.articles WHERE id = :soft_id
                AND deleted_at IS NOT NULL)
);

SELECT id, title, created_at, published_at, updated_at, deleted_at
FROM public.articles WHERE id IN (:active_id, :soft_id) ORDER BY id;
