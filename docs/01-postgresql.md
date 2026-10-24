# Milestone 1: PostgreSQL and the Articles Table

## Current checkpoint

**Step 2: PostgreSQL configuration validated; review pending.** Compose and
environment files now exist. PostgreSQL has not been started, and no table or
SQL script has been created. Step 3 will start and inspect the database.

Follow [the roadmap](ROADMAP.md) for the sequence and [the progress log](PROGRESS.md)
for verification evidence. This guide records the approved design. Executable
commands and SQL examples will be added as we implement their corresponding step.

## What we are learning

The first milestone connects a local terminal to PostgreSQL in a Docker container.
PostgreSQL stores its data in a named Docker volume.

- A **container** runs the PostgreSQL server.
- A **database** is a named collection of data within that server.
- A **schema** groups database objects; we use the default `public` schema.
- A **table** stores article rows with defined columns and constraints.
- A **volume** retains database files independently of the container lifecycle.
- The **psql client** sends SQL to PostgreSQL; it is included in the image.

We will create the database first and the table in a later step so that both
results can be inspected separately.

## Step 2: configure PostgreSQL

**Purpose:** describe one local service and understand its configuration before
starting it.

**Files:** [`compose.yaml`](../compose.yaml), [`.env.example`](../.env.example),
local `.env`, and a minimal [`.gitignore`](../.gitignore). The example file contains
documented development settings and a password placeholder; the local file
supplies the actual password. The existing local file was created with a randomly
generated password; it was not printed or committed.

| Setting | Agreed choice | Reason |
| --- | --- | --- |
| Image | Official `postgres:18` | Fix the major version while allowing its maintenance updates. |
| Database | `article_source` | Identify the source database for this project. |
| Database user | `article_dev` | One administrator for the local learning milestone. |
| Password | Supplied through local `.env` | Keep credentials out of committed files. |
| Host binding | `127.0.0.1` | Limit the published port to the local machine. |
| Host port | Configurable; default `5432` | Allow adjustment if another local database uses that port. |
| Session timezone | UTC | Display timestamps consistently. |
| Persistence | Named volume mounted at `/var/lib/postgresql` | Use the documented volume location for PostgreSQL 18. |
| Readiness | `pg_isready` health check, then a SQL connection | Check both server readiness and the intended database connection. |

