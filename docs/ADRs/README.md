# Architecture Decision Records (ADRs)

This folder contains Architecture Decision Records for the project. Each ADR documents a significant technical or structural decision — what was decided, why, what was ruled out, and what the consequences are.

ADRs are written when a decision is made and updated if circumstances change. They are not deleted — superseded decisions are marked as such and kept for historical context.

## Where CYOA's ADRs actually live

**This folder is empty, and that is current rather than an oversight.** CYOA's accepted decisions — ADR-001 through ADR-010 — are recorded in the decision log at the bottom of [`CLAUDE.md`](../../CLAUDE.md), where each is a short paragraph:

| | |
|---|---|
| ADR-001 | Python 3.12 + FastAPI |
| ADR-002 | Server-rendered HTML + htmx, no SPA |
| ADR-003 | SQLite behind a repository |
| ADR-004 | Markdown + YAML frontmatter for stories, parser behind a protocol |
| ADR-005 | Engine as a pure library; web, storage, and library are adapters |
| ADR-006 | v1 is read-only: no editor, no auth |
| ADR-007 | GHCR image built in CI, deployed with Compose behind Traefik |
| ADR-008 | Unimplemented modules ship as `xfail(strict=True)` specifications |
| ADR-009 | Validation reports warnings even when errors are present |
| ADR-010 | A reader's place lives in a cookie pointing at a database row |

Keeping them there is deliberate: they are the context an assistant or a returning maintainer needs in the same file as everything else they need, and each is currently short enough to read in one sitting. A decision **graduates into this folder** when it outgrows a paragraph — when it needs the alternatives written out, a migration path, or diagrams. At that point the entry in `CLAUDE.md` shrinks to a one-line summary and a link, so there is still exactly one place to look for the list.

Open questions — decisions deliberately *not* yet made — are tracked in the Open questions section of `CLAUDE.md`, not here. An ADR records a decision; an open question is the absence of one.

## What belongs here

- Technology choices (language, framework, database, external APIs)
- Structural patterns (adapter pattern, repository pattern, module boundaries)
- Constraint decisions (no scraping, BYOK model, CLI-only scope)
- Anything where future-you (or a new collaborator) would ask "why did we do it this way?"

## What does not belong here

- Implementation details (those go in docs/specs/)
- Project timelines or milestones (those go in docs/plans/)
- Runbooks or procedures (those go in docs/SOPs/)

## Naming convention

`ADR-NNN-short-description.md` — e.g. `ADR-001-database-choice.md`

## Status values

| Status | Meaning |
|--------|---------|
| Accepted | In effect, follow this decision |
| Draft | Under discussion, not yet binding |
| Deprecated | No longer relevant but kept for history |
| Superseded | Replaced by a later ADR — link provided |
