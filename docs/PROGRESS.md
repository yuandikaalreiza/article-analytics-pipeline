# Progress Log

## Current state

- **Milestone:** 1 - PostgreSQL database and articles table.
- **Checkpoint:** Step 1 documentation created; awaiting your review.
- **Next step:** Step 2 - configure PostgreSQL after the documentation review.
- **Database implementation:** pending; no database or table created by this work.

Read [the roadmap](ROADMAP.md) for the sequence and [the PostgreSQL guide](01-postgresql.md)
for design decisions and acceptance checks.

## Checklist

- [x] Inspect the repository and identify existing files and changes.
- [x] Agree on English documentation and one-step-at-a-time pacing.
- [x] Create the roadmap, PostgreSQL guide, and progress log.
- [ ] Review the Step 1 documentation with the learner.
- [ ] Step 2: create and validate local PostgreSQL configuration.
- [ ] Step 3: start PostgreSQL and verify a SQL connection.
- [ ] Step 4: create and inspect `public.articles`.
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

## How to maintain this log

For each later step, append a dated entry with its purpose, changed files,
verification actions and actual results, learning notes, unresolved issues, and
the next action. Update the current state and checklist after verification.
Keep prior entries as a history. Never include passwords or other credentials.
