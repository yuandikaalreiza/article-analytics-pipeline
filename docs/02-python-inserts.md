# Milestone 2: Basic Python Inserts

## Current checkpoint

**Milestone 2 reviewed and complete.** The CLI's unit
and real PostgreSQL integration suites are implemented. All 21 tests passed.
The source database contained 13 articles before this step, and all 13 were
preserved after fixture cleanup. Planning historical generation is the next step.

Read [the roadmap](ROADMAP.md) for milestone boundaries and [the progress log](PROGRESS.md)
for actual completion evidence. The [PostgreSQL guide](01-postgresql.md) remains
the source of truth for the database schema and SQL learning exercises.

## Goal and starting point

Run a small Python CLI on the host machine, connect to PostgreSQL through its
published localhost port, and insert a few articles that satisfy the existing
schema. Learn configuration, database connections, parameterized SQL, and
transactions before adding historical generation or continuous simulation.

The handoff check confirmed a healthy PostgreSQL service with two existing
articles: one active and one soft-deleted. Preserve both. Python inserts append
rows; they do not reset the database or assume an empty table.

Read-only environment inspection found:

| Component | Existing version |
| --- | --- |
| Python in `.venv` | `3.13.16` |
| uv | `0.13.1` |
| psycopg / psycopg-binary | `3.3.6` / `3.3.6` |
| python-dotenv | `1.2.4` |

These versions were initially read from installed metadata. Step 2 subsequently
verified the binary driver and dotenv imports through uv. Step 3 then verified
Python-to-PostgreSQL connectivity and the unchanged article data.

## Ordered learning steps

| Step | Work | Completion evidence |
| --- | --- | --- |
| 1. Design the CLI | Record behavior, dependencies, configuration, and checks in this guide. | Reviewable plan; no Python implementation. |
| 2. Declare dependencies | Add `pyproject.toml` and `uv.lock`; verify the existing environment. | Lockfile validates; driver and dotenv import successfully. |
| 3. Check the connection | Add the `check` subcommand in `scripts/generate_articles.py`. | Python reports the database, user, version, UTC session timezone, and table availability without changing rows. |
| 4. Insert a few articles | Add the `insert` subcommand in that same script. | A small run returns generated IDs after committing; SQL confirms exactly those new rows. |
| 5. Verify and explain | Add targeted tests and record success/failure cases. | Argument, configuration, timestamp, transaction, and integration checks pass; existing rows are unchanged. |

Steps 1 through 5 are complete and reviewed. Plan the next generator capability
before implementing it.

## Dependencies and file layout

Use Python 3.13 already available in `.venv`.
[`pyproject.toml`](../pyproject.toml) declares Python `>=3.13` and pins
`psycopg[binary]==3.3.6` and `python-dotenv==1.2.4`, matching the existing
environment. [`uv.lock`](../uv.lock) records the resolved dependencies and their
distribution hashes. Use standard-library `argparse`, `datetime`, `logging`, and
`unittest` for the remaining work.

The binary Psycopg distribution avoids a separate local compiler/libpq setup.
See [Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html).

Use a single application script with small helpers for configuration, article
creation, and insertion. No installable package or build backend is needed yet.
Keep later tests under `tests/`, separating unit checks from explicitly invoked
database integration checks. Create each file when its learning step starts.

Preserve the existing `.venv` and caches. Use `uv lock` when deliberately updating
dependencies, followed by `uv sync --locked --inexact`; inexact syncing retains
unrelated installed packages. Routine Python commands use `uv run --locked`,
which also uses inexact syncing by default. See
[uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).

### Step 2: commands and observed results

The existing interpreter was selected explicitly, with automatic Python
downloads disabled. The commands used the ignored repository cache rather than
requiring a global cache change:

```powershell
uv lock --python .venv/Scripts/python.exe --no-python-downloads --cache-dir .cache/uv
uv sync --locked --inexact --python .venv/Scripts/python.exe --no-python-downloads --cache-dir .cache/uv
uv lock --check --offline --python .venv/Scripts/python.exe --no-python-downloads --cache-dir .cache/uv
```

