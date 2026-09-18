"""Application entry point.

Wires the adapters around the engine: settings, database, story library, and
the HTTP routes. This is the only module that knows about all of them at once;
that is the whole job of a composition root.

Exposed as a factory rather than a module-level `app`, so importing this module
has no side effects — tests can import it, and uvicorn is pointed at the
factory instead:

    uvicorn --factory cyoa.main:create_app --reload
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cyoa.config import get_settings
from cyoa.engine.markdown_parser import MarkdownStoryParser
from cyoa.library import StoryLibrary
from cyoa.storage import create_engine_for, create_schema
from cyoa.web import router

_WEB = Path(__file__).parent / "web"


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Mounts static files, registers routes, and ensures the database schema
    exists. Taking no arguments and reading `get_settings()` keeps the uvicorn
    factory signature simple; tests override the settings dependency rather
    than passing configuration in here.
    """
    settings = get_settings()

    app = FastAPI(title=settings.site_name)

    db_engine = create_engine_for(settings.db_path)
    create_schema(db_engine)

    templates = Jinja2Templates(directory=_WEB / "templates")
    # Every page shows it, no page varies it — a global beats threading it
    # through the context of each individual render.
    templates.env.globals["site_name"] = settings.site_name

    # The library is constructed once but reads the directory on every call, so
    # a story dropped into the volume appears without a restart.
    app.state.settings = settings
    app.state.db_engine = db_engine
    app.state.templates = templates
    app.state.library = StoryLibrary(settings.stories_dir, [MarkdownStoryParser()])

    app.mount("/static", StaticFiles(directory=_WEB / "static"), name="static")
    app.include_router(router)

    return app
