# Milestone 2: Basic Python Inserts

## Current checkpoint

**Step 2: dependencies locked with uv and imports verified; review pending.**
The dependency manifest and lockfile now exist. The existing environment's
packages were preserved. No application script has been created and no article
data was changed. Step 3 will implement the read-only connection command.

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
verified the binary driver and dotenv imports through uv. Connecting to
PostgreSQL from Python remains a Step 3 check.

## Ordered learning steps

| Step | Work | Completion evidence |
| --- | --- | --- |
| 1. Design the CLI | Record behavior, dependencies, configuration, and checks in this guide. | Reviewable plan; no Python implementation. |
| 2. Declare dependencies | Add `pyproject.toml` and `uv.lock`; verify the existing environment. | Lockfile validates; driver and dotenv import successfully. |
| 3. Check the connection | Add the `check` subcommand in `scripts/generate_articles.py`. | Python reports the database, user, version, UTC session timezone, and table availability without changing rows. |
| 4. Insert a few articles | Add the `insert` subcommand in that same script. | A small run returns generated IDs after committing; SQL confirms exactly those new rows. |
| 5. Verify and explain | Add targeted tests and record success/failure cases. | Argument, configuration, timestamp, transaction, and integration checks pass; existing rows are unchanged. |

Complete and review each step separately. Steps 1 and 2 are complete; Step 3 is
next.

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

**Review checkpoint:** dependency management and imports are verified. The
connection-check script and Python SQL execution remain Step 3.

## CLI behavior

The following are planned commands, not commands executed in this checkpoint:

```powershell
uv run --locked python scripts/generate_articles.py check
uv run --locked python scripts/generate_articles.py insert --count 5 --author-id 1
```

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
overrides. Existing Compose settings remain usable:

| Variable | Default or requirement |
| --- | --- |
| `POSTGRES_HOST` | `127.0.0.1`; documented in `.env.example` for host-side Python. |
| `POSTGRES_PORT` | `5432`; validate as an integer between 1 and 65535. |
| `POSTGRES_DB` | `article_source` |
| `POSTGRES_USER` | `article_dev` |
| `POSTGRES_PASSWORD` | Required; reject an empty value or the example placeholder. |

The existing local `.env` need not be rewritten: an omitted host uses localhost.
The host process uses the published port, while container-to-container clients
use the Compose service name. Keep those connection contexts clear.

Execution order: parse arguments, load/validate settings, open a connection with
a five-second connect timeout, run the selected command, finish the transaction,
close the connection, and report the result. Put execution behind a main entry
point so importing helpers for unit tests does not connect or write data.

`python-dotenv` supports reading `.env` without overriding an existing process
variable. See its [configuration documentation](https://bbc2.github.io/python-dotenv/).

## Verification and acceptance

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
