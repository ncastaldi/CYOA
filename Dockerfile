# Build the virtualenv in one stage, ship only its contents in the next, so the
# runtime image carries no compilers, no pip cache, and no build metadata.
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir .


FROM python:3.12-slim

# Unbuffered so container logs appear in `docker logs` as they happen.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    CYOA_STORIES_DIR=/app/stories \
    CYOA_DB_PATH=/app/data/cyoa.db

COPY --from=builder /opt/venv /opt/venv

# Runs as a non-root user. `data` is the only directory the app writes to;
# `stories` is mounted read-only in production, since v1 never edits a story.
RUN useradd --system --create-home --uid 10001 cyoa \
    && mkdir -p /app/stories /app/data \
    && chown -R cyoa:cyoa /app

# The example story ships in the image so that `docker run` with no volumes at
# all still gives the reader a book. A mounted stories volume shadows it.
COPY --chown=cyoa:cyoa stories /app/stories

WORKDIR /app
USER cyoa

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"

# --factory because cyoa.main exposes create_app() rather than a module-level
# app; importing the module has no side effects.
CMD ["uvicorn", "--factory", "cyoa.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
