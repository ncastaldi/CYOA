"""Shared fixtures.

Tests run against the fixture stories in `fixtures/stories/`, never against
`stories/` at the repo root — the example story there is content and may be
edited or replaced without anyone expecting the suite to care.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from cyoa.config import get_settings
from cyoa.engine.models import Choice, Passage, Story

FIXTURE_STORIES = Path(__file__).parent / "fixtures" / "stories"


@pytest.fixture(autouse=True)
def settings_for_tests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point `create_app()` at the fixture stories and a throwaway database.

    Autouse because `create_app` reads `get_settings()` itself rather than
    taking configuration as an argument — the environment is the seam. The
    cache is cleared either side so a test never inherits another's settings,
    and `tmp_path` gives every test a database with no history in it.
    """
    monkeypatch.setenv("CYOA_STORIES_DIR", str(FIXTURE_STORIES))
    monkeypatch.setenv("CYOA_DB_PATH", str(tmp_path / "cyoa.db"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def tiny_source() -> str:
    """The raw Markdown of the `tiny` fixture story."""
    return (FIXTURE_STORIES / "tiny" / "story.md").read_text(encoding="utf-8")


@pytest.fixture
def tiny_story() -> Story:
    """The `tiny` fixture story, built directly rather than parsed.

    Hand-built so that graph and state tests do not depend on the parser
    working. A parser bug should fail parser tests, not every test in the suite.
    """
    return Story(
        slug="tiny",
        title="Tiny",
        author="Test Suite",
        description="The smallest story that still branches, ends, and loops.",
        start="start",
        passages={
            "start": Passage(
                id="start",
                body="A door, and a window.",
                choices=[
                    Choice(text="Open the door", target="door"),
                    Choice(text="Climb out the window", target="window"),
                ],
            ),
            "door": Passage(
                id="door",
                body="It was locked all along.",
                choices=[Choice(text="Try the window instead", target="window")],
            ),
            "window": Passage(
                id="window",
                body="You climb out into the afternoon.",
                tags=["ending"],
            ),
        },
    )
