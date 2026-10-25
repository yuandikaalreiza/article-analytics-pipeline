# ClickHouse: Local Docker Installation

This setup follows the [official Docker guide](https://clickhouse.com/docs/get-started/setup/self-managed/docker).
See [the progress log](PROGRESS.md) for actual runtime verification.

## Configuration

The existing [compose.yaml](../compose.yaml) now defines PostgreSQL and ClickHouse
as separate services. ClickHouse uses the official
`clickhouse/clickhouse-server:latest` image, which follows the stable release
branch. The installed version and image digest are recorded in the progress log.

- Database and user: `article_analytics` and `clickhouse_dev`, configured through
  `.env`. The password is in the ignored local `.env`; tracked settings use a
  placeholder in [.env.example](../.env.example).
- HTTP endpoint: `http://127.0.0.1:8123`, with a configurable host port.
- Data: named volume `clickhouse_data` mounted at `/var/lib/clickhouse`.
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

The analytics database starts without application tables. Creating the article
destination and transferring PostgreSQL data are subsequent tasks.

To stop only ClickHouse while retaining its data:

```powershell
docker compose stop clickhouse
```

Starting the service again reuses its named volume. PostgreSQL keeps its own
service and volume. No application tables, data transfer, CDC, or Airbyte are
part of this installation step.
