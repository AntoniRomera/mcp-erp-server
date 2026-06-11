"""Configuration loading.

Settings come from (lowest to highest precedence):
    defaults  <  .env file  <  environment variables  <  CLI overrides

The CLI layer (``__main__.py``) builds a partial dict of explicitly-passed
flags and calls :func:`build_settings` to merge them on top of the env/.env
layer that pydantic-settings resolves automatically.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server configuration resolved from env vars and an optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Allow constructing Settings(**fields) by field name (e.g. build_settings
        # and tests pass `backend_url=`/`demo=`), not only by the env-var alias.
        populate_by_name=True,
    )

    backend_url: str = Field(
        default="http://localhost:8069",
        description="Demo / JSON-RPC endpoint used in live mode.",
        validation_alias="BACKEND_URL",
    )
    readonly: bool = Field(
        default=True,
        description="Restrict the server to allowlisted read-only operations.",
        validation_alias="READONLY",
    )
    demo: bool = Field(
        default=False,
        description="Serve the bundled sample dataset with no network access.",
        validation_alias="DEMO",
    )

    # Optional authentication (absent in demo mode).
    backend_api_key: str | None = Field(default=None, validation_alias="BACKEND_API_KEY")
    backend_username: str | None = Field(default=None, validation_alias="BACKEND_USERNAME")
    backend_password: str | None = Field(default=None, validation_alias="BACKEND_PASSWORD")
    backend_database: str | None = Field(default=None, validation_alias="BACKEND_DATABASE")

    # Network timeout (seconds) for the JSON-RPC adapter.
    request_timeout: float = Field(default=30.0, validation_alias="REQUEST_TIMEOUT")


def build_settings(cli_overrides: dict[str, Any] | None = None) -> Settings:
    """Build :class:`Settings`, applying explicit CLI overrides last.

    ``cli_overrides`` should contain only flags the user actually passed, so
    that unset flags fall through to env / .env / defaults.
    """
    base = Settings()
    if not cli_overrides:
        return base
    merged = base.model_dump()
    merged.update({k: v for k, v in cli_overrides.items() if v is not None})
    return Settings(**merged)
