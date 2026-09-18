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

To run it properly, with your own stories and persistent progress:

```bash
cp .env.example .env        # adjust CYOA_PUBLIC_HOST
docker compose up -d
```

Compose mounts `./stories` read-only and keeps reader progress in a named volume. Traefik labels are already set — adjust the `certresolver` to match your instance.

### Develop on it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

uvicorn --factory cyoa.main:create_app --reload
```

```bash
pytest                                  # tests
ruff check . && ruff format --check .   # lint and format
```

Most of the engine is not implemented yet — its tests are written as `xfail` specifications. See `tests/README.md` for how that works, and `CLAUDE.md` for what is built and what is not.

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
```

The one architectural rule: **the engine is a pure library, everything else is an adapter over it.** `engine/` imports no web framework and no database driver. See `src/cyoa/README.md` for why that matters and what it buys.

---

For the founding brief, see [`docs/foundation.md`](docs/foundation.md).
For the story format, see [`docs/specs/spec-story-format.md`](docs/specs/spec-story-format.md).
For architecture decisions, see [`docs/ADRs/`](docs/ADRs/).
For SOPs and runbooks, see [`docs/SOPs/`](docs/SOPs/).
