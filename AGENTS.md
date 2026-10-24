# Repository guidance

This is a local, self-hosted Data Engineering assessment built as a learning
project. Favor small changes the learner can inspect and understand.

## Read before working

- Read [docs/PROGRESS.md](docs/PROGRESS.md) for the current checkpoint, completed
  checks, and next action. Verify repository state before treating past results
  as current evidence.
- Read [docs/ROADMAP.md](docs/ROADMAP.md) for the active milestone and boundaries.
- For PostgreSQL work, read [docs/01-postgresql.md](docs/01-postgresql.md) for the
  agreed design, commands, and acceptance checks.

## Learning workflow

1. Explain the current step's purpose and expected result in plain English.
2. Implement one agreed learning step per turn unless the user explicitly asks
   for multiple steps. Introduce later components when their milestone is active.
3. Run checks appropriate to the change. Distinguish configuration validation,
   runtime checks, and unverified expectations. Documentation changes need link
   and content checks; database changes need the relevant integration checks.
4. Update `docs/PROGRESS.md` with actual results, lessons, unresolved issues, and
   the next action. Keep the current state and checklist accurate; preserve dated
   entries as history. Put detailed learning explanations and commands in the
   relevant guide. Use English for documentation and PowerShell for host examples.
5. Report what changed, what was verified, and the next step. Pause for the
   learner's review before advancing to another implementation step.

## Implementation and Git

- Keep runtime components local and open source. Choose the simplest approach
  that satisfies the active milestone; add tools and dependencies when needed.
- Keep database settings in configuration and schema details in their guide or
  SQL source. Link to those sources instead of copying them into this file.
- Keep local credentials in ignored files and out of logs, documentation, and
  commits. Use placeholders in tracked environment examples.
- Retain database volumes during routine operations. Delete persistent data
  only when the user explicitly requests a destructive reset.
- Preserve unrelated working-tree changes and existing local environments.
- When asked to commit, use Conventional Commits, such as `docs: ...` or
  `feat: ...`. Stage explicit paths for the requested work and inspect the staged
  diff before committing.