The image's database environment settings initialize an empty data directory.
With an existing volume, changing `.env` does not rename the database, recreate
the user, or change its password. See the [official PostgreSQL image documentation](https://hub.docker.com/_/postgres).

**Expected result:** Compose configuration validates, credentials are ignored by
Git, and Docker engine access is verified. This step does not start PostgreSQL.

### Understand the configuration

- `name` keeps the Compose project and its resource names consistent.
- `services.postgres` describes the single service; it does not start it.
- `environment` passes database settings into the container. Compose reads `.env`
  to substitute values; a shell variable with the same name takes precedence.
- `${POSTGRES_DB:-article_source}` uses the default when the variable is unset or
  empty. `${POSTGRES_PASSWORD:?...}` rejects an unset or empty password.
- `command` tells PostgreSQL to use UTC for its default session timezone.
- `ports` maps the host port to port `5432` in the container. Binding to
  `127.0.0.1` restricts access to this machine.
- `volumes` declares persistent storage. Its default Docker name is
  `article-analytics-pipeline_postgres_data`; the volume is created at startup.
- `healthcheck` runs `pg_isready` over TCP every 10 seconds, with a 5-second
  timeout, 5 retries, and a 30-second startup grace period. `$${POSTGRES_USER}`
  defers substitution to the container shell instead of Compose.
- `restart: unless-stopped` lets Docker restart a running service after a failure
  or engine restart, unless it has been explicitly stopped.

See [Docker's interpolation documentation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
for variable defaults and precedence. The initial `article_dev` database user is
an administrator, suitable for this local learning milestone. Separate application
permissions will be considered with the Python generator.

### Prepare a new checkout

From the repository root in PowerShell, run this only if `.env` does not already
exist:

```powershell
Copy-Item -LiteralPath .env.example -Destination .env
```

Edit `.env` locally and replace the password placeholder with your own password.
For this checkout, the local file is already prepared; keep it rather than
overwriting it with the example. The `POSTGRES_PORT` variable controls only the
host port. Change it if another service uses `5432`.

### Commands used to verify Step 2

Run from the repository root:

```powershell
docker compose version
docker version --format '{{.Client.Version}} / {{.Server.Version}}'
docker compose config --quiet
git check-ignore -- .env .venv/ .cache/
git check-ignore -- .env.example
docker compose ps --all --format json
```

The configuration check should exit successfully without output. The ignore
check should list the local environment and cache paths; the separate example
check should print nothing and exit with code 1, meaning `.env.example` is
trackable. The container listing is empty before the first startup.

Use `config --quiet` for routine validation. Plain `docker compose config`
displays the resolved environment, including the password. During verification,
the JSON configuration was inspected in memory and only assertion results were
printed.

**Observed results:** Docker Compose `v5.5.1`, Docker client and server `29.8.2`,
valid Compose configuration, correct host binding and volume mount, configured
password, correct ignore behavior, and no containers for this project. Docker
engine checks required execution outside the agent sandbox; no Docker Desktop
settings were changed. No TCP listener on host port `5432` was observed at check
time; startup will determine whether it can actually be bound.

**Review checkpoint:** configuration is ready. Starting PostgreSQL, inspecting
the database, and confirming runtime health belong to Step 3.

## Step 3: start and inspect the database

**Purpose:** start the configured server and verify the database before adding
tables.

**Files involved:** the configuration files from Step 2, this guide, and the
progress log.

**Expected result:** the container is healthy and `psql` connects to
`article_source` as `article_dev`.

**Verification:** inspect database name, PostgreSQL major version, current user,
and UTC session timezone. Record the actual results in the progress log.

A running container may still be initializing. A health check gives a readiness
signal; the SQL connection confirms that the intended database is usable. See
[Docker's readiness guidance](https://docs.docker.com/compose/how-tos/startup-order/).

## Step 4: create and inspect the articles table

**Purpose:** understand the schema before inserting data.

**Planned file:** `sql/001_articles.sql`. Execute it explicitly using `psql`,
inside a transaction with stop-on-error behavior. Do not automatically create the
table during container startup.

### Table: public.articles

| Column | Type | Nullability and behavior |
| --- | --- | --- |
| `id` | `BIGINT` identity | Required; generated primary key. |
| `title` | `TEXT` | Required. |
| `content` | `TEXT` | Required. |
| `published_at` | `TIMESTAMPTZ` | Required; explicitly supplied. |
| `author_id` | `BIGINT` | Required; must be positive. |
| `created_at` | `TIMESTAMPTZ` | Required; defaults to current transaction time. |
| `updated_at` | `TIMESTAMPTZ` | Required; defaults to current transaction time. |
| `deleted_at` | `TIMESTAMPTZ` | Optional; null means the article is active. |

The table represents published articles. An authors table and draft publication
workflow are outside this milestone.

### Timestamp rules

- `created_at <= published_at <= updated_at`.
- When `deleted_at` is present, `published_at <= deleted_at <= updated_at`.
- A historical insert must explicitly provide coherent creation, publication,
  and update times. Current-time defaults alone cannot describe an old article.
- Updating an article explicitly advances `updated_at` while preserving its ID
  and creation time.
- Soft deletion sets `deleted_at` and `updated_at` together.
- No trigger automatically maintains timestamps in this milestone.

`TIMESTAMPTZ` represents an instant and displays it using the session timezone.
It does not retain the original timezone label. We use UTC sessions and explicit
timezone offsets in examples. See [PostgreSQL's date/time documentation](https://www.postgresql.org/docs/18/datatype-datetime.html).

### Keys, indexes, and repeatability

Use the primary-key index only. Additional indexes should follow actual query
needs. `author_id` has no foreign key because there is no authors table yet.

Conditional table creation makes rerunning the script safe for the same schema
and existing data. It is not a migration system: if a table already exists with
a different shape, inspect and report the mismatch instead of silently changing
or replacing it.

**Expected result:** all eight columns and the agreed constraints exist.

**Verification:** inspect column types, nullability, identity, defaults,
constraints, and indexes. Record the observed schema in the progress log.

## Step 5: practice operations and verify persistence

**Purpose:** prove the table behaves correctly and understand transactions.

**Files involved:** SQL examples added to this guide, the schema script for its
repeatability check, and the progress log. Use a small number of clearly
identified practice rows.

| Check | Expected result |
| --- | --- |
| Insert a valid article | One row is stored with a generated ID and coherent timestamps. |
| Omit a required value | The insert fails without a committed invalid row. |
| Supply a nonpositive author ID | The insert fails. |
| Supply invalid timestamp ordering | The insert or update fails. |
| Update title or content and advance `updated_at` | ID and `created_at` remain unchanged. |
| Soft delete | The row remains; deletion and update times are populated consistently. |
| Hard delete | The selected row no longer exists. |
| Roll back a valid transaction | Its row changes are not committed. |
| Rerun table creation | Existing rows and table structure remain intact. |
| Recreate the container while retaining its named volume | A committed practice row remains available. |

Run deliberate constraint failures separately so an aborted transaction does
not prevent unrelated checks. A rolled-back insert can still consume an identity
value; gaps in IDs are normal.

Normal stop/start and container recreation must retain the volume. Volume
deletion is a separate destructive reset and is not part of these checks.

Use manual integration checks now. Introduce Python unit tests with the generator.

## Troubleshooting notes

| Symptom | What to investigate |
| --- | --- |
| Docker engine cannot be reached | Check Docker Desktop is running and this terminal can access its Linux engine. |
| Host port is already occupied | Choose another host port in `.env`; keep the container's PostgreSQL port unchanged. |
| Container runs but SQL fails | Inspect health and startup logs, then verify connection settings. |
| A changed password in `.env` does not work | Existing volumes retain the credentials established at initialization. |
| SQL fails on a timestamp constraint | Inspect all lifecycle timestamps together, including values supplied by defaults. |
| Existing table differs from the guide | Stop and inspect the mismatch; conditional creation does not migrate it. |

Exact troubleshooting commands will be recorded when they are needed and
verified during implementation.

## Milestone acceptance

The milestone is complete only after every Step 5 check passes, the schema is
verified, persistence is demonstrated, and the documented setup can be repeated
from a clean checkout. Record failures or skipped checks honestly; container
health alone does not complete the milestone.

Python generation, logical replication, Airbyte, ClickHouse, and Airflow remain
deferred until their own milestones.
