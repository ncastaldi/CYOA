"""Specification for the HTTP layer.

These tests deliberately assert on *behaviour a reader can observe* (a story
is listed, a choice moves you, a missing story 404s) rather than on template
internals. The rendering should be free to change; the reading experience
should not.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cyoa.main import create_app


@pytest.fixture
def client() -> TestClient:
    """A client over a freshly built app.

    One app per test, so a reader's cookies and their stored progress never
    leak from one scenario into the next.
    """
    return TestClient(create_app())


def test_healthz_reports_ok(client: TestClient) -> None:
    assert client.get("/healthz").status_code == 200


def test_library_index_lists_available_stories(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Tiny" in response.text


def test_reading_a_story_starts_at_its_start_passage(client: TestClient) -> None:
    response = client.get("/s/tiny")

    assert response.status_code == 200
    assert "A door, and a window." in response.text


def test_unknown_story_is_a_404(client: TestClient) -> None:
    assert client.get("/s/no-such-story").status_code == 404


def test_choosing_moves_the_reader_to_the_target_passage(client: TestClient) -> None:
    client.get("/s/tiny")

    response = client.post("/s/tiny/choose", data={"choice_index": "0"})

    assert response.status_code == 200
    assert "It was locked all along." in response.text


def test_choice_index_out_of_range_is_rejected(client: TestClient) -> None:
    client.get("/s/tiny")

    assert client.post("/s/tiny/choose", data={"choice_index": "99"}).status_code == 400


def test_the_book_is_readable_without_javascript(client: TestClient) -> None:
    """Each choice is a real form post to a real URL, not only an htmx swap."""
    client.get("/s/tiny")

    response = client.post("/s/tiny/choose", data={"choice_index": "0"}, follow_redirects=True)

    assert response.status_code == 200
    assert "<form" in response.text
