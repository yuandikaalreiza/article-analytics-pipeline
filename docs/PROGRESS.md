# Progress Log

## Current state

- **Milestone:** 5 - Pipeline integrations.
- **Checkpoint:** ClickHouse installation reviewed and verified; saving the
  configuration and documentation before starting minimal Airbyte setup.
- **Next step:** Set up Airbyte for the initial PostgreSQL-to-ClickHouse transfer.
  Further simulation, CDC, and Airflow remain deferred.
- **Database implementation:** PostgreSQL remains healthy with all 2,518 articles
  unchanged. ClickHouse has the empty `article_analytics` database.

Read [the roadmap](ROADMAP.md) for the sequence, [the PostgreSQL guide](01-postgresql.md)
for completed database work, [the Python insertion guide](02-python-inserts.md)
for milestone 2, [the October generation guide](03-historical-generation.md)
for milestone 3, and [the ongoing simulation guide](04-ongoing-simulation.md)
for the deferred simulation work. The [ClickHouse guide](05-clickhouse.md)
records installation settings and connection commands.

## Checklist

- [x] Inspect the repository and identify existing files and changes.
- [x] Agree on English documentation and one-step-at-a-time pacing.
- [x] Create the roadmap, PostgreSQL guide, and progress log.
- [x] Review the Step 1 documentation with the learner.
- [x] Step 2: create and validate local PostgreSQL configuration.
- [x] Add repository agent guidance before starting PostgreSQL.
- [x] Step 3: start PostgreSQL and verify a SQL connection.
- [x] Step 4: create and inspect `public.articles`.
- [x] Step 5: verify operations, constraints, rollback, repeatability, and persistence.
- [x] Review the completed database milestone before designing basic Python inserts.
- [x] Milestone 2 Step 1: document the basic Python CLI design.
- [x] Milestone 2 Step 2: declare dependencies, lock them, and verify imports.
- [x] Milestone 2 Step 3: implement and verify the read-only connection command.
- [x] Milestone 2 Step 4: implement and verify small article insertions.
- [x] Milestone 2 Step 5: verify argument, configuration, and transaction behavior.
- [x] Review milestone 2 before planning historical generation.
- [x] Milestone 3 Step 1: revise the plan to start in October 2026.
- [x] Review the revised October generation plan; learner requested direct ingestion.
- [x] Milestone 3 Step 2: implement reproducible generation and preview.
- [x] Milestone 3 Step 3: implement transactional loading and verify with fixtures.
- [x] Milestone 3 Step 4: load and inspect the 2,500-row October dataset.
- [x] Review the completed October dataset.
- [x] Milestone 4 Step 1: insert and verify five current articles.
- [ ] Review the current article insert exercise.
- [ ] Milestone 4 Step 2: implement and verify one-time updates.
- [ ] Milestone 4 Step 3: implement and verify soft deletion.
- [ ] Milestone 4 Step 4: implement and verify hard deletion.
- [ ] Milestone 4 Step 5: introduce configurable repeated simulation.
- [x] Install ClickHouse through Docker Compose and verify authenticated SQL.
- [ ] Set up the initial PostgreSQL-to-ClickHouse transfer with Airbyte.

## 2026-10-24 - Step 1: create tracking documentation

### Purpose

Make the learning sequence visible and record what has actually been completed
before introducing Docker configuration or SQL.

### Changes

- Created `ROADMAP.md`: milestones, dependencies, and review checkpoints.
- Created `01-postgresql.md`: database design, upcoming steps, verification
  expectations, and troubleshooting notes.
- Created `PROGRESS.md`: current checkpoint, checklist, and chronological log.

### Repository findings

- No application source, Docker configuration, or schema script was present.
- Git showed the original root `README.md`, `.gitignore`, and `.gitattributes`
  as deleted. Documentation creation leaves those deletions untouched.
- Existing `.venv` and `.cache` directories are left untouched.
- Docker CLI was available during planning, but its engine could not be accessed
  from that session. Engine access must be verified during Step 2; this does not
  establish that Docker itself is unavailable.

### Verification evidence

- All three documentation files exist and their local Markdown links resolve.
- Git status still shows the three pre-existing deletions and the existing
  untracked `.cache` directory; the only new project files are these documents.
- No Compose configuration, environment file, SQL file, or Python code was
  created. No container was started and no database checks were run.

### Learning notes

- Creating the PostgreSQL database and creating its table are separate steps.
- Data persistence depends on retaining the volume, not retaining the container.
- Planned acceptance checks are not proof that an implementation works; their
  observed results will be logged when each check runs.

### Next action and checkpoint

Review these documents. Then proceed to Step 2 only: add Compose configuration,
environment files, and minimal ignore rules; validate them and verify Docker
engine access. Starting PostgreSQL remains Step 3.

## 2026-10-24 - Step 1 commit and Step 2 configuration

### Purpose

Save the reviewed documentation using a Conventional Commit, then describe how
PostgreSQL will run locally before starting it.

### Commit

- `ebe8542` - `docs: add PostgreSQL learning roadmap and progress tracking`.
- Contains only the three Step 1 Markdown files. The pre-existing root file
  deletions were not included.
- Step 2 changes remain uncommitted for review.

### Changes

- Added `compose.yaml` with one PostgreSQL 18 service, localhost-only access,
  configurable host port, UTC, a named volume, and a readiness check.
- Added `.env.example` with documented settings and a password placeholder.
- Created an ignored local `.env` using a generated password, without printing
  its value.
- Reintroduced a minimal `.gitignore` as planned for Step 2. Local environment,
  Python environment, cache, and build output files are ignored.
- Updated the guide with configuration explanations and verified commands.
- Left the root `README.md` and `.gitattributes` deletions untouched. Existing
  `.venv` and `.cache` contents are unchanged.

### Verification evidence

- Docker Compose reports `v5.5.1`.
- Docker client and server both report `29.8.2`. The initial sandboxed engine
  check failed with a permission error; the read-only check outside the sandbox
  succeeded. No Docker configuration changes were necessary.
