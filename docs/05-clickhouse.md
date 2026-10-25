# ClickHouse: Local Docker Installation

This setup follows the [official Docker guide](https://clickhouse.com/docs/get-started/setup/self-managed/docker).
See [the progress log](PROGRESS.md) for actual runtime verification.

## Configuration

The existing [compose.yaml](../compose.yaml) now defines PostgreSQL and ClickHouse
as separate services. ClickHouse uses the official
`clickhouse/clickhouse-server:26.7` image. Version 26.7.37.6 was verified after
the Airbyte compatibility fix; the initial installation used `latest` (26.10).

- Database and user: `article_analytics` and `clickhouse_dev`, configured through
  `.env`. The password is in the ignored local `.env`; tracked settings use a
  placeholder in [.env.example](../.env.example).
- HTTP endpoint: `http://127.0.0.1:8123`, with a configurable host port.
- Data: named volume `clickhouse_26_7_data` mounted at `/var/lib/clickhouse`.
  The original `clickhouse_data` volume is retained separately.
- Client compression: [compression.xml](../clickhouse/users.d/compression.xml)
  is mounted read-only under `/etc/clickhouse-server/users.d/` and selects LZ4.
- Readiness: an authenticated `SELECT 1` through the included native client.
- Open-file limit: 262144, following the Docker guide.

Native port 9000 is available inside the Docker network. Host SQL access uses
HTTP; a native client can also run inside the container.

## Commands

Run from the repository root in PowerShell:

```powershell
docker compose config --quiet
docker compose up --detach --no-deps --wait --wait-timeout 120 clickhouse
docker compose ps
```

Open the included SQL client; its credentials expand inside the container:

```powershell
docker compose exec clickhouse sh -c 'exec clickhouse-client --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" --database "$CLICKHOUSE_DB"'
```

Then run:

```sql
SELECT 1;
SELECT version(), currentDatabase(), currentUser();
SHOW TABLES;
```

Airbyte creates and maintains `article_analytics.articles`. Use
`article_analytics.articles_current` for the source's current rows after applying
the view below. Use the underlying `articles FINAL` when inspecting CDC metadata.

To stop only ClickHouse while retaining its data:

```powershell
docker compose stop clickhouse
```

Starting the service again reuses its named volume. PostgreSQL keeps its own
service and volume.

## Airbyte compatibility

The initial 26.10 server exposed two Java-client incompatibilities: ZSTD
responses caused an LZ4 decoding error, and a response-format override caused
schema parsing to fail. LZ4 alone fixed only the first error. Pinning 26.7
with a fresh volume resolved the schema failure; the previous volume was kept
instead of opening newer database files with an older server.

## Current articles view

Airbyte delivers PostgreSQL hard deletes as rows with `_ab_cdc_deleted_at`
populated. The existing `ReplacingMergeTree` keeps the latest version per ID;
`FINAL` alone does not remove those deletion markers.

[003_clickhouse_articles_current.sql](../sql/003_clickhouse_articles_current.sql)
defines a normal view: first read the latest article versions with `FINAL`, then
exclude hard-delete markers. It exposes the original eight article columns.
Application soft deletes remain present with `deleted_at` populated, matching
PostgreSQL. For active articles, additionally filter `deleted_at IS NULL`.

Apply after Airbyte has created the underlying `articles` table. From the
repository root in PowerShell:

```powershell
Get-Content -Raw sql/003_clickhouse_articles_current.sql | docker compose exec -T clickhouse sh -c 'exec clickhouse-client --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" --database "$CLICKHOUSE_DB" --multiquery'
```

The SQL uses the configured database selected by the client. Reapplying replaces
only the view definition; it preserves all underlying article rows.

```sql
SELECT * FROM article_analytics.articles_current WHERE id = 1398;
SELECT count(*) FROM article_analytics.articles_current;
SELECT count(*) FROM article_analytics.articles_current WHERE deleted_at IS NOT NULL;
```

After ID 1398's hard-delete event is synced, the first query should return no
rows. The view reads newly synced data on every query without a refresh job or
duplicated storage. It retains the underlying CDC data; it does not physically
delete it. Airbyte continues writing to `articles`, not to the view.

The `FINAL` operation adds read work, especially for broad queries over a growing
table. Benchmark realistic queries and design retention separately before
claiming production-scale performance. A normal view provides logical
current-state equality with PostgreSQL after sync; raw-table row counts can differ.
