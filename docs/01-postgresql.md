# Milestone 1: PostgreSQL and the Articles Table

## Current checkpoint

**Milestone 1 reviewed; operation and persistence checks passed.** PostgreSQL
is healthy with two labeled practice articles: one active and one soft-deleted.
The next milestone's plan is in [the Python insertion guide](02-python-inserts.md).

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
- `volumes` declares persistent storage. Its current Docker name is
  `article-analytics-pipeline_postgres18_data`; the volume is created at startup.
  Step 3 changed the initial `postgres_data` declaration after discovering that
  name already referred to a PostgreSQL 17 database. See the startup notes below.
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

**Step 2 result:** configuration validated. Runtime verification is recorded in
Step 3 below.

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

### Start and check the service

Run from the repository root in PowerShell:

```powershell
docker compose config --quiet
docker compose up --detach --wait --wait-timeout 60 postgres
docker compose ps --all
```

The first startup downloads the image if it is not already available. Compose
creates the project network, named volume, and container. The image initializes
the database and user from the configured environment when the data directory
is empty. `--detach` leaves the server running in the background; `--wait`
waits for readiness, with a 60-second startup wait limit.

The successful result was `Up (healthy)` with `127.0.0.1:5432->5432/tcp`.

### Inspect the database using SQL

Use this PowerShell snippet to run the included `psql` client over the Compose
network. The single-quoted here-string preserves the dollar signs for the
container's shell to expand. Credentials are read inside the container and are
not printed or written into the command.

```powershell
$inspectionScript = @'
PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X --no-password \
  -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -c "SELECT current_database() AS database_name, current_user AS database_user;" \
  -c "SHOW server_version;" \
  -c "SHOW timezone;" \
  -c "SHOW data_directory;" \
  -c "SELECT count(*) AS public_table_count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
'@
docker compose exec -T postgres sh -c $inspectionScript
```

- `exec -T` runs the client inside the existing container without an interactive
  terminal. It does not start another PostgreSQL server.
- `-h postgres` connects through the service's network address. `PGPASSWORD`
  supplies the configured password without putting its value in the command.
- `-X` ignores client startup files; `--no-password` prevents an unattended
  command from hanging on a password prompt.
- `ON_ERROR_STOP=1` stops the client on SQL errors. Each `-c` runs one read-only
  SQL command.

Observed results:

| Check | Actual result |
| --- | --- |
| Database | `article_source` |
| User | `article_dev` |
| Server version | `18.6 (Debian 18.6-1.pgdg13+2)` |
| Session timezone | `UTC` |
| Data directory | `/var/lib/postgresql/18/docker` |
| Base tables in `public` | `0` |

These results verify a usable source database before creating any application
tables. The installed minor version is an observation; the image still follows
the `postgres:18` major-version tag.

### Inspect health and storage

```powershell
docker inspect --format '{{.State.Status}} / {{.State.Health.Status}} / restarts={{.RestartCount}}' article-analytics-pipeline-postgres-1
docker inspect --format '{{json .Mounts}}' article-analytics-pipeline-postgres-1
```

The healthy container reported `running / healthy / restarts=0`. Its active
named volume is `article-analytics-pipeline_postgres18_data`, mounted at
`/var/lib/postgresql`. A host TCP connection to `127.0.0.1:5432` also succeeded.
Agent sandbox restrictions required Docker engine and host socket checks to run
outside the sandbox; no Docker Desktop or firewall settings were changed.

### First startup: an existing PostgreSQL 17 volume