- `docker compose config --quiet` succeeded.
- In-memory inspection of the resolved configuration confirmed exactly one
  service, `postgres:18`, the intended database and user, a nonempty password
  different from the example placeholder, `127.0.0.1:5432:5432`, a named volume
  at `/var/lib/postgresql`, UTC, and the readiness check. No credentials were
  printed.
- Git ignore checks confirmed `.env`, `.venv`, and `.cache` are ignored while
  `.env.example` remains trackable.
- No TCP listener on host port `5432` was observed during the check. This does
  not guarantee that a later startup can bind the port.
- `docker compose ps --all --format json` returned no containers for this project.
- No image was pulled, no container was started, and no schema was created.

### Learning notes

- Compose configuration validation does not start the service or prove runtime
  health. A SQL connection is still required in Step 3.
- `.env` supplies Compose substitutions; only settings declared under
  `environment` are passed into PostgreSQL's container.
- The password is required, while the database name, username, and host port
  have development defaults.
- The named volume declaration will take effect when the service starts.

### Next action and checkpoint

Review Step 2. Then proceed to Step 3 only: start PostgreSQL, wait for health,
connect with `psql`, and verify database name, user, version, and session timezone.
Creating the articles table remains Step 4.

## 2026-10-24 - Preparation checkpoint: repository agent guidance

### Purpose

Preserve the agreed learning workflow for future sessions before proceeding to
database startup. This is a documentation checkpoint, not a database step.

### Changes

- Added root `AGENTS.md` with pointers to the progress log, roadmap, and
  PostgreSQL guide.
- Recorded the one-step-per-turn workflow, explanations, appropriate checks,
  documentation updates, and review checkpoints.
- Included local development constraints, credential and volume handling, and
  Conventional Commit guidance.
- Replaced the roadmap's duplicated working instructions with a link to
  `AGENTS.md`. Milestone boundaries remain in the roadmap.

### Verification evidence

- Checked that the root instructions and all local Markdown links in the
  affected documents resolve to existing files.
- Reviewed the guidance against the agreed workflow and kept changing database
  settings and current progress in their existing sources.
- No runtime configuration, credentials, or database state changed. No database
  startup or integration checks were performed for this documentation change.

### Learning notes

`AGENTS.md` holds durable instructions for how an agent works in this repository.
The roadmap holds the plan; the guide explains implementation; the progress log
records observed results. Read the progress log to resume rather than storing
the current step in multiple instruction files.

### Next action and checkpoint

Review the agent guidance, then proceed to Step 3 only: start PostgreSQL and
inspect the database. Creating the table remains Step 4. These documentation
changes remain uncommitted for review.

## 2026-10-24 - Reviewed configuration commit and Step 3 startup

### Purpose

Commit the reviewed configuration and agent guidance, then start PostgreSQL and
verify the source database before adding tables.

### Commit

- `2c3ee1c` - `feat: configure local PostgreSQL and document agent workflow`.
- Includes the configuration, agent guidance, and related documentation from
  the preceding checkpoints. The local `.env` and pre-existing root `README.md`
  and `.gitattributes` deletions were excluded.
- The subsequent Step 3 volume correction and documentation remain uncommitted
  for review.

### Changes and startup diagnosis

- Downloaded the official `postgres:18` image and attempted startup with health
  waiting enabled.
- The original named volume already contained PostgreSQL 17 data. The first
  startup failed with an existing-data layout error and an unhealthy container.
- Stopped the failed restart loop, inspected mount metadata and image defaults,
  and read version markers using a temporary container with a read-only volume
  mount. The original root `PG_VERSION` was `17`; the PostgreSQL 18 image default
  was `/var/lib/postgresql/18/docker`.
- Verified that `article-analytics-pipeline_postgres18_data` did not exist, then
  changed Compose's volume declaration from `postgres_data` to `postgres18_data`.
- Repeated the same startup command successfully with the new volume. The old
  volume remains intact. No data was deleted or migrated.
- Updated the guide with verified startup and inspection commands and the
  reason for the storage correction.

### Verification evidence

- `docker compose config --quiet` succeeded after the volume correction.
- `docker compose up --detach --wait --wait-timeout 60 postgres` succeeded and
  reported the container healthy.
- Status inspection reported `running / healthy / restarts=0` and the published
  port `127.0.0.1:5432->5432/tcp`.
- The included `psql` client connected over the Compose network to service
  `postgres`, with the configured password supplied inside the container.
- Read-only SQL returned database `article_source`, user `article_dev`, version
  `18.6 (Debian 18.6-1.pgdg13+2)`, timezone `UTC`, and data directory
  `/var/lib/postgresql/18/docker`.
- The `public` schema contained `0` base tables. No articles table or schema
  script was created.
- Mount inspection confirmed the active volume is
  `article-analytics-pipeline_postgres18_data` at `/var/lib/postgresql`.
- Volume inspection confirmed both the old PostgreSQL 17 volume and the new
  PostgreSQL 18 volume exist.
- The first host socket probe was blocked by sandbox permissions. Repeating it
  outside the sandbox successfully connected to `127.0.0.1:5432`. Docker Desktop
  and firewall settings were unchanged.

### Learning notes

- A named volume can outlive repository files and containers. Starting a new
  configuration does not guarantee that a familiar volume name is empty.
- A PostgreSQL major-version change requires a supported upgrade procedure or
  separate fresh storage. Reusing PostgreSQL 17 files directly with PostgreSQL 18
  is insufficient.
- Database initialization and table creation are separate operations. The
  image has created the source database; the articles table is still pending.
- Health, successful SQL, and host port reachability are distinct checks.
  Persistence across container recreation has not yet been tested.

### Next action and checkpoint

PostgreSQL remains running for inspection. Review Step 3, then proceed to Step 4
only: create `sql/001_articles.sql`, execute it explicitly, and inspect all eight
columns and the agreed constraints. Data-operation and persistence checks remain
Step 5.

