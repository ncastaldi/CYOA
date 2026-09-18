# Engine

The story engine — the part this project exists to build. It turns story files into a validated graph of passages and moves readers through it.

This package is pure Python. It imports no web framework, no database driver, and no HTTP client, and it has no idea any of those exist. Everything else in CYOA is an adapter over this package.

## What belongs here

- The internal story model (`models.py`) — `Story`, `Passage`, `Choice`
- Parsers translating a source format into that model (`parser.py`, `markdown_parser.py`)
- Graph analysis and validation (`graph.py`) — dangling targets, unreachable passages, dead ends
- Play state and the transitions between passages (`state.py`)

## What does not belong here

- FastAPI routes, request objects, or template rendering (those go in `../web/`)
- SQL, SQLAlchemy models, or anything that persists (those go in `../storage/`)
- Filesystem scanning and story discovery (that goes in `../library/`)
- Calls to external APIs, including LLM providers

If something here needs to import from `cyoa.web` or `cyoa.storage`, the dependency is backwards — the adapter should be calling in, not the other way around.

## Conventions

**The parser boundary is absolute.** Only parsers in this package may look at raw story-file syntax. No route, template, loader, or repository gets to run its own `[[...]]` regex. This is the rule that keeps the on-disk format swappable — the moment it leaks, adding Twee support stops being a new class and becomes a refactor.

**Validation reports, parsing raises.** A file that cannot become a `Story` at all raises `StoryParseError`. A story that parses but has graph problems returns issues from `validate_story` — all of them, in one pass. Authors should see every problem at once, not one per run.

**State transitions are pure and immutable.** `advance()` returns a new `PlaySession` rather than mutating one. Undo, replay, and an editor's "what if" preview then cost nothing extra.

**Position belongs to the session, not the reader.** See the multiplayer note in `state.py` — this is a deliberate assumption with a known limit, not an accident.
