# cyoa

The application package. One rule governs its layout:

> **The engine is a pure library. Everything else is an adapter over it.**

```
cyoa/
├── engine/    Story model, parsers, graph validation, play state.  Pure Python.
├── library/   Discovers stories on disk and builds the catalogue.
├── storage/   SQLite behind a repository.  The only SQL in the project.
├── web/       FastAPI routes, Jinja templates, static assets.
├── config.py  Environment-driven settings.
└── main.py    Composition root — wires the adapters around the engine.
```

## Dependency direction

Dependencies point **inward**. `web` and `storage` and `library` may import from `engine`. `engine` imports from none of them, and does not know they exist.

```
web ──┐
      ├──> engine
storage ──┘        (engine imports nothing from its adapters)
library ──┘
```

This is why the roadmap items are additive rather than rewrites:

| Roadmap item | What it actually costs |
|---|---|
| Twee story format | A new parser class in `engine/` |
| CLI or SSH client | A second adapter beside `web/` |
| LLM story generation | A provider behind the same loader interface `library/` already uses |
| Multiplayer | Sessions already carry a participant list; the transport is new, the model mostly is not |
| Move to PostgreSQL | A connection string and a migration, contained to `storage/` |

If a change to one of those forces edits across three packages, the boundary has eroded — that is the signal to stop and fix it rather than push through.

## What does not belong here

- Story content — that lives in `stories/`, outside the package, mounted as a volume in production
- Dev-time utilities — those go in `scripts/`
- Tests — those go in `tests/`

## Conventions

- Public functions and methods carry type hints. mypy is not enabled yet; annotating as we go is what keeps turning it on a config change rather than a refactor.
- Public functions, classes, and modules carry docstrings. Say *why*, not just *what* — the what is usually readable from the signature.
- Passage ids are `snake_case`, so they are safe in URLs without escaping.