## 2026-10-24 - Step 4: create and inspect the articles table

### Purpose

Create the source table and understand its stored definition before adding
practice data.

### Changes

- Added `sql/001_articles.sql` with transactional conditional table creation,
  eight columns, a generated identity primary key, timestamp defaults, and four
  named author/lifecycle checks.
- Executed the file explicitly through the container's included `psql` client
  with stop-on-error behavior. No automatic startup script was introduced.
- Updated the PostgreSQL guide with the creation command, schema explanations,
  inspection commands, and actual results.
- Left the existing runtime configuration and database volumes unchanged.

### Verification evidence

- The preflight service status was healthy. A read-only lookup returned null
  for `public.articles`, confirming there was no existing table to replace.
- Schema execution exited successfully and reported `BEGIN`, `CREATE TABLE`,
  and `COMMIT`.
- `psql` table inspection and `information_schema.columns` showed exactly eight
  columns with the agreed types and order. Seven are required; `deleted_at` is
  nullable.
- `id` is a `BIGINT` identity with generation mode `ALWAYS` and a primary key.
- `created_at` and `updated_at` default to `CURRENT_TIMESTAMP`. Publication has
  no default; deletion is nullable with no explicit default.
- Table inspection confirmed the checks for positive `author_id`, creation
  before or at publication, update at or after publication, and optional deletion
  between publication and update.
- Index inspection showed exactly one index: `articles_pkey`, a unique B-tree
  on `id`. There are zero user triggers.
- The table contains zero rows. No insert, update, delete, constraint-failure,
  repeatability, rollback, or container-recreation checks were performed yet.

### Learning notes

- Identity generation provides IDs; the primary key enforces their uniqueness.
- Defaults fill omitted values at insertion time. A default on `updated_at`
  does not automatically maintain it on later updates.
- Metadata inspection verifies the installed structure. Exercising valid and
  invalid data is a separate check for Step 5.
- Conditional creation preserves an existing table but does not validate or
  migrate a different schema; inspect an existing definition before rerunning.

### Next action and checkpoint

Review the schema and its explanations, then proceed to Step 5. Use a few
clearly identified practice rows to verify operations, invalid values,
transaction rollback, repeatability with retained data, and persistence through
container recreation with the PostgreSQL 18 volume retained. The table remains
empty and these changes remain uncommitted for review.

## 2026-10-24 - Schema commit and Step 5 verification

### Purpose

Save the reviewed schema and storage correction, then prove article operations,
constraint enforcement, rollback, repeatability, and persistence with a small
practice dataset.

### Commit

- `345f1c5` - `feat: add articles schema and isolate PostgreSQL 18 storage`.
- Contains the pending Step 3 storage correction, Step 4 table script, and
  related documentation. The local `.env` and pre-existing root file deletions
  were excluded.
- Step 5 practice SQL and documentation remain uncommitted for review.

### Changes

- Added `sql/002_practice_articles.sql` as an explicit manual exercise separate
  from initialization. It captures generated IDs, exercises operations and
  rollback, and prints boolean results for inspection.
- Used three committed practice insertions to exercise update, soft deletion,
  and hard deletion. Two labeled rows remain for the learner to inspect.
- Tested nine invalid statements through separate client invocations.
- Repeated conditional schema creation twice with retained data, then recreated
  only the PostgreSQL container with its existing named volume.
- Updated the guide with verified commands, results, and explanations.

### Verification evidence

- Preflight confirmed a healthy service, zero article rows, and no pre-existing
  `[practice step 5]` rows.
- All eight positive-operation and rollback boolean assertions were true:
  update preserved ID and creation time while advancing update time; soft delete
  retained the row; hard delete removed its own row; rollback undid an insert,
  update, and delete.
- Missing title/publication inputs returned SQLSTATE `23502`. Zero/negative
  authors, creation after publication, update before publication, deletion before
  publication or after update, and an invalid existing-row update returned
  `23514` with the expected named constraints. All nine clients exited with
  expected SQL-error code `3`.
- Every committed article value was unchanged after the rejected statements.
- Two schema reruns succeeded. Table OID `16390`, row count `2`, and row
  fingerprint `b5934dc43e2939ed872b4247a703c561` were unchanged.
- Container recreation changed the container ID from `042fc44a5a74...` to
  `2993f15413dd...`; the new container was healthy.
- After recreation, the same table OID, row count, and full-row fingerprint were
  retained. Mount inspection confirmed use of
  `article-analytics-pipeline_postgres18_data`.
- The old PostgreSQL 17 volume was untouched. No volume deletion or data reset
  was performed.
- The fresh PostgreSQL 18 initialization, schema application, and operation
  sequence were verified across Steps 3 through 5. A second isolated clone was
  not separately bootstrapped.

### Retained data

| ID | Title | State |
| --- | --- | --- |
| 1 | `[practice step 5] Persistence article` | Active; historical creation/publication, updated content. |
| 2 | `[practice step 5] Soft-deleted article` | Retained with deletion and update timestamps set together. |

The hard-deleted and rolled-back insert rows are absent. Failed and rolled-back
inserts can leave sequence gaps; no identity reset was performed.

### Learning notes

- Soft deletion is an update that retains a row; hard deletion removes it.
- Transactions can undo multiple kinds of row changes together.
- Expected constraint errors are successful negative checks when their SQLSTATE
  and constraint match the intended case.
- Schema reruns preserve the existing table; retained volume storage preserves
  data across container replacement. These are separate properties.
- A new checkout does not imply an empty database when the same named Docker
  volume already exists.

### Next action and checkpoint

Review the completed PostgreSQL milestone and inspect the retained practice
rows. After review, design milestone 2's small Python insertion CLI. Python
implementation, replication, and downstream pipeline services remain deferred.

## 2026-10-24 - Database milestone commit and Python design checkpoint

