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
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
