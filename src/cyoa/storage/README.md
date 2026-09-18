# Storage

Persistence for reader progress. SQLite, one file on a mounted volume, behind a repository layer.

Stories themselves are **not** stored here — they are files in `stories/`, discovered by `../library/`. This package holds only what the application generates: where readers are, and where they have been.

## What belongs here

- SQLAlchemy table definitions (`models.py`)
- Engine construction, schema creation, and session scoping (`database.py`)
- Repositories that translate between rows and engine types (`repository.py`)

## What does not belong here

- Story content or anything that parses it (that goes in `../engine/`)
- Business rules about what a valid move is (that goes in `../engine/state.py`)
- HTTP concerns — a repository never raises an HTTP error or returns a response

## Conventions

**No SQL outside this package.** Not in a route, not in a template, not in the engine. If a caller needs data shaped differently, that is a new repository method, not a query written somewhere else.

**Repositories speak engine types.** A caller hands over a `PlaySession` and gets a `PlaySession` back. `PlaySessionRow` never escapes this package. That boundary is what makes "move to Postgres" or "add a cache" a change contained to these three files.

**Rows are not the domain.** `models.py` describes how a session is written down; `cyoa.engine.state.PlaySession` describes what one *is*. They are allowed to diverge — `participants` and `history` are JSON columns precisely because the domain treats them as whole values rather than things to query into.

**No migration tool yet.** `create_schema` calls `create_all`, which is honest about where the project is. The first schema change that cannot be expressed as an added nullable column is the moment Alembic goes in — not before.