### Purpose

Save the reviewed database verification work and define the smallest Python
learning milestone before introducing application code.

### Commit

- `21d8685` - `test: verify article operations and PostgreSQL persistence`.
- Contains the Step 5 practice SQL and related database documentation. Existing
  root `README.md` and `.gitattributes` deletions were excluded, as were local
  credentials and caches.
- The new Python planning document and tracking updates remain uncommitted for
  review.

### Changes

- Added `docs/02-python-inserts.md` with the dependency plan, one-script CLI,
  configuration, transaction behavior, and verification sequence.
- Split the milestone into five reviewable steps: design, dependencies,
  connection check, inserts, then targeted validation.
- Updated the roadmap and current checklist to identify milestone 2 as active.

### Verification evidence

- Read-only handoff checks confirmed a healthy PostgreSQL container and two
  articles: one active and one soft-deleted. No article rows were changed.
- The existing `.venv` interpreter reports Python `3.13.16`; uv reports
  `0.13.1`.
- Installed package metadata reports `psycopg` and `psycopg-binary` at `3.3.6`,
  and `python-dotenv` at `1.2.4`. Driver imports and Python-to-database
  connectivity have not been tested yet.
- No Python source, dependency manifest, or lockfile was created. No packages
  were installed, removed, or upgraded. Existing environment and cache contents
  were preserved.

### Learning notes

- The generator will run on the host, so it connects to the published localhost
  port; the previous container-side client used the Compose service name.
- Recording dependencies makes a fresh setup reproducible even when packages
  already happen to be present in this local environment.
- A connection check and an insertion command are separate learning steps.
- Small inserts should use one transaction per run so a failure cannot commit
  only part of the requested articles.

### Next action and checkpoint

Review the Python guide. Then perform milestone 2 Step 2 only: add
`pyproject.toml` and `uv.lock`, document the optional host setting in
`.env.example`, and verify imports while retaining unrelated environment
packages. Writing the connection command remains Step 3; inserts remain Step 4.

## 2026-10-24 - Milestone 2 Step 2: uv dependency setup

### Purpose

Apply the user's choice of uv, declare reproducible Python dependencies, and
verify imports while preserving the existing environment.

### Changes

- Added `pyproject.toml` with Python `>=3.13`, `psycopg[binary]==3.3.6`, and
  `python-dotenv==1.2.4`. The script project has no build backend or installable
  application package yet.
- Generated `uv.lock` with uv `0.13.1` using the existing `.venv` interpreter.
- Added the host-side `POSTGRES_HOST` setting to `.env.example`; left the actual
  `.env` and credentials unchanged.
- Recorded uv as the Python dependency/execution convention in `AGENTS.md` and
  changed the planned application commands to `uv run --locked`.
- Updated the Python guide and roadmap with verified setup results.

### Verification evidence

- Captured the installed package inventory before syncing: 14 packages.
- The sandboxed PyPI lookup failed with a DNS error. Repeating lock generation
  outside the sandbox succeeded and resolved five entries including the project.
- `uv sync --locked --inexact` checked four external packages without installing,
  removing, or upgrading any package. A before/after comparison confirmed all
  14 pre-existing package names and versions were retained.
- `uv lock --check --offline` passed with the selected interpreter and project
  cache.
- Imports through `uv run --locked` succeeded on Python `3.13.16`:
  `psycopg` version `3.3.6`, driver implementation `binary`, and `python-dotenv`
  version `1.2.4`.
- No database command was executed and no application script was created.
  Python-to-PostgreSQL connectivity remains unverified until Step 3.

### Learning notes

- `pyproject.toml` declares the project's requirements; `uv.lock` records the
  resolved dependency set for repeatable setup.
- `--locked` requires consistency with the lockfile. `--inexact` preserves
  unrelated packages when syncing the existing environment.
- A successful import proves that dependencies load, not that the database
  connection or application behavior works.

### Next action and checkpoint

Review this dependency setup, then implement Step 3 only: add the `check`
subcommand in `scripts/generate_articles.py` and verify a read-only connection
using `uv run --locked`. Article insertion remains Step 4. Changes remain
uncommitted for review.

## 2026-10-24 - uv setup commit and milestone 2 Step 3

### Purpose

Save the reviewed uv setup and Python plan, then verify the first application
command's database connection without changing article data.

### Commit

- `5262ac5` - `build: manage Python dependencies with uv`.
- Includes dependency tracking, the Python milestone plan, uv agent guidance,
  and related documentation. Local credentials and pre-existing root file
  deletions were excluded.
- Step 3 source and documentation remain uncommitted for review.

### Changes

- Added `scripts/generate_articles.py` with a required `check` subcommand.
- Added explicit repository-root dotenv loading, process-variable precedence,
  configuration validation, and a five-second connection timeout.
- Opened the check transaction as read-only and queried connection facts plus
  article-table availability. The command does not initialize or change schema.
- Added concise error reporting without raw database exceptions, connection
  strings, or passwords. Success is reported after the connection closes.
- Updated the Python guide with usage, execution flow, and actual outcomes.

### Verification evidence

- Preflight Docker status was healthy. The source table snapshot was
  `2:b5934dc43e2939ed872b4247a703c561`.
- The sandboxed Python connection could not reach the local port. Repeating the
  same command outside the sandbox succeeded without environment-wide changes.
- `uv run --locked ... check` exited `0` and reported database `article_source`,
  user `article_dev`, PostgreSQL `18.6`, timezone `UTC`, read-only transaction
  `on`, and available `public.articles`.
- Running from the `scripts` directory also succeeded, verifying that root
  dotenv loading is independent of the invocation directory.
- Help exited `0`; omitting the required subcommand exited `2`.
- An unused local port produced exit `1` and a safe connection error in about
  `5.63` seconds. Missing table, invalid port, placeholder password, and wrong
  password cases also returned the expected safe exit `1`.
- The wrong-password output contained neither its supplied test password nor
  a traceback or connection string.
