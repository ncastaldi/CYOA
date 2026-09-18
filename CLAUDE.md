# CLAUDE.md

This file is the primary context document for Claude (and other LLM assistants) working in this repository. Read it first.

---

## Project identity

**CYOA** — a self-hosted choose-your-own-adventure engine. A containerized application someone runs on their own hardware; once running, it serves a digital choose-your-own-adventure book, read in a browser.

This is a hobby project. **The engine is the point** — the fun is in building the platform, and stories are the excuse. Story content comes from elsewhere: people close to the maintainer, or an LLM. That has a real consequence for design — the engine must be general enough to run a story it has never seen, written by someone who never read its source.

Anything that makes the engine more interesting to build is worth considering. Anything that turns this into a content-management chore is not.

## Stack

- **Python 3.12+**
- **FastAPI** — chosen over Flask for native async, SSE, and websockets, which is what the multiplayer and LLM-streaming roadmap items need
- **Jinja2 + htmx** — server-rendered HTML, no build step, no bundler, no `node_modules`. htmx is vendored in `src/cyoa/web/static/js/`, not CDN-loaded
- **SQLite via SQLAlchemy** — one file on a volume, behind a repository layer
- **Markdown + YAML frontmatter** for story files
- **pytest + ruff** — ruff covers lint and format; mypy and a coverage gate are deliberately deferred, see Open questions
- **Docker**, image published to GHCR by CI, deployed with Compose behind Traefik

## Architecture

```
src/cyoa/
├── engine/    Story model, parsers, graph validation, play state.  Pure Python.
├── library/   Discovers stories on disk, builds the catalogue.
├── storage/   SQLite behind a repository.  The only SQL in the project.
├── web/       FastAPI routes, Jinja templates, static assets.
├── config.py  Environment-driven settings (CYOA_ prefix).
└── main.py    Composition root — exposes create_app(), no module-level app.
```

**One rule governs the layout: the engine is a pure library, everything else is an adapter over it.** `engine/` imports no web framework and no database driver, and does not know they exist. Dependencies point inward — `web`, `storage`, and `library` may import from `engine`; never the reverse.

This is what keeps the roadmap additive rather than a series of rewrites:

| Roadmap item | What it costs |
|---|---|
| Twee story format | A new parser class in `engine/` |
| CLI or SSH client | A second adapter beside `web/` |
| LLM story generation | A provider behind the loader interface `library/` already uses |
| Multiplayer | Sessions already carry a participant list |
| Move to PostgreSQL | A connection string and a migration, contained to `storage/` |

If a change to one of those forces edits across three packages, the boundary has eroded. Stop and fix it rather than pushing through.

Two patterns are load-bearing:

- **Parser boundary.** Story formats are `StoryParser` implementations. Only parsers see raw file syntax.
- **Repository.** Repositories speak engine types. `PlaySessionRow` never leaves `storage/`.

## Constraints (non-negotiable)

1. **Never `eval` story content.** When passages eventually get conditions (`if has_lantern`), the lazy implementation is `eval()` — which makes any story file someone hands you a remote-code-execution vector. Write a small expression evaluator or a restricted rule syntax instead. There is no deadline that justifies breaking this one.
2. **v1 makes zero outbound network calls.** The book plays offline. The LLM provider is the only thing that ever changes this, and it stays optional and off by default.
3. **Single container, no required companions.** Someone should be able to `docker run` the image and get a book — no database server, no sidecar, no setup step. The example story ships in the image for exactly this reason.
4. **Nothing outside the parser layer touches story-file syntax.** No route, template, or repository gets its own `[[...]]` regex. The moment this leaks, the story format stops being a decision that can be revisited.
5. **No secrets in the repo.** API keys and credentials come from the environment. `.env` is gitignored; `.env.example` carries names and never values.

## Code style