Lock generation resolved five entries, including the project itself. Sync
checked four external packages without installing, removing, or upgrading any
package. The offline lockfile check passed. Before/after package inventories
confirmed that all 14 previously installed packages retained their versions.

Imports were verified using `uv run --locked` with that same interpreter and
cache selection. The essential import check for routine use is:

```powershell
uv run --locked python -c "import psycopg; from psycopg import pq; from dotenv import load_dotenv; print(psycopg.__version__, pq.__impl__)"
```

The verified driver version was `3.3.6`, implementation `binary`, with
`python-dotenv` version `1.2.4` on Python `3.13.16`. No database connection was
opened by the import check.

The first sandboxed lock generation could not resolve PyPI. Repeating the same
metadata lookup outside the sandbox succeeded. Package-index access is needed
when dependencies are not cached; application execution remains fully local.

`POSTGRES_HOST=127.0.0.1` is now documented in [`.env.example`](../.env.example).
The actual local `.env` and its password were left unchanged.

For a fresh checkout with uv available, `uv sync --locked --inexact` creates the
environment from the lockfile, using a compatible Python installation or uv's
normal interpreter provisioning. The existing-checkout commands above instead
reuse the already available interpreter and do not download another Python.

**Step 2 result:** dependency management and imports were verified. The next
section records Step 3's connection and failure checks.

## Step 3: check the database from Python

The implemented script is
[`scripts/generate_articles.py`](../scripts/generate_articles.py). Run from the
repository root:

```powershell
uv run --locked python scripts/generate_articles.py --help
uv run --locked python scripts/generate_articles.py check
```

During agent verification, `--cache-dir .cache/uv` was also passed to uv to keep
cache access inside the workspace. The first connection attempt was blocked by
the sandbox; the same check succeeded outside it, without changing Docker,
firewall, or database settings.

The verified output was:

```text
Database: article_source
User: article_dev
PostgreSQL: 18.6 (Debian 18.6-1.pgdg13+2)
Timezone: UTC
Read-only transaction: on
Articles table: public.articles
```

### Read the script in execution order

1. `main()` parses the required subcommand before loading configuration. Help
   and usage errors therefore do not require database access.
2. `load_settings()` explicitly locates the repository-root `.env`, preserves
   process overrides, and validates the host, database, user, port, and password.