- The first combined failure check hit a verification-script issue: a .NET
  restoration call left an empty port variable. Corrected restoration by removing
  previously absent variables from `Env:` and reran all five failure checks
  successfully. No application fix was required for this test-procedure issue.
- Import checks confirmed no settings load or connection on module import.
- The post-test SQL snapshot exactly matched the baseline: two rows with all
  values unchanged. No database objects were added or removed, and `.env` was
  not rewritten.

### Learning notes

- Dependency imports and successful authenticated database connections are
  different checks.
- `connection.read_only = True` makes PostgreSQL enforce a read-only transaction;
  the query reports that setting as evidence.
- Process overrides support controlled failure checks without editing local
  credentials. An absent variable and an explicitly empty one can behave
  differently, so temporary overrides must be restored carefully.
- The command's main-entry guard allows helpers to be imported for later tests
  without opening database connections.

### Next action and checkpoint

Review Step 3, then implement Step 4 only: add the `insert` subcommand, generate
a few simple articles with coherent UTC timestamps, insert one run in a single
transaction, and verify returned IDs and unchanged prior data. Formal unit and
transaction-failure integration checks remain Step 5.

## 2026-10-24 - Step 3 follow-up: require environment connection settings

### Purpose

Apply the user's request to keep connection values in environment configuration
instead of hardcoding fallback values in Python.

### Changes

- Removed host, database, username, and port fallback values from the script.
  All five connection settings must now be supplied by `.env` or process
  variables; missing or blank settings produce an error before connecting.
- Added the previously missing `POSTGRES_HOST` entry to the ignored local
  `.env`, taking its value from `.env.example`. Appending the entry preserved
  all existing settings and credentials.
- Updated the Python guide to describe required configuration rather than
  runtime defaults. No Compose configuration or database objects changed.

### Verification evidence

- All 15 absent, empty, and whitespace-only cases across the five required
  variables raised the expected configuration error.
- Custom connection values were retained, process overrides took precedence
  over dotenv values, and password whitespace was preserved.
- The real `uv run --locked ... check` command still succeeded with UTC,
  read-only mode `on`, and `public.articles` available.
- No article writes were performed. Local `.env` remains ignored by Git.

### Next action and checkpoint

Review the configuration correction. The next learning step remains milestone 2
Step 4: add small article insertions. Changes remain uncommitted.

## 2026-10-24 - Step 3 follow-up: readable settings error handling

### Purpose

Make settings loading and its try/except flow easier to read while retaining
required environment configuration.

### Changes

- Added `get_required_env()` to share the missing/blank validation.
- Replaced the mapping loop with explicit reads for host, database, user, port,
  and password, followed by a clear return dictionary.
- Kept exception handling close to dotenv loading and port conversion. Both
  produce `SettingsError`, handled once by `main()`.
- Preserved required connection values, process overrides, port validation,
  password whitespace, and safe error messages. Added safe handling for dotenv
  encoding failures alongside file-access errors.

### Verification evidence

- All 22 missing/blank, invalid-port, dotenv-read, and placeholder-password
  cases raised the expected settings error.
- Explicit values and password whitespace were preserved; shell values still
  took precedence over dotenv configuration.
- A CLI configuration failure returned `1` without calling the database driver.
- The live `uv run --locked ... check` command succeeded with UTC, read-only
  mode `on`, and the articles table available. No database writes were performed.

### Next action and checkpoint

Review the readability change. Milestone 2 Step 4 remains next; no insertion
behavior was introduced and changes remain uncommitted.

## 2026-10-24 - Connection CLI commit and milestone 2 Step 4

### Purpose

Save the reviewed read-only CLI and settings cleanup, then insert a few articles
from Python using one transaction per invocation.

### Commit

- `d4911e8` - `feat: add read-only PostgreSQL connection CLI`.
- Includes the connection command, required environment configuration, readable
  settings errors, and related documentation. Local credentials and existing
  root file deletions were excluded.
- Step 4 changes remain uncommitted for review.

### Changes

- Added `insert` with positive `--count` and `--author-id` arguments, defaulting
  to one article and author `1`.
- Added small helpers for integer validation, demonstration article creation,
  and parameterized insertion with `RETURNING id`.
- Generated coherent timezone-aware UTC timestamps and null deletion times.
- Kept transaction ownership in `main()`'s connection context; the insertion
  helper does not commit per row. Results are printed after successful commit.
- Preserved environment-only connection settings and the read-only check command.
- Updated the guide with usage, execution flow, actual IDs, and verification.

### Verification evidence

- Preflight confirmed a healthy service and two existing articles. Captured a
  fingerprint of each original row before writes.
- The default insert invocation exited `0`, committing ID `13` with author `1`.
- `insert --count 5 --author-id 7` exited `0`, committing IDs `14` through `18`
  with author `7`.
- A separate SQL connection confirmed all six returned IDs exist. Creation,
  publication, and update timestamps match for each new row; deletion is null.
- Content containing an apostrophe was stored correctly through bound parameters.
- Total count grew from `2` to `8`. Both original row fingerprints were unchanged.
- Eight invalid count/author cases exited `2` before configuration loading or
  database connection.
- A transaction smoke check inserted a valid probe followed by an invalid
  author. PostgreSQL rejected the second insert and the first rolled back.
  The entire eight-row snapshot was unchanged afterward, with no retained probe.
- The read-only `check` command still succeeded with UTC, read-only mode `on`,
  and the article table available.

### Retained Python demonstration rows

| IDs | Count | Author | State |
| --- | --- | --- | --- |
| `13` | 1 | `1` | Active |
| `14`, `15`, `16`, `17`, `18` | 5 | `7` | Active |

The earlier rows `1` and `2` remain intact. Failed and rolled-back operations
can consume identity values; no sequence reset was performed.

### Learning notes

- Parameterized SQL sends article values separately from the SQL statement,
  correctly handling quoted text.
