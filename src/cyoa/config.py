"""Runtime configuration, read from the environment.

Every setting is `CYOA_`-prefixed and has a default that works, so `docker run`
with no environment at all still produces a running app. Secrets are never
read from a file in the repo — see the constraints in `CLAUDE.md`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        stories_dir: Where story files live. Mounted read-only in production.
        db_path: The SQLite file holding reader progress. Mounted read-write.
        site_name: Shown in the header and page titles.
        public_host: The hostname this instance is served at. Used for the
            Traefik router rule in `compose.yaml`; the app itself generates
            relative URLs and does not assume it owns the origin.
        log_level: Standard logging level name.
    """

    model_config = SettingsConfigDict(env_prefix="CYOA_", env_file=".env", extra="ignore")

    stories_dir: Path = Path("stories")
    db_path: Path = Path("data/cyoa.db")
    site_name: str = "CYOA"
    public_host: str = "cyoa.castaldifamily.com"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, read once.

    Cached so that settings are resolved a single time per process. Tests that
    need different values should call `get_settings.cache_clear()` or override
    the FastAPI dependency rather than mutating the returned object.
    """
    return Settings()
