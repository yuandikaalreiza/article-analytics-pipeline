# Milestone 3: October 2026 Article Generation

## Current checkpoint

**October ingestion reviewed and complete.** The learner requested proceeding
directly to ingestion after the scope revision. Generation, preview, loader
checks, and the first 2,500-row load are complete. The table now contains 2,513
rows, including all 13 original articles unchanged. The historical window starts
on October 1, 2026, replacing the earlier proposal to start in 2016.

Read [the progress log](PROGRESS.md) for actual results and [the roadmap](ROADMAP.md)
for milestone boundaries. Build on the reviewed [Python CLI](02-python-inserts.md)
and the existing [article schema](../sql/001_articles.sql).

## First dataset

| Choice | First exercise |
| --- | --- |
| New articles | 2,500 total; configurable through the CLI. |
| Start | October 1, 2026, at 00:00:00 UTC, inclusive. |
| End | A fixed UTC cutoff captured before the first load; no later than the run's start time or October 26 at 00:00:00 UTC. Exclusive. |
| Intended coverage | October 1 through the elapsed portion of October 25 for a load run on October 25. |
| Distribution | Variable daily counts and more publications during daytime; synthetic assumptions, not measured company traffic. |
| Existing data | Append to the existing table; preserve every prior row. |
| Expected total | Baseline row count plus 2,500 after a successful commit. |

The verified baseline was 13 rows, and the resulting total is 2,513.
Inspect the current baseline before any additional load.
The date range does not determine the count: 2,500 across 25 calendar dates is
an average of 100 per date, not a requirement for exactly 100 every day.
The last day may be partial. Date boundaries in this exercise use UTC;
displaying them in Jakarta time can place some rows on different local dates.

Resolve and print the exact cutoff before loading. Allow it to be supplied
explicitly on later runs; reject an empty range or a cutoff in the future.
Record the actual cutoff in the progress log so the dataset can be reproduced.
If execution happens after October 25, keep the October window rather than
silently extending it. Do not use a moving current time inside the article loop.

## Implementation

- Extend [generate_articles.py](../scripts/generate_articles.py) with a separate
  historical-generation subcommand. Keep the existing `check` and small `insert`
  commands working as reviewed.
- Reuse required environment settings, safe error handling, parameterized
  insertion, and caller-owned transactions. Database connection values remain
  in `.env` or process environment variables.
- Add small helpers for range validation and seeded article generation in the
  existing script. No new package layout or dependency is needed initially.
- Expose count, start, cutoff, seed, positive author ID, and batch size through
  CLI options. Require count and explicit date inputs; the guide supplies the
  October exercise values. Record a supplied seed, or resolve and print one
  before generation if omitted.
- Use a dedicated standard-library random generator. Identical seed, resolved
  date range, count, author, and generator version reproduce article values.
  Database-generated IDs are excluded from that promise. Batch size should not
  change the generated values or their order.
- Combine a small set of original Indonesian news-style title/content templates
  with topics and locations. Keep articles clearly labeled as synthetic practice
  data. No scraped news, network calls, or additional text library is needed.
- Start with one configurable author, matching the existing CLI. Author pools
  and more sophisticated text generation can follow a reviewed need.

### Timestamp rules

Generate publication times in the selected interval, with variation across days
and a simple daytime bias. These are learning assumptions, not a model of real
kumparan publishing patterns.

For each article, explicitly set `created_at <= published_at = updated_at` and
`deleted_at = NULL`. Choose creation time between the selected start and
publication, with at most a six-hour drafting delay. All values are aware UTC
instants. Publication and creation must precede the exclusive cutoff.
Updates and deletions will be exercised in the next milestone.

### Loading and failures

First validate the arguments and generate a small preview without connecting to
PostgreSQL. The preview should show representative articles and aggregate date
checks, not thousands of lines.

For the 2,500-row exercise, retain the existing insertion helper and feed it
batches of 500 articles by default. Discard returned IDs after counting each
batch rather than keeping every ID for final output. Batches limit application
memory; the existing helper still executes one INSERT per row. This is an
intentional first implementation for the small dataset, not a claim of bulk
loading performance for millions of rows.

Use one transaction for the entire load. If a later batch fails, roll back all
new rows from that invocation. Print final success only after commit, including
the inserted count and elapsed time. Do not automatically retry an ambiguous
commit outcome; verify the database before rerunning. A rerun normally appends
another 2,500 rows, even with the same seed. Seeds do not provide deduplication.

Keep the current Docker service and persistent volume. No schema migration,
table reset, index addition, or volume recreation is needed for this exercise.
Measure loading time and table size during verification. Design a faster writer
before attempting 100K or 1M records; that is outside this first October load.

## Ordered learning steps

| Step | Work and files | Completion evidence |
| --- | --- | --- |
| 1. Revise the plan | This guide, roadmap, and progress log. | October scope and expected count documented; learner reviews. |
| 2. Generate and preview | Extend the existing script and unit suite with range validation, seed handling, templates, timestamp generation, and preview. | Same inputs reproduce values; preview creates no connection; boundaries and invalid inputs tested. |
| 3. Implement loading | Extend the CLI and integration suite with bounded batches and one transaction. | Small uniquely labeled fixtures commit correctly; a later-batch failure rolls everything back; existing tests still pass. |
| 4. Load and inspect October data | Run the reviewed command once for 2,500 rows; record exact inputs and results here and in the progress log. | Actual count increases by 2,500, prior rows match, dates are valid, and timing/storage observations are recorded. |

