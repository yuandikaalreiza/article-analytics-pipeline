# Progress Log

## Current state

- **Milestone:** 1 - PostgreSQL database and articles table.
- **Checkpoint:** Step 4 table creation and schema inspection complete; awaiting
  your review before row-operation checks.
- **Next step:** Step 5 - practice and verify operations, constraints,
  repeatability, rollback, and persistence.
- **Database implementation:** PostgreSQL is running with the agreed
  `public.articles` table; it currently contains zero rows.

Read [the roadmap](ROADMAP.md) for the sequence and [the PostgreSQL guide](01-postgresql.md)
for design decisions and acceptance checks.

## Checklist

- [x] Inspect the repository and identify existing files and changes.
- [x] Agree on English documentation and one-step-at-a-time pacing.
- [x] Create the roadmap, PostgreSQL guide, and progress log.
- [x] Review the Step 1 documentation with the learner.
- [x] Step 2: create and validate local PostgreSQL configuration.
- [x] Add repository agent guidance before starting PostgreSQL.
- [x] Step 3: start PostgreSQL and verify a SQL connection.
- [x] Step 4: create and inspect `public.articles`.
- [ ] Step 5: verify operations, constraints, rollback, repeatability, and persistence.
- [ ] Review the completed database milestone before designing basic Python inserts.

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

## How to maintain this log

For each later step, append a dated entry with its purpose, changed files,
verification actions and actual results, learning notes, unresolved issues, and
the next action. Update the current state and checklist after verification.
Keep prior entries as a history. Never include passwords or other credentials.
