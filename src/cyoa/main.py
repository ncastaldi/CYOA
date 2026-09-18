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

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Mounts static files, registers routes, and ensures the database schema
    exists. Taking no arguments and reading `get_settings()` keeps the uvicorn
    factory signature simple; tests override the settings dependency rather
    than passing configuration in here.
    """
    raise NotImplementedError