All four steps are complete. The learner explicitly requested ingestion, so
Steps 2 through 4 were performed in this turn: unit checks, integration checks,
preview, one real load, then independent verification. No further load or
milestone starts automatically.

## Verification and acceptance

- Unit checks: reject invalid counts, authors, batches, naive cutoffs, future
  cutoffs, and reversed/empty intervals before database access. Test October 1
  and cutoff boundaries, short intervals, coherent UTC lifecycle values, seed
  reproducibility, batch-size independence, and nonempty synthetic text.
- Preview checks: exactly the requested generation count is represented in
  summary checks, only a few sample rows are displayed, and no database
  connection is opened.
- Integration checks: use unique fixture labels and exact cleanup as in the
  current test suite. Verify committed counts and stored values, and prove an
  invalid row in a later batch leaves no earlier batch committed. Preserve the
  original dataset and keep the existing 21 tests passing.
- Actual load: capture the baseline count and existing row fingerprints, record
  resolved seed/start/cutoff/count/author/batch size and the source commit, then
  run once. Inspect the new rows for lifecycle rules, date bounds, null deletion,
  nonempty text, and varied publication dates. Compare all original row values.
- Record new-row count, resulting total, daily distribution, elapsed load time,
  and table/index size observations. Generated rows remain for the learner to
  inspect; test fixtures alone are cleaned up.

## Commands and actual results: October 25, 2026

The first load used the following explicit inputs. These dates use UTC, not
Jakarta calendar boundaries. The cutoff was captured before implementation
and remained fixed through preview, loading, and verification.

```powershell
$historicalArgs = @(
    "historical",
    "--count", "2500",
    "--start-date", "2026-10-01",
    "--until", "2026-10-25T02:26:52Z",
    "--seed", "20261001",
    "--author-id", "7",
    "--batch-size", "500"
)
uv run --locked python scripts/generate_articles.py @historicalArgs --preview
```

Preview generated all 2,500 values while showing three samples. It made no
database connection. The following load command was then executed once:

```powershell
uv run --locked python scripts/generate_articles.py @historicalArgs
```

Repeating the load appends another 2,500 articles. Preview is the command to
repeat when inspecting generation without adding rows. Agent execution also
passed `--cache-dir .cache/uv`; localhost database access ran outside the sandbox.

| Check | Observed result |
| --- | --- |
| Unit suite | 21 tests passed in 0.103 seconds, including 6 new historical checks. |
| Integration suite | 9 tests passed in 6.506 seconds; zero skips, including 3 new historical checks. |
| Transaction | One commit across five 500-row batches; load reported 2.516 seconds. |
| Row count | 13 before; 2,500 inserted; 2,513 after. |
| Original data | Every original ID and stored-value fingerprint matched. |
| Generated values | All seven generated fields in every new row matched regenerated seeded values. |
| Publication minimum | `2026-10-01T00:46:48.600532+00:00`. |
| Publication maximum | `2026-10-25T01:49:36.006776+00:00`, before the exclusive cutoff. |
| Lifecycle | All 2,500 have coherent UTC timestamps and null deletion; author ID is 7. |
| Table size | 49,152 bytes immediately before loading; 1,916,928 afterward. Includes table auxiliary storage, excludes indexes. |
| Index size | 16,384 bytes before; 73,728 afterward. |
| Table plus indexes | 65,536 bytes before; 1,990,656 afterward, about 1.90 MiB. |

Storage figures are PostgreSQL relation measurements, not the total Docker volume
size. Test activity had increased allocated pages before the measured load.
Database-wide storage also includes WAL, catalogs, and other database files.

The source was based on commit `32d9534` plus the uncommitted generator changes.
The executed script's SHA-256 was
`c1b9fedd5c977d927590c50675c93ed4b2db116b1b255db74158ba7b6231c341`.
The script, tests, and documentation were subsequently reviewed for the
milestone commit; the detailed checkpoint is in the progress log.

### Observed new articles per UTC date

| October date | Rows | October date | Rows |
| --- | ---: | --- | ---: |
| 01 | 120 | 14 | 104 |
| 02 | 96 | 15 | 95 |
| 03 | 74 | 16 | 123 |
| 04 | 96 | 17 | 112 |
| 05 | 98 | 18 | 83 |
| 06 | 112 | 19 | 125 |
| 07 | 112 | 20 | 121 |
| 08 | 106 | 21 | 115 |
| 09 | 105 | 22 | 101 |
| 10 | 78 | 23 | 123 |
| 11 | 95 | 24 | 88 |
| 12 | 110 | 25 | 5 |
| 13 | 103 | | |

October 25 contains only the elapsed first 2 hours and 26 minutes before the
cutoff. The simple weighting favors 08:00-20:00 UTC by a factor of three and
weekdays by a factor of 1.2; these synthetic assumptions explain the uneven
counts and do not represent observed traffic.

For inspection through a SQL client, these queries read the retained dataset:

```sql
SELECT count(*) FROM public.articles;

SELECT (published_at AT TIME ZONE 'UTC')::date AS publication_date,
       count(*)
FROM public.articles
WHERE title LIKE '[historical seed=20261001] %'
GROUP BY 1
ORDER BY 1;
```

Ongoing simulation and pipeline integrations remain deferred. The earlier SQL
exercises containing 2016 timestamps remain valid historical records; the new
generator scope does not rewrite them. The October dataset has been reviewed;
planning ongoing operation simulation is the next learning step.