- Python defaults, enforced by ruff — PEP 8, `snake_case`, sorted imports. Line length 100.
- **Type hints on public functions and methods.** mypy is not enabled yet; annotating as we go is what keeps turning it on a config change rather than a refactor.
- **Docstrings on public functions, classes, and modules.** Say *why*, not just *what* — the what is usually readable from the signature. The interesting comments in this codebase explain a decision, not a mechanism.
- Passage ids and story slugs are lowercase with hyphens or underscores, so they are URL-safe without escaping.
- Story files live at `stories/{slug}/story.md`.
- **Tests that need a story on disk build it in `tmp_path`, not in `tests/fixtures/stories/`.** The shared fixture directory is the library `test_web.py` renders, and the library lists unparseable stories rather than hiding them — so a deliberately broken fixture added there turns up in an unrelated test's assertions. `tests/fixtures/stories/` stays the shape the web tests expect.

## Current state

### Done

- Repo scaffolded from template; `foundation.md` and `CLAUDE.md` written
- Package structure with the engine/adapter boundary established
- Story format designed and specified (`docs/specs/spec-story-format.md`)
- Root tooling: `pyproject.toml`, `Dockerfile`, `compose.yaml` with Traefik labels, `compose.local.yaml` for local runs, `.env.example`
- CI (lint, format, test) and GHCR publishing, with publish gated on CI
- **The engine is complete and green** — 35 passing tests across four modules:
  - `engine/models.py` — the internal story model
  - `engine/markdown_parser.py` — frontmatter, passages, choices, tags
  - `engine/graph.py` — `validate_story` and `reachable_from`
  - `engine/state.py` — `begin` and `advance`, immutable transitions

  Verified end to end against `stories/example/story.md`, which no test uses: 5 passages, all reachable, zero validation issues, walks to an ending.

- **The adapters are complete and green** — 42 passing tests, no `xfail` left in the suite:
  - `library/loader.py` — discovery, parser dispatch, catalogue; a broken story lists as `is_playable=False` rather than vanishing
  - `storage/` — engine construction, `create_all` schema, `PlaySessionRepository`
  - `web/routes.py` + `main.create_app` — the five routes, rendered through Jinja and htmx

  Verified end to end against `stories/example/story.md` through a real uvicorn boot: the library lists it, a reader walks it to an ending, progress survives across requests, and restart returns to the start passage.

- **Every package has unit tests of its own** — 99 passing tests. `library/` and `storage/` were previously covered only through `test_web.py`; `tests/test_library.py` and `tests/test_storage.py` now test them directly, at the same behaviour-level as `test_state.py`. Between them they pin down the things the web layer only reaches by accident: slug validation as the barrier between a URL segment and the filesystem, dispatch to a second parser by extension, the catalogue being re-read per call, and UTC being re-attached to timestamps SQLite hands back naive.

- **Documentation reflects the built state.** Every doc in the repo was audited against the code: the template leftovers are gone (`CONTRIBUTING.md` described a stack-agnostic template with no CI; `SECURITY.md` said there was no deployed application; `scripts/README.md` pointed at a `backend/` directory that never existed), the retired `xfail` convention is marked retired rather than described as current, and `docs/ADRs/README.md` now says where the ADRs actually are. `compose.local.yaml` was added because `compose.yaml` publishes no ports and needs a Traefik-owned network, so it cannot run on a development machine. <!-- inherited-docs-ok -->

### In progress

Nothing. v1 reads end to end, and every package is covered.

### Not started

**Roadmap, beyond v1**, in no committed order: a story editor behind an admin login, multiplayer, live LLM story generation at read time, stats/inventory/combat, non-text media.

Sequencing, and the state of the queue between sessions, lives in `roadmap.md`. This file stays the *why*; that one tracks the *what next*.

## Open questions

- **Twee format.** Markdown + frontmatter was chosen for v1, but Twee is an established interactive-fiction standard with a free visual editor (Twine) that could substitute for building one. Revisit after research. The parser boundary is what keeps this cheap — it should stay a new parser class, not a refactor.
- **Multiplayer shape.** `engine/state.py` assumes readers move through one book *together*, sharing a position, because that is the likelier shape and it costs nothing now. Independent per-reader positions would be a schema change. Decide deliberately before building multiplayer, not during.
- **Stats, inventory, combat.** Interesting, undecided, and the thing most likely to turn a narrative engine into an RPG engine. If it happens, see constraint 1 first.
- **Auth for the v2 editor.** App-level admin password (portable for any self-hoster) versus Traefik + Authentik forward auth (matches the existing homelab, less code). Not decided; v1 has no auth at all.
- **mypy.** Deferred, not rejected. Type hints are being written as we go specifically so adoption stays a config change. Turn it on when the engine's shape settles.
- **Coverage gate.** Deferred until there is enough code for a threshold to mean something rather than be arbitrary.