3. `check_database()` opens a Psycopg connection with a five-second connect
   timeout and marks its transaction read-only before executing SQL. See
   [Psycopg transaction characteristics](https://www.psycopg.org/psycopg3/docs/api/connections.html#psycopg.Connection.read_only).
4. A single query reads connection facts and checks whether `public.articles`
   exists. It also reads `transaction_read_only`, proving the query ran in a
   read-only transaction.
5. The connection context finishes the transaction and closes the connection.
   Only then does the command report success. A missing table produces an error
   instead; the script never applies the schema automatically.

The main-entry guard keeps importing the script free of configuration loading
and database connections. Future insertion helpers can be added to the same
file without running anything on import.

Settings validation uses `get_required_env()` for the shared missing/blank check.
`load_settings()` reads each setting explicitly, catches dotenv read failures
only around dotenv loading, and catches integer conversion failures only around
port parsing. These failures become `SettingsError`, so `main()` has one clear
configuration-error handler. This keeps required-value checks, conversion, and
CLI reporting easy to follow without introducing fallback connection values.

### Verified behavior

| Scenario | Observed result |
| --- | --- |
| Normal `check` | Exit `0`, correct database facts, UTC, read-only `on`, table available. |
| Run from the `scripts` directory | Exit `0`; root `.env` still found correctly. |
| `--help` | Exit `0` and describe the `check` command. |
| No subcommand | Exit `2` with an argparse usage error. |
| Override to an unused local port | Exit `1` with a safe connection error in about `5.63` seconds. |
| Override database to `postgres`, which has no articles table | Exit `1` with the missing-table message; no schema changes. |
| Nonnumeric port | Exit `1` with a concise configuration error. |
| Example password placeholder | Exit `1` before connecting. |
| Wrong password | Exit `1` without exposing the supplied test password or a traceback. |
| Import the module | Does not load settings or open a connection. |

Failure checks temporarily changed process variables and restored them afterward;
the actual `.env` was unchanged. An initial combined check exposed a Windows
test-procedure issue: restoring a previously absent variable through the .NET
environment API left an empty port override. Removing the absent variable from
`Env:` fixed the verification procedure, and all failure checks then passed.
The application correctly treats an explicitly empty port as invalid.

The pre/post SQL snapshot remained
`2:b5934dc43e2939ed872b4247a703c561`: two articles with every stored value
unchanged. This comparison was separate from the Python command's own query.

**Review checkpoint:** the connection command is ready. Step 4 will add inserts;
this step introduced no generated rows or schema changes.

## Step 4: insert a few articles

Both commands are now implemented. From the repository root:

```powershell
uv run --locked python scripts/generate_articles.py check
uv run --locked python scripts/generate_articles.py insert
uv run --locked python scripts/generate_articles.py insert --count 5 --author-id 7
```

The first insert uses the defaults of one article and author `1`. The second
requests five articles for author `7`. The author field is a positive numeric
identifier; there is still no authors table or foreign key.

Observed output from the two insertion runs:

```text
Inserted articles: 1
IDs: 13
```

```text
Inserted articles: 5
IDs: 14, 15, 16, 17, 18
```

IDs are observations of this database, not values to expect on another run.
Article text is labeled `[python demo]` so it is distinguishable from the earlier
SQL practice rows. Repeating a run appends more articles, even when their text
matches existing demonstrations.

### Read the insertion flow

1. `positive_int()` validates `--count` and `--author-id` through argparse before
   settings loading or database access.
2. `make_article()` creates one article with a timezone-aware UTC instant shared
   by creation, publication, and update. It leaves `deleted_at` null and omits
   `id` so PostgreSQL generates it.
3. `main()` supplies a generator of articles to `insert_articles()` inside a
   Psycopg connection context. The helper uses a cursor and returns generated
   IDs without committing individual rows.
4. Named SQL parameters pass values separately from the statement; text is not
   interpolated into SQL. The demonstration content includes an apostrophe,
   which was stored correctly. See [Psycopg parameter binding](https://www.psycopg.org/psycopg3/docs/basic/params.html).
5. Successful context exit commits the entire run and closes the connection.
   Any insertion error escapes that context so it rolls back before the CLI
   reports a safe error. Count and IDs are printed only after successful commit.

This implementation intentionally uses one insert statement per article for a
small learning dataset. Generation is lazy, but returned IDs are retained in
memory. Large historical loads and bulk insertion will be designed later.

### Verified results

| Scenario | Observed result |
| --- | --- |
| Default invocation | One committed article, ID `13`, author `1`. |
| Five-article invocation | Five committed articles, IDs `14` through `18`, author `7`. |
| Stored timestamps and deletion state | Each new article has matching creation/publication/update times and null deletion. |
| Existing rows | Fingerprints for both SQL practice rows were unchanged. |
| Total row count | Increased from `2` to `8`; exactly six new returned IDs are present. |
| Invalid count/author values | Eight zero, negative, nonnumeric, and fractional cases exited `2` before settings loading or connection. |
| Failed second insertion | A valid probe followed by an invalid author caused a constraint error; the first insertion rolled back. All eight committed rows were unchanged. |
| Read-only `check` after insertion | Still exited `0`, reporting UTC, read-only `on`, and table availability. |

The transaction smoke check called the insertion helper with two articles, one
valid and one with author `0`, inside the same connection context used by the
CLI. A separate connection compared the full row count and fingerprint before
and after rollback. No probe article remained. This verifies the rollback path
without adding a public failure-injection flag or changing database constraints.

The six generated rows remain available to inspect. Failed probe inserts may
advance the identity sequence; do not reset it to remove gaps.

**Review checkpoint:** Step 4 is verified. Step 5 will turn the targeted smoke
checks into maintained unit/integration tests and cover the remaining failure
cases. No new dependency, database migration, historical generator, or continuous
simulation was introduced.

## CLI behavior

- `check` performs a read-only connection check, reports safe connection facts,
  and fails if `public.articles` is unavailable. It does not create tables.
- `insert` defaults to `--count 1` and `--author-id 1`. Both arguments must be
  positive integers; reject invalid arguments before connecting.
- Produce simple labeled demonstration titles and content. Each invocation
  appends new rows; repeated runs may reuse text but receive different IDs.
- Use one timezone-aware UTC instant for each generated article's creation,
  publication, and update timestamps. Leave deletion null and omit the generated
  ID. Historical timestamp distribution is a later milestone.
- Use bound SQL parameters. Insert a small run in one transaction, retrieve IDs
  with `RETURNING`, and print the committed count and IDs only after success.
- Roll back the entire run if any insertion fails. Do not retry automatically.
  Failed/rolled-back insertions can consume IDs; verify counts by returned IDs
  or before/after differences, not by assuming consecutive values.
- Exit `0` on success, `2` for CLI usage errors, and `1` for configuration,
  connection, schema-readiness, or database-operation failures. Log concise
  errors to stderr without credentials, a full DSN, or a raw exception dump.

Psycopg connection context management can commit on successful exit and roll
back on an exception. Keep the exception outside the transaction context until
rollback has occurred. See [Psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).

## Configuration and execution flow

Load the repository-root `.env` explicitly, preserving process environment
overrides. All five Python connection settings are required; the script has no
fallback host, port, database name, or username. Local example values live in
`.env.example`, not in the Python source:

| Variable | Requirement and example |
| --- | --- |
| `POSTGRES_HOST` | Required; local example `127.0.0.1`. |
| `POSTGRES_PORT` | Required integer between 1 and 65535; local example `5432`. |
| `POSTGRES_DB` | Required; local example `article_source`. |
| `POSTGRES_USER` | Required; local example `article_dev`. |
| `POSTGRES_PASSWORD` | Required; reject an empty value or the example placeholder. |

An absent or blank variable produces a configuration error before connecting.
The local `.env` was extended with its previously missing `POSTGRES_HOST` entry
from `.env.example`; its existing values and credentials were preserved.
The host process uses the published port, while container-to-container clients
use the Compose service name. Keep those connection contexts clear.

The configuration follow-up checked all five variables as absent, empty, and
whitespace-only: all 15 cases were rejected. Explicit values, process-variable
precedence, and password whitespace were preserved. The real read-only check
still succeeded using the completed local `.env`.

The readability follow-up verified 22 validation/read-error cases, preserved
explicit values and password whitespace, and confirmed that configuration errors
return exit `1` before any connection attempt. The real read-only command also
continued to succeed. Dotenv permission/encoding failures produce a safe
`SettingsError` without exposing the underlying exception details.

Execution order: parse arguments, load/validate settings, open a connection with
a five-second connect timeout, run the selected command, finish the transaction,
close the connection, and report the result. Put execution behind a main entry
point so importing helpers for unit tests does not connect or write data.

`python-dotenv` supports reading `.env` without overriding an existing process
variable. See its [configuration documentation](https://bbc2.github.io/python-dotenv/).

## Verification and acceptance

### Step 5: maintained test commands

Run the following from the repository root. Unit tests do not require PostgreSQL:

```powershell
uv run --locked python -m unittest discover -s tests/unit -v
```

The separately invoked database suite requires the local service and schema:

```powershell
uv run --locked python scripts/generate_articles.py check
uv run --locked python -m unittest discover -s tests/integration -v
```

Agent verification additionally passed `--cache-dir .cache/uv` to keep cache
access inside the workspace. Database tests ran outside the agent sandbox to
allow local socket access. The earlier interpreter-cache limitation recorded
during docstring work did not recur with that cache selection; the current
application source also passed Python AST parsing.

Tests use standard-library `unittest`; no new test dependency was added.
The explicit discovery directories keep unit checks and database operations
separate.

| Suite | Source | Verified result |
| --- | --- | --- |
| Unit | [test_generate_articles.py](../tests/unit/test_generate_articles.py) | 15 tests passed in about 0.08 seconds. |
| PostgreSQL integration | [test_postgres.py](../tests/integration/test_postgres.py) | 6 tests passed in about 5.71 seconds; zero skips. |

Unit coverage includes required environment values, dotenv precedence, port
boundaries, placeholder passwords, safe settings/read errors, invalid CLI
arguments, help without credentials, coherent UTC timestamps, safe connection
errors, missing-table reporting, suppressed success output on commit failure,
and import safety. Table-driven subtests exercise multiple invalid inputs within
these 15 test methods.

Integration coverage uses real PostgreSQL connections and the actual SQL helpers:

- Read-only connection facts and successful CLI check output.
- A committed two-article CLI run, inspected from a separate connection, with
  generated IDs, quotes/percent signs in content, and timestamp round-trips.
- Successful insertion followed by the caller's explicit rollback, proving the
  helper does not commit on its own.
- A valid first article followed by an invalid author, proving full rollback.
- A real unreachable-port failure with safe logs and bounded connection time.
- Missing-table reporting against the built-in `postgres` maintenance database,
  without removing or creating tables.

The commit test labels generated articles through the factory boundary; the
driver, insertion helper, transaction, and database constraints remain real.
Unit mocks are limited to configuration and CLI/error boundaries where external
effects are intentionally excluded.

### Fixture ownership and retained data

Run database checks against the local development setup without another writer
changing it during verification. Each test captures the existing row fingerprints
and assigns fixture titles a unique UUID marker. Cleanup deletes only the exact
titles registered for that test, then compares the database with its original
snapshot. It does not truncate tables, reset identities, delete volumes, or
remove prior articles. Assertions check rollback before cleanup so cleanup cannot
hide a partial-commit defect.

The missing-table test assumes the normal local development user can connect to
the built-in `postgres` database. If that database already contains an articles
table, the test explicitly skips rather than removing someone else's table.
Other setup failures fail with an actionable database-readiness message.

Preflight found 13 articles, reflecting additional rows since the earlier
eight-row checkpoint. The independently captured pre/post snapshot was identical:
`13:b7f6c71af709ffc086be6baf6a4bdbaf`. No fixture rows remain. Inserting, rolling
back, and deleting fixtures can advance the identity sequence; gaps are normal.

**Review checkpoint:** milestone 2's implemented behavior and tests have been
reviewed. The next milestone will plan historical timestamps, realistic dummy
text, reproducibility, and efficient batching; those features are not implemented
in this step.

### Acceptance checklist

- Step 2: verify imports and the lockfile without replacing the existing
  environment or upgrading unrelated packages.
- Step 3: run `check`; compare database/user/timezone with SQL and confirm the
  row count is unchanged. Check an unreachable local port using a temporary
  environment override, then restore it; the command must fail promptly.
- Step 4: insert one article, then five. Verify returned IDs exist, counts grow
  by the requested amounts, timestamps satisfy the schema, and deletion is null.
  Compare existing practice rows before/after to confirm they are unchanged.
- Step 5 unit checks: reject invalid count/author/port values, detect missing
  password, preserve process-variable precedence, and generate coherent UTC
  timestamps. Use `unittest` without another test dependency.
- Step 5 integration checks: exercise real PostgreSQL commit and rollback.
  Drive the insertion helper with a valid article followed by an invalid article
  and confirm neither is committed; do not add a public failure-injection flag.
  Verify missing table or connection failures produce a safe nonzero result.
- Record actual commands, retained row IDs, and outcomes in the progress log.
  Keep all prior article data and volumes intact. Tests use their own labeled
  rows or rolled-back transactions rather than broad deletes or table resets.

The milestone is complete when the documented Python commands are repeatable,
the returned rows are verified, targeted tests pass, and errors leave no partial
run committed. It is intentionally for a few records: Faker, seeds, historical
bulk loading, COPY, update/delete simulation, continuous loops, replication,
and downstream services remain later milestones.