- `RETURNING` provides the actual generated IDs; successful exit from the
  connection context commits before those IDs are reported to the user.
- The insertion helper participates in its caller's transaction, making the
  entire invocation atomic and allowing a real rollback check.
- These are deliberately small demonstration inserts. Bulk performance and
  realistic historical distributions belong to later milestones.

### Next action and checkpoint

Review Step 4 and the retained rows, then perform Step 5: add maintained unit
and PostgreSQL integration tests for configuration, arguments, UTC timestamps,
commit/rollback, and safe errors. No additional pipeline services are needed.

## 2026-10-24 - Google-style Python docstrings

### Purpose

Set a consistent format for Python docstrings and begin applying it to the
active CLI source.

### Changes

- Added repository guidance to use Google-style Python docstrings, with
  `Args`, `Returns`, and `Raises` sections when they apply.
- Expanded the callable docstrings in `scripts/generate_articles.py` to explain
  inputs, results, errors, and transaction ownership.
- Preserved the current Milestone 2 Step 4 review checkpoint. Step 5 remains the
  next implementation step after that review.

### Verification evidence

- PowerShell content checks found `Args`, `Returns`, and `Raises` sections in the
  updated source; all documented `AGENTS.md` link targets exist.
- `git diff --check` passed.
- Python AST validation could not run: `uv` was unable to persist its interpreter
  cache in the sandbox, and the system `python.exe` Windows app shim could not
  start. No runtime or database checks were run.

### Next action and checkpoint

Review the docstring format, then continue with the existing Step 4 review.
After approval, proceed to Milestone 2 Step 5.

## 2026-10-24 - Milestone 2 Step 5: maintained test suites

### Purpose

Turn the CLI's manual checks into repeatable unit and PostgreSQL integration
tests while preserving the learner's existing dataset.

### Changes

- Added `tests/unit/test_generate_articles.py` for configuration, argument,
  timestamp, CLI output/error, and import behavior without PostgreSQL.
- Added `tests/integration/test_postgres.py` for real transactions, persistence
  after commit, read-only checks, and database failure behavior.
- Kept the suites explicitly invoked through separate discovery directories.
  Used standard-library unittest with no dependency changes.
- Used unique fixture titles and exact-title cleanup; compared each test's
  final dataset with its original row fingerprints.
- Followed the current Google-style docstring convention and left the existing
  application implementation and its docstrings intact.
- Updated the Python guide with maintained test commands and verified results.

### Verification evidence

- Preflight source parsing passed using uv and the project cache, resolving
  the previously recorded inability to validate the newer docstrings.
- PostgreSQL was healthy. The preflight dataset contained 13 articles rather
  than the 8 recorded at the earlier checkpoint; captured the actual current
  contents before running any fixture operations.
- `uv run --locked ... python -m unittest discover -s tests/unit -v` passed all
  15 unit tests. Subtests cover missing/blank settings, invalid counts/authors,
  invalid ports and boundaries, and safe dotenv read failures.
- `uv run --locked ... python -m unittest discover -s tests/integration -v`
  passed all 6 integration tests with zero skips in about 5.71 seconds.
- Real tests verified committed CLI inserts through another connection,
  quoted-text/timestamp round-trips, caller-owned rollback, failed-second-row
  rollback, enforced read-only mode, unreachable connection handling, and
  missing-table reporting without schema changes.
- Fixture cleanup preserved all original rows. An independent SQL comparison
  matched the complete pre/post snapshot:
  `13:b7f6c71af709ffc086be6baf6a4bdbaf`.
- No table truncation, identity reset, volume deletion, application-code change,
  or dependency addition was performed. Test inserts may consume identity values.

### Learning notes

- Unit tests isolate configuration and CLI boundaries; integration tests prove
  behavior against real PostgreSQL constraints and transactions.
- A committed insertion, an explicit caller rollback, and a failed batch are
  different transaction outcomes and each has its own maintained check.
- Fixture cleanup runs even when an assertion fails. Rollback is checked before
  cleanup so deleting a fixture cannot conceal a partial commit.
- Live state must be inspected rather than inferred from a historical row count.

### Next action and checkpoint

Review the completed basic Python insertion milestone and its tests. After
review, plan the next milestone for historical article data, configurable
counts/seeds, realistic text, and batch efficiency. Historical generation,
continuous simulation, and downstream services remain deferred. These test and
documentation changes remain uncommitted for review.

## 2026-10-25 - Resume and reverify Milestone 2 Step 5

### Purpose

Confirm the saved testing checkpoint after the session reset before advancing.

### Verification evidence

- PostgreSQL remained running and healthy; no service restart was required.
- `uv run --locked --cache-dir .cache/uv python -m unittest discover -s tests/unit -v`
  passed all 15 tests in 0.138 seconds.
- `uv run --locked --cache-dir .cache/uv python -m unittest discover -s tests/integration -v`
  passed all 6 tests in 5.824 seconds with zero skips. Local database access
  required execution outside the agent sandbox.
- Independent read-only SQL snapshots before and after the database suite both
  returned `13:b7f6c71af709ffc086be6baf6a4bdbaf`, matching the previous checkpoint.
  All 13 existing articles were preserved; test fixtures were removed.
- No application, dependency, configuration, or schema changes were needed.
  The pre-existing root file deletions remain untouched.

### Learning notes and next action

Saved progress identifies where to resume; fresh checks establish current
behavior. Step 5 is complete and its test/documentation changes remain
uncommitted for review. Review milestone 2 before planning historical generation.

## 2026-10-25 - Milestone 2 review and commit

The learner approved the completed tests and requested a Conventional Commit.
The commit includes the two test suites and their tracking documentation.
The pre-existing `README.md` and `.gitattributes` deletions are excluded.
The latest verification remains 15 unit tests and 6 integration tests passed,
with all 13 existing articles preserved. No further runtime changes were made.

