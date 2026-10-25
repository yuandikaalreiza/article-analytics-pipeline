# Milestone 4: Ongoing Article Simulation

## Current checkpoint

**Duration-based simulation implemented.** The existing CLI now supports live
inserts, edits, soft deletions, and optional hard deletions over a requested number of minutes. The
earlier exercises below are retained as history; see the progress log for the
latest database counts.

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

## Run the real-time simulation

From the repository root in PowerShell:

```powershell
uv run --locked python scripts/generate_articles.py simulate --duration 60
```

`--duration` is in **minutes**: 60 means one hour. By default, the command
performs 60 inserts, 30 updates, 10 soft deletes, and zero hard deletes across that hour. These
are totals for the entire run, not per-minute counts. Override them when needed:

```powershell
uv run --locked python scripts/generate_articles.py simulate --duration 60 --inserts 300 --updates 1000 --soft-deletes 100 --seed 42
```

Add `--hard-deletes N` to permanently remove N randomly selected active articles.
Soft and hard deletes share the available active-row budget. Deleted rows stop
being eligible for later operations; the last active row is retained until any
remaining edits are finished. Each hard delete logs the removed ID and database
execution timestamp after commit, without changing its former `updated_at`.

To request only one hard delete over 1.2 seconds (this changes real source data):

```powershell
uv run --locked python scripts/generate_articles.py simulate --duration 0.02 --inserts 0 --updates 0 --soft-deletes 0 --hard-deletes 1 --seed 42
```

Repeating the command deletes another article. The seed does not make it
idempotent. In this repository's verification run it removed ID 1398; future
runs can select another ID as the active dataset changes. Windows execution
used the uv verification environment documented in the progress log.

For a CDC deletion check, confirm the chosen ID exists in both systems before
deleting it, then inspect it after a successful Airbyte sync. Source removal is
separate from destination deletion handling; the latter must be verified.

- Operations occur in random order at jittered times distributed across the
  duration. The process remains running until the duration ends. A slow database
  can cause an overrun while it finishes the requested counts.
- Each operation uses its own transaction, committed before its ID and timestamp
  are printed. No database transaction is held open during a scheduling wait.
- Timestamps are actual aware UTC instants, not fabricated historical dates.
  New articles have equal creation, publication, and update times; edits advance
  `updated_at`; soft deletes set `deleted_at` and `updated_at` to the same instant.
  Timestamps need not be globally unique.
- Edits randomly select active articles, including existing historical articles
  and newly inserted rows. The same article can be edited more than once.
  Deleted rows are excluded. Updates and deletes preserve creation/publication.
- Counts can be zero, but the combined count must be positive. Impossible requests
  fail before writes. When starting empty, inserts precede operations needing a row.
- Ctrl+C stops gracefully with exit code 130 and prints completed and remaining
  counts. Database failures stop the run and roll back the current transaction;
  earlier commits remain. There is no automatic resume or retry.
- An optional seed repeats random scheduling, text, and target choices under the
  same starting rows and execution conditions. Actual wall-clock timestamps vary.
- Active-row selection uses a count and a random ordered offset. This is simple
  for this assessment dataset; it is not designed as a high-throughput load tool.
  Use one simulator at a time for predictable counts and target selection.

Airbyte keeps its separately configured hourly CDC schedule. The generator
does not trigger syncs or keep writing after its duration to advance CDC.
The earlier idle-source wait can still occur after generation stops.

For a short manual exercise, `--duration 0.1 --inserts 3 --updates 2
--soft-deletes 1` runs for six seconds. It changes real source data.
Afterward, inspect printed IDs and compare PostgreSQL with ClickHouse using
`FINAL` after a completed Airbyte sync. Updates count operations, not distinct IDs;
soft-deleted articles remain present, and active queries use `deleted_at IS NULL`.

The implementation was checked with unit scheduling tests using a fake clock
and real PostgreSQL lifecycle operations inside rolled-back transactions.
No hour-long simulator was started during implementation.