The first startup failed with an existing-data layout error. Inspection showed
that `article-analytics-pipeline_postgres_data` already existed and contained a
root `PG_VERSION` marker of `17`. The PostgreSQL 18 image uses a different
directory layout and cannot directly open a PostgreSQL 17 cluster. See the
[official image's upgrade and storage notes](https://hub.docker.com/_/postgres).

The failed restart loop was stopped. A temporary container inspected file names
and version markers through a read-only mount. The image's `PGDATA` default and
the service's mount target matched the intended PostgreSQL 18 configuration;
the conflict came from the existing volume contents.

The fix was limited to changing the volume declaration to `postgres18_data`
after verifying that name was unused. Repeating the same startup command then
succeeded. Both the original volume and the new volume still exist. No old
database files were deleted or migrated. The new database uses the new volume
and is separate from any previous data.

**Review checkpoint:** leave PostgreSQL running for inspection. Step 4 will
create the articles table. Row operations and persistence across container
recreation remain Step 5 checks.

## Step 4: create and inspect the articles table

**Purpose:** understand the schema before inserting data.

**File:** [`sql/001_articles.sql`](../sql/001_articles.sql). Execute it explicitly
using `psql`, inside a transaction with stop-on-error behavior. Table creation is
separate from container startup.

### Table: public.articles

| Column | Type | Nullability and behavior |
| --- | --- | --- |
| `id` | `BIGINT` identity | Required; generated always as identity; primary key. |
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

### Create the table explicitly

Before creation, the service was healthy and a read-only lookup of
`to_regclass('public.articles')` returned null, confirming that this table did not
already exist. On a future database where it exists, inspect its definition
first; stop and report any mismatch with the agreed schema rather than replacing
it or assuming conditional creation will repair it.

Run from the repository root in PowerShell:

```powershell
$schemaClient = @'
PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X --no-password \
  -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 -f -
'@
Get-Content -LiteralPath sql/001_articles.sql -Raw | docker compose exec -T postgres sh -c $schemaClient
if ($LASTEXITCODE -ne 0) { throw 'Schema creation failed; inspect the transaction result before continuing.' }
```

`Get-Content -Raw` reads the SQL file and pipes it to the container's client.
`-T` keeps standard input available; `-f -` reads SQL from that input. The SQL
file contains `BEGIN` and `COMMIT`, and `ON_ERROR_STOP=1` stops processing on an
error. A failed statement cannot leave this creation transaction partly
committed.

The observed output was:

```text
BEGIN
CREATE TABLE
COMMIT
```

### Understand the definition

- `public.articles` names the schema and table explicitly.
- `GENERATED ALWAYS AS IDENTITY` assigns IDs from a sequence. Normal inserts
  omit `id`; explicit ID values require a deliberate override. The primary key
  separately enforces uniqueness and creates the table's only index. See
  [PostgreSQL's identity-column documentation](https://www.postgresql.org/docs/18/ddl-identity-columns.html).
- `NOT NULL` makes each field except `deleted_at` required. It does not reject
  empty text; content-quality rules belong to the later generator design.
- `CURRENT_TIMESTAMP` supplies transaction time when creation and update times
  are omitted. It does not automatically change `updated_at` on later updates.
- Four named checks enforce positive author IDs and the lifecycle ordering
  described above. Their names make future constraint failures easier to read.
- `IF NOT EXISTS` skips creation when a relation already exists. It does not
  compare or migrate its definition. See [CREATE TABLE](https://www.postgresql.org/docs/18/sql-createtable.html).

### Inspect the stored schema

These are read-only checks against PostgreSQL's actual definition:

```powershell
$schemaInspection = @'
PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X --no-password \
  -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -c '\d+ public.articles' \
  -c "SELECT ordinal_position, column_name, data_type, is_nullable, column_default, is_identity, identity_generation FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'articles' ORDER BY ordinal_position;" \
  -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND tablename = 'articles';" \
  -c "SELECT count(*) AS user_trigger_count FROM pg_trigger WHERE tgrelid = 'public.articles'::regclass AND NOT tgisinternal;" \
  -c "SELECT count(*) AS article_count FROM public.articles;"
'@
docker compose exec -T postgres sh -c $schemaInspection
if ($LASTEXITCODE -ne 0) { throw 'Schema inspection failed.' }
```

`\d+` is a `psql` inspection command. The SQL queries then make column, index,
trigger, and row-count details explicit.

Observed results:

- Exactly eight columns in the agreed order and with the agreed data types.
- Seven required columns; only `deleted_at` is nullable.
- `id` is an `ALWAYS` identity column and the primary key.
- `created_at` and `updated_at` default to `CURRENT_TIMESTAMP`;
  `published_at` must be supplied and `deleted_at` defaults to null.
- Four lifecycle/author checks are installed, matching the schema file.
- The only index is `articles_pkey`, a unique B-tree on `id`.
- Zero user triggers and zero article rows.

**Review checkpoint:** table creation and metadata inspection are complete.
Inserts, updates, both deletion types, intentional constraint failures,
transaction rollback, rerunning creation, and container recreation remain Step 5.

## Step 5: practice operations and verify persistence

**Purpose:** prove the table behaves correctly and understand transactions.

**Files involved:** [`sql/002_practice_articles.sql`](../sql/002_practice_articles.sql),
the schema script for its repeatability check, this guide, and the progress log.
The practice file is a manual SQL exercise, separate from database initialization.

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

### Run and read the practice operations

Run the practice file once on a dataset without existing `[practice step 5]`
rows. It checks for that prefix before making changes; repeating the practice
file deliberately raises an error instead of duplicating or replacing its rows.
That guard is separate from the repeatable schema-creation script.

```powershell
$practiceClient = @'
PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X --no-password \
  -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 -q -A -t -f -
'@
Get-Content -LiteralPath sql/002_practice_articles.sql -Raw | docker compose exec -T postgres sh -c $practiceClient
if ($LASTEXITCODE -ne 0) { throw 'Article practice SQL failed.' }
```

The file uses `RETURNING` and `psql`'s `\gset` to capture generated IDs, so its
updates and deletes target its own inserted rows. It performs these actions:

1. Insert a historical article with explicit creation/publication times in 2016.
2. Update its content and advance `updated_at`, retaining its ID and creation time.
3. Insert another article and soft-delete it by setting deletion/update times
   together. The row remains in the table.
4. Insert a third article and hard-delete it. The row is removed.
5. Commit the two retained rows.
6. Begin another transaction, insert a temporary article, update the active
   article, and delete the soft-deleted article. Roll back the transaction.

The JSON result groups contain eight boolean checks. Every value must be
`true`; during execution a PowerShell check also parsed them and failed if any
value was false or any expected result group was missing. The file itself stops
on SQL errors and prints the boolean results for inspection.

Observed results: all eight checks were true. The retained IDs were `1` and `2`;
the hard-deleted row and rolled-back insert were absent. The active article's
creation and publication times remain in 2016, while its update time reflects
the current practice operation.

The initial dataset guard prints `1` when no matching practice rows exist and
raises division-by-zero on a repeated run. Its surrounding transaction rolls
back if this check fails. Identity sequences can advance on failed or rolled-back
inserts; gaps are expected and do not require resetting IDs.

### Check deliberately invalid statements separately

Each invalid statement was sent through its own `psql` invocation with
`ON_ERROR_STOP=1` and `VERBOSITY=verbose`. The verification required client exit
code `3`, the expected SQLSTATE, and the expected named constraint for check
violations. These expected errors count as successful checks.

| Case | Invalid input | Expected result |
| --- | --- | --- |
| Missing title | Insert content, publication time, and author without a title. | `23502`: not-null violation |
| Missing publication time | Insert title, content, and author without publication. | `23502`: not-null violation |
| Zero author | Set `author_id` to `0`. | `23514`: `articles_author_id_positive` |
| Negative author | Set `author_id` to `-1`. | `23514`: `articles_author_id_positive` |
| Creation after publication | Creation is one hour after publication; update is two hours after. | `23514`: `articles_created_before_publication` |
| Update before publication | Creation is two hours before publication; update is one hour before. | `23514`: `articles_updated_after_publication` |
| Deletion before publication | Creation is two hours before publication; deletion is one hour before. | `23514`: `articles_deleted_within_lifecycle` |
| Deletion after update | Creation, publication, and update are current transaction time; deletion is one hour later. | `23514`: `articles_deleted_within_lifecycle` |
| Invalid existing-row update | Change the retained historical article's update time to 2015. | `23514`: `articles_updated_after_publication` |

For example, this reproduces the missing-title case as an isolated invocation:

```powershell
$invalidClient = @'
PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X --no-password \
  -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 -v VERBOSITY=verbose -f -
'@
$invalidSql = @'
INSERT INTO public.articles (content, published_at, author_id)
VALUES ('Rejected practice data', CURRENT_TIMESTAMP, 1);
'@
$invalidSql | docker compose exec -T postgres sh -c $invalidClient
if ($LASTEXITCODE -ne 3) { throw 'Expected the invalid statement to fail.' }
```

Run one invalid statement at a time. A failure inside a transaction aborts that
transaction until rollback; it should not hide the results of another scenario.
For the lifecycle cases, supply explicit creation, publication, and update values
so current-time defaults do not accidentally cause a different constraint to fail.

Observed results: all nine cases were rejected as expected. A fingerprint of all
committed row values was identical before and after these rejected statements.

### Verify schema reruns with existing data

The following read-only query captures table identity, row count, and a
fingerprint of every row value. MD5 is used only for this local comparison,
not for password storage or security.

```powershell
$snapshotSql = @'
SELECT json_build_object(
    'table_oid', 'public.articles'::regclass::oid,
    'row_count', count(*),
    'row_fingerprint', md5(COALESCE(jsonb_agg(to_jsonb(a) ORDER BY id), '[]'::jsonb)::text)
) FROM public.articles AS a;
'@
$snapshotSql | docker compose exec -T postgres sh -c $practiceClient
```

Capture this before and after running `sql/001_articles.sql` twice using the
Step 4 creation command. Both runs should succeed and skip the existing table.

Observed results: both reruns succeeded, with table OID `16390`, row count `2`,
and fingerprint `b5934dc43e2939ed872b4247a703c561` unchanged. The identifiers and
fingerprint are observations of this dataset, not values a fresh setup must match.

### Verify persistence through container recreation

Capture the current container ID and the row snapshot above, then run:

```powershell
docker compose ps --quiet postgres
docker compose up --detach --force-recreate --wait --wait-timeout 60 postgres
docker compose ps --quiet postgres
$snapshotSql | docker compose exec -T postgres sh -c $practiceClient
docker compose ps --all
```

Observed results: the container ID changed from `042fc44a5a74...` to
`2993f15413dd...`, the new container became healthy, and the table OID, two-row
count, and fingerprint all matched the pre-recreation snapshot. Mount inspection
confirmed it reused `article-analytics-pipeline_postgres18_data`.

This is a container replacement, not a database reset. The old PostgreSQL 17
volume was not touched. The two retained practice articles remain available
for inspection; future generator counts must account for existing rows.

**Review checkpoint:** all Step 5 operation and persistence checks passed.
Review this milestone before introducing Python dependencies or generator code.

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

All Step 5 checks passed, the schema was inspected, and persistence was
demonstrated. For a new checkout, prepare `.env` as described in Step 2, start the
service with the Step 3 command, and apply `sql/001_articles.sql` with the Step 4
command. Existing Docker volumes are independent of the checkout: a new checkout
on the same machine can reuse this database rather than initialize an empty one.
The full sequence was exercised on the new PostgreSQL 18 volume in Steps 3
through 5; a second isolated clone was not separately bootstrapped.

The database milestone is ready for learner review. Record failures or skipped
checks honestly; container health alone does not complete a milestone.

Python generation, logical replication, Airbyte, ClickHouse, and Airflow remain
deferred until their own milestones.
