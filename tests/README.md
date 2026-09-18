# Tests

pytest, run with `pytest` from the repo root.

## Layout

```
tests/
├── conftest.py              Shared fixtures
├── test_models.py           The internal story model
├── test_parser.py           Markdown + frontmatter parsing
├── test_graph.py            Graph validation and reachability
├── test_state.py            Play state and passage transitions
├── test_library.py          Story discovery, the catalogue, parser dispatch
├── test_storage.py          Engine, schema, repository round trip
├── test_web.py              HTTP behaviour
└── fixtures/stories/tiny/   The story the suite is written against
```

99 tests, all green.

## What belongs here

- Unit tests for the engine — parsing, graph validation, state transitions
- HTTP-level tests exercising real routes through FastAPI's `TestClient`
- Story fixtures the suite asserts against

## What does not belong here

- Story content meant for readers (that goes in `stories/`)
- Dev-time utilities (those go in `scripts/`)

## Conventions

**Tests use `fixtures/stories/`, never `stories/`.** The example story at the repo root is *content* — someone should be able to rewrite or delete it without breaking the suite.

**Graph and state tests build stories by hand.** The `tiny_story` fixture constructs a `Story` directly rather than parsing one, so a parser bug fails the parser tests instead of every test in the suite.

**Assert on what a reader can observe.** Web tests check that a story is listed, that a choice moves you, that a missing story 404s — not which template rendered or what the markup nests. Rendering should be free to change; the reading experience should not.

**Tests that need a story on disk build it in `tmp_path`.** Not in `fixtures/stories/` — the library deliberately *lists* stories it cannot parse rather than hiding them, so a broken fixture added to the shared directory turns up in the library index `test_web.py` asserts against. Writing the directory inside the test also means the test states its own situation instead of pointing at one three directories away. `test_library.py` does this throughout.

**A test written against existing code has to be shown to fail.** The engine's tests were written before their implementations, so red-green did the work. `test_library.py` and `test_storage.py` were not: they describe code that already worked, and every one passed on its first run — which is exactly when a test proves nothing. Each was checked against a deliberately broken copy of the code it covers before being committed. If you add tests to a package that already works, do the same; a test that has never failed is a test you have no reason to trust.

### The xfail convention (retired)

Unimplemented modules used to ship as `pytest.mark.xfail(raises=NotImplementedError, strict=True)` specifications — tests written first, with `strict=True` so that implementing a function turned its test into an XPASS failure demanding the marker be deleted. Scaffolding that cleaned itself up instead of rotting into permanently-skipped tests.

It worked, and it is done: every module is implemented and **no `xfail` markers remain in the suite**. The convention is recorded in ADR-008 and kept here because it is worth reaching for again the next time a package gets built from an empty file — not because there is anything currently marked.
