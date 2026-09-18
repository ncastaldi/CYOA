# API Documentation

This folder contains hand-written API documentation, integration guides, and reference material for the project's APIs.

**CYOA serves its own generated docs while running:** FastAPI publishes Swagger UI at `/docs`, ReDoc at `/redoc`, and the OpenAPI schema at `/openapi.json`. Those are always current, so nothing here should restate a route's shape — what belongs here is the documentation an auto-generator cannot produce: context, intent, and integration guidance.

Worth knowing before reading them: **CYOA is not an API-first application.** It is a server-rendered site (ADR-002), so every route below returns HTML rather than JSON, and the OpenAPI schema describes them accordingly. The only JSON endpoint is the health probe.

| Route | Returns | Purpose |
|---|---|---|
| `GET /` | HTML | The library index — every story found on disk, re-read per request |
| `GET /healthz` | JSON | Liveness probe for Compose and Traefik. Touches neither disk nor database |
| `GET /s/{slug}` | HTML | Start or resume a story |
| `POST /s/{slug}/choose` | HTML | Take a choice. Returns the passage partial to htmx, a full page otherwise |
| `POST /s/{slug}/restart` | HTML | Discard progress and begin again |

`/choose` and `/restart` are real form posts, not JSON APIs — every interaction works with JavaScript disabled, and htmx is an enhancement over that rather than a requirement. A reader's position lives in a per-story cookie holding a play-session id; the session itself is a database row (ADR-010).

## What belongs here

- Endpoint guides that explain the "why" behind API design choices
- Authentication and authorization flow documentation
- Integration guides for external consumers of this API
- Postman collections or Bruno request files
- Versioning and deprecation policy
- Rate limiting and error code reference

## What does not belong here

- Auto-generated OpenAPI/Swagger specs (those are served live by the framework, if it produces them)
- Architecture decisions about the API design (those go in docs/ADRs/)
- Deployment or infrastructure docs (those go in docs/SOPs/)