Milestone 2 is reviewed and complete. The next learning step is to document
milestone 3's historical generation design: date range, reproducible seeds,
realistic article text, configurable counts, batching, and transaction behavior.
Implementation will follow review of that plan.

## 2026-10-25 - Milestone 3 Step 1: October scope revision

### Purpose and changes

The learner requested starting with October 2026 instead of generating from
2016. Created `03-historical-generation.md` and updated the roadmap to reflect
that scope. Milestone 2 was saved in `32d9534` with the Conventional Commit
`test: verify article CLI configuration and PostgreSQL transactions`.

The first dataset is planned as 2,500 new articles from October 1 to a fixed
cutoff covering the elapsed part of October 25. The cutoff cannot exceed the
run's start time. Daily counts may vary; 100 per calendar date is an average.
The expected total is the freshly checked baseline plus 2,500, or 2,513 if the
previously verified 13-row baseline is unchanged.

### Verification and learning notes

- Inspected the current script, schema, dependencies, roadmap, and checkpoint.
  The existing settings, insertion helper, and transaction ownership can be
  reused; no dependency or schema change is planned for this first dataset.
- Checked local Markdown links and documentation whitespace/content. This step
  changes documentation only; no runtime tests or database operations were run.
- Retained dated log entries and the earlier SQL exercises containing 2016
  timestamps as history. The active roadmap now starts in October 2026.
- A date range and a record count are separate inputs. A seed reproduces
  generated values for fixed inputs; it does not make repeated loads idempotent.
- The root `README.md` and `.gitattributes` deletions remain untouched.

### Next action and checkpoint

Review the revised plan. Step 2 will implement seeded generation and a preview
without database access. The actual 2,500-row insertion remains Step 4 after
the loader and its transaction behavior are verified. These documentation
changes remain uncommitted for review.

## 2026-10-25 - October generation, verification, and ingestion

### Authorization and changes

The learner requested starting ingestion directly, authorizing generation,
loader implementation, and the first dataset in one turn. Extended the existing
CLI with `historical`, explicit count/start/cutoff, seed, author, batch size, and
a database-free preview. Reused environment configuration and the insertion
helper; no schema, dependency, service, or volume changes were needed.

Added six unit checks for seeded values, timestamp boundaries, timezone parsing,
argument validation, preview isolation, and commit-failure output. Added three
integration checks for committed historical batches, failure in a later batch,
and value consistency across batch sizes with explicit rollback.

### Verification evidence

- PostgreSQL was running and healthy. Captured original fingerprints and a
  13-row baseline before tests. All tests restored the original dataset.
- Unit suite: 21 tests passed in 0.103 seconds.
- Integration suite: 9 tests passed in 6.506 seconds, zero skips. Database access
  required execution outside the agent sandbox.
- A full 2,500-record preview succeeded, showing three samples and 25 publication
  dates without database access.
- Loaded once using seed `20261001`, author `7`, batch size `500`, start
  `2026-10-01T00:00:00Z`, and exclusive cutoff `2026-10-25T02:26:52Z`.
  Five batches committed in one transaction; reported load time was 2.516 seconds.
- Independent post-load inspection found exactly 2,500 new rows and 2,513 total.
  Every original row fingerprint was unchanged. Regeneration matched all seven
  generated fields in all 2,500 new rows; all are active with coherent timestamps.
- Publication times range from `2026-10-01T00:46:48.600532+00:00` to
  `2026-10-25T01:49:36.006776+00:00`. October 25 has five rows because its
  selected interval covers only the first 2 hours and 26 minutes.
- Table plus index allocation grew from 65,536 bytes just before loading to
  1,990,656 bytes afterward, about 1.90 MiB. These are relation sizes, not the
  entire volume. Detailed daily counts and measurements are in the guide.
- Executed source: base commit `32d9534` plus uncommitted changes; script SHA-256
  `c1b9fedd5c977d927590c50675c93ed4b2db116b1b255db74158ba7b6231c341`.

### Lessons and checkpoint

Batches bound application memory; a single outer transaction controls atomicity.
The initial writer still uses one parameterized INSERT per row. Seeds reproduce
values but rerunning the load appends rows. Preview does not insert anything.
No automatically repeated load, reset, identity restart, or volume deletion ran.

Review the retained October articles. This work remains uncommitted; the root
`README.md` and `.gitattributes` deletions remain untouched. Choose the next step
after review; ongoing simulation and pipeline integrations remain deferred.

## 2026-10-25 - October milestone review and commit

### Purpose and review results

The learner authorized the proposed dataset review and Conventional Commit.
Reviewed the pending generator and test changes and performed a new read-only
inspection against the retained database.

- Confirmed 2,513 total rows: 2,500 historical articles and the 13 original rows.
- Compared every original row fingerprint and regenerated all seven fields of
  every historical article; all matched. Checked timestamp ordering, range
  bounds, null deletion, and coverage across 25 UTC publication dates.
- Complete dataset fingerprint:
  `2513:271e9314d55fcf85f605a4622802895e`.
- The script's SHA-256 still matched the version used during ingestion and the
  passing 21-unit/9-integration-test run. No application fixes or repeat test run
  were needed; this checkpoint used read-only database verification.
- Checked documentation links and whitespace, then inspected the staged diff.
  The commit includes only the generator, its two test suites, and three related
  documentation files. The existing root file deletions are excluded.

### Learning note and next action

Git stores the generator, tests, and recorded evidence. The 2,513 database rows
remain in the local Docker volume; a Git checkout alone does not restore them.
No additional rows, updates, deletions, or simulation loop ran during review.

Milestone 3 is complete. Plan the next milestone for ongoing operations, starting
with one-time current inserts, then updates, soft deletion, hard deletion, and
finally configurable continuous execution. Keep each implementation separately
observable and pause for the learner's review.

## 2026-10-25 - Milestone 4 Step 1: current article inserts

### Purpose and changes

