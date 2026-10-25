# Milestone 4: Ongoing Article Simulation

## Current checkpoint

**Step 1: one-time current inserts verified; review pending.** Five new articles
were committed using the existing CLI. The table now contains 2,518 rows.
All 2,513 previously stored articles, including the October dataset, are unchanged.

Read [the progress log](PROGRESS.md) for current results and [the roadmap](ROADMAP.md)
for milestone boundaries. Reuse the [existing Python CLI](02-python-inserts.md)
and [article schema](../sql/001_articles.sql); the
[historical generation guide](03-historical-generation.md) records the initial load.

## Purpose and sequence

Learn each article lifecycle operation through a small, observable CLI run.
First operate once, verify the result, and review it. Introduce repeated execution
after the individual operations are understood.

| Step | Purpose | Completion evidence | Status |
| --- | --- | --- | --- |
| 1. Current inserts | Reuse `insert` to create five articles with current UTC timestamps. | Five returned IDs exist after commit; all previous rows are unchanged. | Complete; review pending |
| 2. Update | Add a one-time command targeting a specific active article ID. Change its text and advance `updated_at`. | ID, author, creation, and publication stay unchanged; updated text persists; failure handling is verified. | Next |
| 3. Soft deletion | Add an explicit-ID operation setting deletion and update timestamps together. | Row remains present with coherent `deleted_at` and `updated_at`; define repeated-delete behavior during design. | Later |
| 4. Hard deletion | Add an explicit-ID operation removing a selected demonstration row. | Only the requested row disappears; other rows remain unchanged. | Later |
| 5. Repeated simulation | Add operation counts and configurable execution intervals. | Verified operation selection, transaction boundaries, error handling, and graceful stopping. | Later |

Use the existing environment configuration and caller-owned transactions. Keep
runtime components local. No scheduler, new database service, replication
configuration, or dependency is needed for these first operations.

## Step 1: insert current articles

The existing `insert` command already implements this behavior. No application
or test changes were required. Its small demonstration titles/content remain
useful for learning; this step focuses on lifecycle behavior.

Each new article explicitly supplies one aware UTC instant for all three fields:
`created_at = published_at = updated_at`. `deleted_at` is null. PostgreSQL assigns
the primary key. All requested insertions share one transaction; success and
IDs are printed only after commit. The existing tests already cover these
behaviors, including rollback and commit-failure output.

### Executed command

From the repository root in PowerShell, this was run once:

```powershell
uv run --locked python scripts/generate_articles.py insert --count 5 --author-id 7
```

Agent execution also passed `--cache-dir .cache/uv` and required access outside
the sandbox for localhost database connections. Connection settings continued
to come from `.env` or the process environment.

Repeating this command creates five more rows. Each invocation numbers its titles
from 1 again; repeated titles are allowed. Database IDs distinguish the rows.

### Verification: October 25, 2026

| Check | Observed result |
| --- | --- |
| Before insertion | 2,513 rows; the full dataset fingerprint matched the reviewed October checkpoint. |
| CLI output | `Inserted articles: 5`; IDs `2556, 2557, 2558, 2559, 2560`. |
| After insertion | 2,518 rows; exactly those five IDs were new. |
| Existing data | All 2,513 original stored-value fingerprints matched. |
| New article values | Titles/content matched the CLI output's article order; every author ID is 7 and deletion is null. |
| Timestamp consistency | Creation, publication, and update are equal for each article and fall within the observed execution window. |
| Earliest new timestamp | `2026-10-25T02:39:24.900622+00:00`. |
| Latest new timestamp | `2026-10-25T02:39:24.908135+00:00`. |
| Complete dataset fingerprint | `2518:e3789e5c005e4e354a06dcbb30e31f91`. |

Verification used a separate read-only connection after the real CLI committed.
No test suite was rerun because application and test code were unchanged. The
last maintained suite run passed 21 unit and 9 integration tests. This exercise
independently checked the actual new rows and preservation of existing data.

Identity values can have gaps after rolled-back or cleaned-up test insertions.
The highest ID therefore differs from the row count; that is expected.

### Inspect the retained rows

Use the container's `psql` client as explained in the
[PostgreSQL guide](01-postgresql.md). These are read-only inspection queries:

```sql
SELECT count(*) FROM public.articles;

SELECT id, title, author_id, created_at, published_at, updated_at, deleted_at
FROM public.articles
WHERE id IN (2556, 2557, 2558, 2559, 2560)
ORDER BY id;
```

## Next checkpoint

Review the five retained rows. Next, implement and verify a one-time update
command. Use one of these demonstration IDs for the first exercise, preserving
the historical dataset. Keep soft deletion, hard deletion, and intervals as
separate later steps. No update, deletion, or continuous loop ran in Step 1.
