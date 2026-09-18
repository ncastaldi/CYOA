# Tests

pytest, run with `pytest` from the repo root.

## Layout

```
tests/
├── conftest.py              Shared fixtures
├── test_models.py           The internal story model
├── test_parser.py           Markdown + frontmatter parsing
├── test_graph.py            Graph validation and reachability
├── test_web.py              HTTP behaviour
└── fixtures/stories/tiny/   The story the suite is written against
```

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

### The xfail convention

Most of the engine is not implemented yet. Its tests are written anyway — they are the specification — and marked at module level:

```python
pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason="... — delete this marker when it is",
)
```

Three things make this work:

- `raises=NotImplementedError` means a test failing for any *other* reason is a real failure, not a silently tolerated one.
- `strict=True` means the moment you implement the function, the passing test **fails** with XPASS — telling you to delete the marker. Scaffolding that cleans itself up rather than rotting into permanently-skipped tests.
- Anything that would raise during **fixture setup** must be called from the test body instead. `xfail` only covers the call phase; an exception in a fixture is reported as an error and turns CI red regardless of the marker. See `_client()` in `test_web.py`.

When you implement a module, delete its `pytestmark` block and watch the tests go green for real.
