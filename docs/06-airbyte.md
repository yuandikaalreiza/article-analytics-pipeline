# Airbyte: Minimal Local Setup

Follow the [official local quickstart](https://docs.airbyte.com/platform/using-airbyte/getting-started/oss-quickstart).
See [the progress log](PROGRESS.md) for actual installation status and checks.

**Installed and verified:** Airbyte 2.4.0 is available at
`http://localhost:8000`. Source and destination configuration is the next step.

Airbyte's supported local installer is `abctl`. It manages a Kubernetes cluster
inside Docker using kind. PostgreSQL and ClickHouse stay in the existing Compose
project; Airbyte is managed separately by `abctl`.

## Local installation

The official Windows AMD64 `abctl` release is stored in the ignored project
cache. No system PATH change was needed. Download and extraction used the
[official v0.30.4 release](https://github.com/airbytehq/abctl/releases/tag/v0.30.4).
Its published archive SHA-256 matched:
`215c59f084d5b8dad4357b36e152353ee95811ee768c3b49c04ba33d566358c2`.

Run from the repository root in PowerShell:

```powershell
$abctl = ".cache/tools/abctl/v0.30.4/abctl-v0.30.4-windows-amd64/abctl.exe"
$env:DO_NOT_TRACK = "1"
& $abctl version
& $abctl local install --chart-version 2.4.0 --values airbyte/values.yaml --low-resource-mode --no-browser --host localhost --insecure-cookies
```

Low-resource mode reduces the installation footprint and disables Connector
Builder, which is unnecessary for the built-in PostgreSQL and ClickHouse
connectors. Docker exposes approximately 8 GB of memory shared with existing
services. Installation readiness must be verified; the presence of a Docker
container alone does not mean the Airbyte application is ready.

The expected UI address is `http://localhost:8000`. The host option configures
the HTTP ingress hostname; it is not a Docker loopback binding setting.
Cookies are allowed over HTTP for this local development instance.

## Required image overrides

The official chart 2.4.0 references `airbyte/utils:2.4.0` and
`airbyte/async-profiler:2.4.0`, which are not published. The initial installation
stalled during image preparation. An older chart inspected during diagnosis
had the same problem, so downgrading was not used.

The small [values file](../airbyte/values.yaml) retains the official chart and
overrides only these two references: `utils:latest` for the optional Helm
connection test, and a verified official Linux AMD64 profiler image pinned by
digest. All core Airbyte component versions remain 2.4.0. A similar missing-tag
problem is [reported upstream](https://github.com/airbytehq/airbyte/issues/70969).
The retry reused the existing cluster and downloaded images without deleting data.

## Status and login

```powershell
& $abctl local status
```

Airbyte generates local login credentials during installation. To view them
privately in your own terminal after successful installation:

```powershell
& $abctl local credentials
```

Keep those values out of Git and shared logs. `abctl` stores its local cluster
configuration under `$env:USERPROFILE/.airbyte/abctl`; the executable/cache is
not committed. First-time UI onboarding may ask for an email and organization.
For this installation, the generated login email and password were saved to
the ignored `.cache/airbyte-login.json` without printing their values.

## Verified installation results

- `abctl` v0.30.4; Airbyte chart/application 2.4.0; installer exited successfully.
- Eight long-running Airbyte pods ready; bootloader completed. Both persistent
  volume claims are bound. Ingress controller is ready.
- `abctl local status` reports deployed Airbyte and ingress charts.
- UI returned HTTP 200 with Airbyte HTML. `/api/v1/health` returned HTTP 200
  and `available=true`.
- PostgreSQL and ClickHouse remain healthy. The 2,518-row source fingerprint
  matches its prior value, and the ClickHouse analytics database remains empty.
- Credentials are excluded from Git and were not printed to shared output.

The host's Docker mapping for Airbyte uses port 8000 on all interfaces; the
ingress accepts the configured `localhost` hostname. PostgreSQL and ClickHouse
retain their existing loopback-only host bindings.

## Subsequent CDC verification

The learner configured the PostgreSQL source and ClickHouse destination in the
UI. PostgreSQL now starts with `wal_level=logical`; source CDC uses slot
`airbyte_slot` and publication `airbyte_publication`. Container-to-host access
uses `host.docker.internal`. The local PostgreSQL server uses disabled SSL.
ClickHouse uses HTTP port 8123 and the 26.7 compatibility configuration described
in [its guide](05-clickhouse.md).

Initial transfer and later committed source changes were observed in ClickHouse.
An idle CDC read logged `Heartbeat not progressing` while its processed WAL
position remained below the target. A requested single-row update advanced it;
job 7 then completed with 1,401 committed records. This is a documented local
observation, not a requirement to manually write data before every sync.

The learner configured an hourly Airbyte schedule. Airflow remains deferred.
Check each job's final status separately from the generator's status.

## Original installation scope

This step installs Airbyte only. Next configure PostgreSQL as a source and
ClickHouse as a destination, then perform one manual initial transfer. Connector
network reachability must be checked then; addresses inside Airbyte containers
are not the host's localhost. CDC, schedules, and Airflow remain deferred.
