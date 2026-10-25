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

Airbyte now creates and maintains `article_analytics.articles`. Query it using
`FINAL` when checking deduplicated results.

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
