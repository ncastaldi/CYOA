"""HTTP routes — a thin adapter over the engine.

Routes do three things: turn a request into engine calls, turn the result into
a template context, and pick a template. They contain no story logic. If a
route starts deciding what a valid move is, that decision belongs in
`cyoa.engine.state` instead.

Route table
-----------
    GET  /                      library index — every story found on disk
    GET  /healthz               liveness probe for compose and Traefik
    GET  /s/{slug}              start or resume a story
    POST /s/{slug}/choose       take a choice; returns the passage partial
    POST /s/{slug}/restart      discard progress and begin again

htmx swaps the passage partial in place, so `/choose` returns
`partials/passage.html` for an htmx request and a full page otherwise. Keeping
both paths working means the book is readable with JavaScript disabled, and
means a passage URL can be linked to.

Where a reader is, is kept in a cookie holding a play-session id; the session
itself lives in the database. Nothing about the story is stored in the cookie,
so an edited story file takes effect on the next request rather than being
frozen into a browser.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from markdown_it import MarkdownIt

from cyoa.engine.models import Passage, Story
from cyoa.engine.parser import StoryParseError
from cyoa.engine.state import PlaySession, advance, begin
from cyoa.library import StoryLibrary, StoryNotFoundError
from cyoa.storage import PlaySessionRepository, session_scope

router = APIRouter()

#: Identifies the reader across requests, so a session can name its
#: participants. Anonymous and per-browser in v1; an authenticated user id can
#: take its place without the engine noticing.
READER_COOKIE = "cyoa_reader"

#: Prose rendering only. Passage *structure* — headings, `[[choice->target]]`,
#: tags — is the parser's business and has already been resolved into the
#: `Passage` model by the time a route sees one; what is left in `body` is an
#: author's prose. `html=False` escapes any raw HTML in a story file rather
#: than trusting content that may have been generated or handed to us.
_MARKDOWN = MarkdownIt("commonmark", {"html": False})


def _session_cookie(slug: str) -> str:
    """Name of the cookie holding the play-session id for one story.

    Per story rather than one global cookie: a reader part-way through two
    books should not lose their place in one by opening the other.
    """
    return f"cyoa_session_{slug}"


def get_library(request: Request) -> StoryLibrary:
    """The story library built at startup."""
    return request.app.state.library


def get_repository(request: Request) -> Iterator[PlaySessionRepository]:
    """Yield a repository bound to a transaction that lasts for this request."""
    with session_scope(request.app.state.db_engine) as db:
        yield PlaySessionRepository(db)


LibraryDep = Annotated[StoryLibrary, Depends(get_library)]
RepositoryDep = Annotated[PlaySessionRepository, Depends(get_repository)]


def _load_story(library: StoryLibrary, slug: str) -> Story:
    """Load a story, translating library failures into HTTP ones.

    This is the one place a `StoryNotFoundError` becomes a 404 — the library
    and the engine stay free of HTTP concepts.
    """
    try:
        return library.load(slug)
    except StoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"No story named {slug!r}.") from exc
    except StoryParseError as exc:
        raise HTTPException(
            status_code=500, detail=f"Story {slug!r} is on disk but could not be read."
        ) from exc


def _reader_id(request: Request) -> str:
    """Return this browser's reader id, minting one if it has none yet."""
    return request.cookies.get(READER_COOKIE) or str(uuid.uuid4())


def _resume_or_begin(
    request: Request,
    story: Story,
    repository: PlaySessionRepository,
) -> PlaySession:
    """Return the reader's session for this story, starting one if needed.

    A stored session whose passage no longer exists is replaced rather than
    repaired: story files are re-read from disk on every request, so a renamed
    passage can legitimately strand a reader mid-book. Beginning again is the
    only move that leaves them somewhere readable.
    """
    session_id = request.cookies.get(_session_cookie(story.slug))
    if session_id:
        existing = repository.get(session_id)
        if (
            existing is not None
            and existing.story_slug == story.slug
            and story.passage(existing.current_passage_id) is not None
        ):
            return existing

    session = begin(story, [_reader_id(request)], session_id=str(uuid.uuid4()))
    repository.save(session)
    return session


def _current_passage(session: PlaySession, story: Story) -> Passage:
    """The passage a session is sitting on."""
    passage = story.passage(session.current_passage_id)
    if passage is None:
        raise HTTPException(status_code=500, detail=f"Story {story.slug!r} has no passage to show.")
    return passage


def _render_passage(
    request: Request,
    story: Story,
    session: PlaySession,
    *,
    partial: bool,
) -> Response:
    """Render a passage as either the htmx partial or the whole page.

    Both paths render the same partial, which is what keeps the JavaScript-free
    reading experience identical to the swapped one.
    """
    passage = _current_passage(session, story)
    templates = request.app.state.templates
    response = templates.TemplateResponse(
        request,
        "partials/passage.html" if partial else "passage.html",
        {
            "story": story,
            "passage": passage,
            "passage_html": _MARKDOWN.render(passage.body),
            "session": session,
        },
    )
    _remember(response, request, story.slug, session)
    return response


def _remember(response: Response, request: Request, slug: str, session: PlaySession) -> None:
    """Pin the reader and their place in this story to the browser."""
    response.set_cookie(
        _session_cookie(slug),
        session.id,
        httponly=True,
        samesite="lax",
    )
    if request.cookies.get(READER_COOKIE) != session.participants[0]:
        response.set_cookie(
            READER_COOKIE,
            session.participants[0],
            httponly=True,
            samesite="lax",
        )


def _is_htmx(request: Request) -> bool:
    """True when htmx issued this request and expects a fragment back."""
    return request.headers.get("hx-request") == "true"


@router.get("/healthz", name="healthz")
def healthz() -> dict[str, str]:
    """Liveness probe. Deliberately touches neither disk nor database."""
    return {"status": "ok"}


@router.get("/", response_class=HTMLResponse, name="library_index")
def library_index(request: Request, library: LibraryDep) -> Response:
    """The shelf: every story found on disk, re-read on each request."""
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "library.html", {"stories": library.list_stories()})


@router.get("/s/{slug}", response_class=HTMLResponse, name="read_story")
def read_story(
    request: Request,
    slug: str,
    library: LibraryDep,
    repository: RepositoryDep,
) -> Response:
    """Start a story, or pick it back up where the reader left off."""
    story = _load_story(library, slug)
    session = _resume_or_begin(request, story, repository)
    return _render_passage(request, story, session, partial=False)


@router.post("/s/{slug}/choose", response_class=HTMLResponse, name="choose")
def choose(
    request: Request,
    slug: str,
    library: LibraryDep,
    repository: RepositoryDep,
    choice_index: Annotated[int, Form()],
) -> Response:
    """Take a branch out of the current passage.

    The engine decides whether the move is legal; this route only translates
    its refusal into a 400.
    """
    story = _load_story(library, slug)
    session = _resume_or_begin(request, story, repository)

    try:
        moved = advance(session, story, choice_index)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository.save(moved)
    return _render_passage(request, story, moved, partial=_is_htmx(request))


@router.post("/s/{slug}/restart", response_class=HTMLResponse, name="restart_story")
def restart_story(
    request: Request,
    slug: str,
    library: LibraryDep,
    repository: RepositoryDep,
) -> Response:
    """Throw away progress and open the story at its first passage again."""
    story = _load_story(library, slug)

    previous = request.cookies.get(_session_cookie(slug))
    if previous:
        repository.delete(previous)

    session = begin(story, [_reader_id(request)], session_id=str(uuid.uuid4()))
    repository.save(session)
    return _render_passage(request, story, session, partial=_is_htmx(request))
