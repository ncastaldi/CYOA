# CYOA

A self-hosted choose-your-own-adventure engine. Drop a story file in, get a branching book you can read in a browser.

---

## Stack

| | |
|---|---|
| **Language** | Python 3.12+ |
| **Framework** | FastAPI |
| **Frontend** | Server-rendered Jinja2 + htmx — no build step, no bundler |
| **Database** | SQLite via SQLAlchemy |
| **Story format** | Markdown with YAML frontmatter |
| **Tests / lint** | pytest, ruff |
| **Deployment** | Docker image published to GHCR, run with Compose behind Traefik |

## Quick Start

### Run it

```bash
docker run --rm -p 8000:8000 ghcr.io/ncastaldi/cyoa:latest
```

Open <http://localhost:8000>. The example story ships in the image, so this works with no volumes and no configuration.

To run the code in your working tree instead of the published image:

```bash
docker compose -f compose.yaml -f compose.local.yaml up --build
```

### Deploy it

```bash
cp .env.example .env        # adjust CYOA_PUBLIC_HOST
docker compose pull && docker compose up -d
```

Compose mounts `./stories` read-only and keeps reader progress in a named volume. Traefik labels are already set — adjust the `certresolver` to match your instance.

**`compose.yaml` on its own is production-only.** It publishes no ports and joins an external `proxy` network that Traefik is expected to already own, so `docker compose up` will not work on a laptop without the `compose.local.yaml` overlay above. That is the point of the split: the deploy path cannot accidentally expose a port, and the local path cannot accidentally reach for a network that isn't there.

### Develop on it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

uvicorn --factory cyoa.main:create_app --reload
```

```bash
pytest                                  # tests — 99 of them, all green
ruff check . && ruff format --check .   # lint and format
```

CI runs exactly those three commands, so a clean local run is a clean pipeline.

FastAPI serves interactive API docs at `/docs` while the app is running, and the OpenAPI schema at `/openapi.json`.

**v1 is complete: the book reads end to end.** Every package has its own tests, and there are no `xfail` specifications left in the suite. See `roadmap.md` for what is queued next and `CLAUDE.md` for how the pieces fit together.

### Write a story

One folder per story under `stories/`, each with a `story.md`:

```markdown
---
title: The Cave
start: mouth
---

## mouth

Cold air pushes out of the opening.

[[Go in->tunnel]]
[[Turn back->trail]]
```

A passage with no choices is an ending. See `stories/README.md` for the quick version and `docs/specs/spec-story-format.md` for the full specification.

## Project Structure

```
src/cyoa/
├── engine/    Story model, parser, graph validation, play state.  Pure Python.
├── library/   Discovers stories on disk, builds the catalogue.
├── storage/   SQLite behind a repository.  The only SQL in the project.
├── web/       FastAPI routes, Jinja templates, static assets.
├── config.py  Environment-driven settings.
└── main.py    Composition root.

stories/        Story content.  Mounted as a volume in production.
tests/          pytest suite and story fixtures.
docs/           All project documentation.
scripts/        Dev-time utilities (not shipped).

CLAUDE.md       Context document: what this is, why it is shaped this way.
roadmap.md      Working queue: done, in progress, and what comes next.
```

The one architectural rule: **the engine is a pure library, everything else is an adapter over it.** `engine/` imports no web framework and no database driver. See `src/cyoa/README.md` for why that matters and what it buys.

---

For the founding brief, see [`docs/foundation.md`](docs/foundation.md).
For the story format, see [`docs/specs/spec-story-format.md`](docs/specs/spec-story-format.md).
For architecture decisions, see the decision log in [`CLAUDE.md`](CLAUDE.md) — ADR-001 through ADR-010 live there while they are short enough to read in one sitting. [`docs/ADRs/`](docs/ADRs/) is where one moves when it outgrows that.
For what is queued next, see [`roadmap.md`](roadmap.md).
For SOPs and runbooks, see [`docs/SOPs/`](docs/SOPs/).