The learner requested starting the next step after the October milestone was
committed as `21306af` (`feat: add seeded October article generation`). Reused
the existing current-time `insert` command for a small one-time exercise. Added
`04-ongoing-simulation.md` to explain the operation, command, results, and later
steps. Updated the roadmap and current checkpoint.

### Verification evidence

- Read-only preflight confirmed 2,513 rows and the reviewed fingerprint
  `2513:271e9314d55fcf85f605a4622802895e` before insertion.
- Ran `uv run --locked --cache-dir .cache/uv python scripts/generate_articles.py
  insert --count 5 --author-id 7` once. All five rows committed; returned IDs were
  `2556, 2557, 2558, 2559, 2560`.
- A separate read-only connection found 2,518 rows, with exactly those five IDs
  added and every previous row fingerprint unchanged.
- Verified title/content values, author 7, null deletion, and equal creation,
  publication, and update instants within the execution window. New timestamps
  span `2026-10-25T02:39:24.900622+00:00` through
  `2026-10-25T02:39:24.908135+00:00`.
- Resulting dataset fingerprint:
  `2518:e3789e5c005e4e354a06dcbb30e31f91`.
- Database connections required execution outside the agent sandbox. No
  application, dependency, schema, or test code changed, so maintained tests
  were not rerun; the latest recorded run passed 21 unit and 9 integration tests.
- Documentation links/content and whitespace were checked. Existing root file
  deletions remain untouched; documentation changes are uncommitted.

### Learning note and next checkpoint

Current inserts use the execution time; historical generation supplies dates
from an earlier interval. Both append rows. Identity gaps from prior tests are
normal, and repeated demonstration titles do not imply duplicate IDs.

Review the five retained articles. Next implement one explicit-ID update,
preserving its ID, author, creation, and publication while changing text and
advancing `updated_at`. No updates, deletions, or continuous loop ran here.

## 2026-10-25 - Scope change: move to ClickHouse

The learner requested moving past source-data exercises and installing
ClickHouse with minimal changes. Further updates, deletions, and continuous
simulation are deferred; they are not prerequisites for the installation.

Inspected the existing Compose configuration and checked the official
[ClickHouse Docker guide](https://clickhouse.com/docs/get-started/setup/self-managed/docker).
Recorded a minimal installation plan in the roadmap: one additional service,
environment settings, a named data volume, localhost HTTP access, readiness,
and a real SQL connection check. No extra Python code or custom server XML is
planned. Destination tables, data transfer, and CDC remain separate later tasks.

Only tracking documentation changed in this planning step. Local Markdown links
and whitespace were checked. No container, dependency, environment setting, or
database was changed, and no runtime tests were run. Pending earlier
documentation and unrelated root deletions remain uncommitted and untouched.

## 2026-10-25 - Install ClickHouse through Docker Compose

### Changes

- Added one `clickhouse` service to the existing Compose file using the official
  stable `clickhouse/clickhouse-server:latest` image. Applied the documented
  open-file limit of 262144 and an authenticated SQL health check.
- Added ClickHouse settings to `.env.example` and appended local values with a
  generated password to the ignored `.env`. Existing PostgreSQL settings were
  preserved; no credentials were printed.
- Published HTTP at `127.0.0.1:8123`, mounted a new named data volume, and used
  the container's included native client. No custom XML or dependency was added.
- Added `05-clickhouse.md` with the official reference and basic commands.

### Verification evidence

- Preflight found no existing project ClickHouse data volume or Docker
  container publishing port 8123. PostgreSQL was healthy.
- `docker compose config --quiet` passed; `.env` remains ignored by Git.
- `docker compose up --detach --no-deps --wait --wait-timeout 120 --quiet-pull
  clickhouse` pulled the image and completed successfully with a healthy service.
- Installed version: `26.10.2.103`. Pulled image digest:
  `clickhouse/clickhouse-server@sha256:b2bfa4d8399ee9973868cc5c1754cb506a6f4b86fbddc41010cc090beb55c85e`.
- An authenticated HTTP SQL query returned `1`, database `article_analytics`,
  user `clickhouse_dev`, and zero application tables. The configured native
  SQL health check also passed.
- Mount inspection confirmed
  `article-analytics-pipeline_clickhouse_data -> /var/lib/clickhouse`.
  Persistence is configured; container recreation was not exercised here.
- Both services are running and healthy, with HTTP port 8123 and PostgreSQL
  port 5432 bound to localhost only.
- PostgreSQL's complete before/after fingerprint matched:
  `2518:e3789e5c005e4e354a06dcbb30e31f91`. No PostgreSQL data changed.
- Documentation links and whitespace checks passed. Python tests were not
  rerun because no Python code changed; runtime installation checks were used.

### Learning note and next action

ClickHouse runs alongside PostgreSQL in Docker, with its own persistent data.
Installing it does not move any articles. Next set up Airbyte for an initial
transfer and define destination table handling at that point. No destination
table, data transfer, CDC, Airbyte, or Airflow was implemented in this step.
The installation changes remain uncommitted; earlier documentation changes and
the pre-existing root deletions are preserved.

## 2026-10-25 - Commit ClickHouse checkpoint before Airbyte

The learner requested committing the pending changes and starting minimal
Airbyte setup. The commit includes Compose, the tracked environment template,
and the pending source-exercise/ClickHouse documentation. Local credentials
and the pre-existing root file deletions are excluded.

Docker preflight confirmed PostgreSQL and ClickHouse remain healthy. The
official Airbyte quickstart uses `abctl`, which manages Kubernetes inside
Docker. No `abctl` was found on PATH. Docker exposes 12 CPUs and approximately
8 GB of memory shared with other running services; use low-resource mode for
this local assessment. This is installation preparation, not a completed
Airbyte runtime check.

## How to maintain this log

For each later step, append a dated entry with its purpose, changed files,
verification actions and actual results, learning notes, unresolved issues, and
the next action. Update the current state and checklist after verification.
Keep prior entries as a history. Never include passwords or other credentials.
