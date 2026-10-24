# Article Analytics Pipeline: Learning Roadmap

## Start here

Build this project one small, observable step at a time. Understand each change,
verify its result, and review it before continuing.

- Read [the PostgreSQL guide](01-postgresql.md) for the current milestone.
- Read [the progress log](PROGRESS.md) for completed work and the next action.
- Documentation is in English. Examples will use PowerShell on the local machine
  and the PostgreSQL container's included `psql` client.

## Milestones

| Milestone | Learning goal | Completion evidence | Status |
| --- | --- | --- | --- |
| 1. PostgreSQL database and table | Run PostgreSQL locally, understand the article schema, and practice SQL operations. | A healthy database, verified schema, successful operation checks, and persistent data. | Step 5 checks passed; milestone review pending |
| 2. Basic Python inserts | Connect a small Python CLI to PostgreSQL and insert a few articles. | Reproducible manual execution and verified inserted rows. | Deferred |
| 3. Historical data generation | Generate realistic articles from 2016 onward using seeds and batches. | Configurable counts, coherent timestamps, and measured batch performance. | Deferred |
| 4. Ongoing data simulation | Perform inserts, updates, soft deletes, and hard deletes from Python. | Verified operations, configurable counts and intervals, and useful failure logs. | Deferred |
| 5. Pipeline integrations | Introduce Airbyte, ClickHouse, then Airflow as separate learning milestones. | Define acceptance criteria when each integration becomes active. | Deferred |

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

For now, use one PostgreSQL container and a named Docker volume. Do not add a
database UI, Python package scaffolding, replication settings, or other services.
