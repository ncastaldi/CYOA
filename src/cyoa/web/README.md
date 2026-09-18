# Web

The HTTP adapter — FastAPI routes, Jinja2 templates, and static assets. Server-rendered HTML enhanced with htmx. No build step, no bundler, no `node_modules`.

## What belongs here

- Route handlers (`routes.py`)
- Jinja2 templates (`templates/`) and their htmx partials (`templates/partials/`)
- CSS and vendored JavaScript (`static/`)

## What does not belong here

- Story parsing or anything that reads story-file syntax (that goes in `../engine/`)
- Rules about what a valid move is (that goes in `../engine/state.py`)
- SQL or SQLAlchemy (that goes in `../storage/`)

## Conventions

**Routes call the engine; they never reimplement it.** A handler resolves the request, asks the engine, and renders. When a handler starts branching on story content, the logic has landed in the wrong package.

**Every interaction works without JavaScript.** htmx swaps the passage partial in place for a smoother read, but each choice is also a real form post to a real URL that returns a real page. A passage should be linkable and a book readable with scripting off — this is a text medium, and degrading gracefully costs almost nothing here.

**Partials are templates, not fragments of one.** A handler returns `partials/passage.html` for an htmx request and the full page otherwise, with both including the same partial. Never build HTML by string concatenation in a route.

**Assets are vendored, not fetched.** htmx is committed to `static/js/`, not pulled from a CDN at page load. The app must work on a homelab with no outbound internet, and a story should not stop rendering because someone else's CDN is down.

**The app does not assume it owns the origin.** Traefik terminates TLS and may mount this app anywhere. Generate URLs with `url_for`; never hardcode a scheme, host, or leading path.