## Decision log

### ADR-001 — Python 3.12 + FastAPI
Python for the graph and parsing work at the heart of the project; FastAPI over Flask because native async, SSE, and websockets are what the multiplayer and LLM-streaming roadmap items need. Choosing Flask would have meant bolt-ons for both.

### ADR-002 — Server-rendered HTML + htmx, no SPA
The product is text. An SPA would add a build pipeline, a second package ecosystem, and a bundler to render prose. htmx gives smooth passage swaps with a vendored 50KB file and no toolchain. Every interaction also works as a plain form post, so the book reads with JavaScript disabled.

### ADR-003 — SQLite behind a repository
One file on a volume, backs up with `cp`, no second container — which is what constraint 3 requires. The repository layer means outgrowing SQLite later is a connection string and a migration, contained to `storage/`.

### ADR-004 — Markdown + YAML frontmatter for stories, parser behind a protocol
Authors are people and LLMs, not programmers. JSON is hostile to hand-authoring; YAML's block scalars make multi-paragraph prose unpleasant. Markdown lets an author write a story rather than a data structure. Parsing sits behind a `StoryParser` protocol so the format stays revisitable — see the Twee open question.

### ADR-005 — Engine as a pure library; web, storage, and library are adapters
The stated point of the project is building the engine. Keeping it free of framework and database imports is what makes the roadmap additive, and what lets the engine be tested without HTTP or SQL. This is the rule that the other decisions lean on.

### ADR-006 — v1 is read-only: no editor, no auth
Stories are hand-edited or LLM-generated files dropped into a directory. An editor means CRUD forms and an auth story, which is the least interesting work available and would delay a playable book. Editor and auth land together, later.

### ADR-007 — GHCR image built in CI, deployed with Compose behind Traefik
Deploys are `docker compose pull && up -d`: no build toolchain on the host, no source checkout in production, and tagged releases become real rollback points. The publish workflow calls CI as a reusable workflow, so an image that could not pass tests is never pushed.

### ADR-008 — Unimplemented modules ship as `xfail(strict=True)` specifications
Tests are written before implementations and marked xfail against `NotImplementedError`. `strict=True` means implementing a function makes its test fail with XPASS until the marker is deleted — scaffolding that cleans itself up instead of rotting into permanently-skipped tests.

*Status: accepted, currently dormant.* It did its job through v1 and no `xfail` markers remain in the suite. Reach for it again the next time a package is built from an empty file; note that it only applies to code written before its implementation, so tests added to a package that already works need a different way to earn trust (see `tests/README.md`).

### ADR-009 — Validation reports warnings even when errors are present
`validate_story` does not suppress warnings on a story that already has errors, even though a dangling link makes reachability noisier — an orphan caused by a broken link is reported as both. Suppressing would mean an author fixes the errors, re-runs, and only then learns what else is wrong, which is the one-problem-per-run loop the function exists to avoid. Callers that want only blocking problems filter on `Severity.ERROR`.

### ADR-010 — A reader's place lives in a cookie pointing at a database row
The cookie holds a play-session id and nothing else; the session itself is a row. Putting the position in the cookie would have avoided the database entirely, but it freezes a story into a browser — an edited passage would not reach a reader mid-book, and the "drop a file in and it plays" metric runs straight through that. The cookie is per story, so two books in progress do not evict each other, and the reader id it carries is the `participants` entry the multiplayer shape already expects.

---

*Last updated: 2026-09-18 | Session: unit tests for `library/` and `storage/`; `roadmap.md` introduced as the cross-session work queue; full documentation audit against the built state*
