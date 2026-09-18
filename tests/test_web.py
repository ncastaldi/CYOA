"""Specification for the HTTP layer.

Not implemented yet — see `tests/README.md` for the xfail convention.

These tests deliberately assert on *behaviour a reader can observe* (a story
is listed, a choice moves you, a missing story 404s) rather than on template
internals. The rendering should be free to change; the reading experience
should not.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cyoa.main import create_app

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason="web layer not implemented — delete this marker when it is",
)


def _client() -> TestClient:
    """Build a client inside the test body, not in a fixture.

    `xfail` only covers exceptions raised during the call phase; one raised in
    fixture setup is reported as an error and would turn CI red. Once
    `create_app` is implemented, this becomes an ordinary fixture.
    """
    return TestClient(create_app())


def test_healthz_reports_ok() -> None:
    assert _client().get("/healthz").status_code == 200


def test_library_index_lists_available_stories() -> None:
    response = _client().get("/")

    assert response.status_code == 200
    assert "Tiny" in response.text


def test_reading_a_story_starts_at_its_start_passage() -> None:
    response = _client().get("/s/tiny")

    assert response.status_code == 200
    assert "A door, and a window." in response.text


def test_unknown_story_is_a_404() -> None:
    assert _client().get("/s/no-such-story").status_code == 404


def test_choosing_moves_the_reader_to_the_target_passage() -> None:
    client = _client()
    client.get("/s/tiny")

    response = client.post("/s/tiny/choose", data={"choice_index": "0"})

    assert response.status_code == 200
    assert "It was locked all along." in response.text


def test_choice_index_out_of_range_is_rejected() -> None:
    client = _client()
    client.get("/s/tiny")

    assert client.post("/s/tiny/choose", data={"choice_index": "99"}).status_code == 400


def test_the_book_is_readable_without_javascript() -> None:
    """Each choice is a real form post to a real URL, not only an htmx swap."""
    client = _client()
    client.get("/s/tiny")

    response = client.post("/s/tiny/choose", data={"choice_index": "0"}, follow_redirects=True)

    assert response.status_code == 200
    assert "<form" in response.text
