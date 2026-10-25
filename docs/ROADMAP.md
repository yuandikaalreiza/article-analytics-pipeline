# Article Analytics Pipeline: Learning Roadmap

## Start here

Build this project one small, observable step at a time. Understand each change,
verify its result, and review it before continuing.

- Read [the PostgreSQL guide](01-postgresql.md) for database setup and SQL exercises.
- For milestone 2, read [the Python insertion guide](02-python-inserts.md).
- For milestone 3, read [the October generation plan](03-historical-generation.md).
- For milestone 4, read [the ongoing simulation guide](04-ongoing-simulation.md).
- For ClickHouse setup, read [the Docker installation guide](05-clickhouse.md).
- For Airbyte setup, read [the local installation guide](06-airbyte.md).
- Read [the progress log](PROGRESS.md) for completed work and the next action.
- Documentation is in English. Examples will use PowerShell on the local machine
  and the PostgreSQL container's included `psql` client.

## Milestones

| Milestone | Learning goal | Completion evidence | Status |
| --- | --- | --- | --- |
| 1. PostgreSQL database and table | Run PostgreSQL locally, understand the article schema, and practice SQL operations. | A healthy database, verified schema, successful operation checks, and persistent data. | Reviewed and committed |
| 2. Basic Python inserts | Connect a small Python CLI to PostgreSQL and insert a few articles. | Reproducible manual execution and verified inserted rows. | Reviewed and complete; 21 tests passed |
| 3. Historical data generation | Start with 2,500 synthetic articles from October 1, 2026, through a fixed October cutoff; use seeds and bounded batches. | Verified counts, coherent timestamps, reproducibility, and observed load time. | Reviewed and complete: 2,500 added, 2,513 total |
| 4. Ongoing data simulation | Simulate article changes over a duration in minutes. | Configurable inserts, updates, soft/hard deletes, per-operation commits, and useful logs. | Implemented and tested; committed hard delete excluded from destination current-state view |
| 5. Pipeline integrations | Install ClickHouse first, then connect the pipeline with Airbyte; introduce Airflow later. | Verified initial transfer and later CDC syncs to ClickHouse. | CDC replication verified; final reconciliation after generation stops remains pending; Airflow deferred |

## ClickHouse installation: complete

Follow the [official Docker installation guide](https://clickhouse.com/docs/get-started/setup/self-managed/docker).
The source already has sufficient data; further Python simulation is deferred.

1. Add one `clickhouse` service to the existing `compose.yaml`, using the official
   `clickhouse/clickhouse-server` image. Use the documented stable `latest` tag
   for the initial installation and record the pulled version and image digest.
2. Add database/user/password settings to `.env.example` and the ignored local
   `.env`. Create `article_analytics` with a local `clickhouse_dev` user.
3. Mount a named volume at `/var/lib/clickhouse`, publish HTTP port 8123 on
   `127.0.0.1`, set the documented `nofile` limit of 262144, and add a simple
   readiness check. Use the included client; no extra client installation or
   custom XML configuration is needed.
4. Validate Compose, start only ClickHouse, and verify `SELECT 1`, the installed
   version, and database availability. Preserve the PostgreSQL container/data.
5. Record the actual results in the progress log. Creating destination tables,
   transferring articles, CDC, Airbyte, and Airflow are subsequent tasks.

ClickHouse is running and healthy. Authenticated HTTP SQL confirmed version
`26.10.2.103`, database `article_analytics`, and user `clickhouse_dev`.
The database has no application tables yet. Airbyte 2.4.0 is now installed with
`abctl` and its UI/API are healthy at `http://localhost:8000`. Next configure its
PostgreSQL source and ClickHouse destination for one manual initial transfer;
decide destination table handling there. Further simulation, CDC, and Airflow
remain deferred.

Later milestones are a direction, not an implementation specification. Design
each one after the preceding milestone has been reviewed. All components must
remain self-hosted, open source, and runnable locally.

## Milestone 1 sequence

| Step | Purpose | Files involved | Expected result | Verification |
| --- | --- | --- | --- | --- |
| 1. Create tracking documentation | Agree on the learning sequence and record progress. | The three Markdown files in `docs/`. | A navigable roadmap, guide, and progress log. | Read the documents, check their links, and confirm database work is still pending. |
| 2. Configure PostgreSQL | Describe the local service and its settings. | `compose.yaml`, `.env.example`, local `.env`, and minimal `.gitignore`. | Valid Compose configuration with credentials excluded from Git. | Validate Compose, check ignore rules without printing credentials, and verify Docker engine access. |
| 3. Start and inspect the database | Observe the difference between a running container and a usable database. | Compose and environment files; updated guide and log. | PostgreSQL accepts SQL connections to `article_source`. | Check health, database name, server version, and UTC session timezone. |
| 4. Create the articles table | Learn columns, defaults, constraints, and the primary key. | `sql/001_articles.sql`; updated guide and log. | The agreed `public.articles` schema exists. | Inspect all eight columns, constraints, defaults, and indexes. |
| 5. Practice and verify | Learn data changes, transactions, repeatability, and persistence. | `sql/002_practice_articles.sql`, guide examples, and progress log. | Each acceptance check has recorded evidence. | Run the checks listed in the PostgreSQL guide. |

Each step depends on the previous one. Step 1 creates documentation only.
Steps 2 through 5 are performed separately, with a review checkpoint after each.

## Working agreement

The repository's [AGENTS.md](../AGENTS.md) defines the learning workflow,
verification, documentation, and commit conventions for agents. Keep those
instructions there; use this roadmap for milestone boundaries and sequencing.

PostgreSQL and ClickHouse run in Compose with separate named volumes. Airbyte
runs in a Docker-backed cluster managed by `abctl`. Python runs on the host
through uv. No installable Python package, CDC settings, or Airflow is needed
for the current installation checkpoint.
