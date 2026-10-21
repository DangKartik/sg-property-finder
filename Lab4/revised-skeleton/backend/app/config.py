"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Settings:
    """Stereotype: configuration. Runtime settings sourced from `.env`.

    The class keeps secrets out of source control. Phase 2 will implement
    `fromEnv()` with pydantic-settings or python-dotenv and validate required
    values at startup.
    """

    ONEMAP_API_KEY: str | None
    ONEMAP_EMAIL: str | None
    ONEMAP_PASSWORD: str | None
    ONEMAP_BASE_URL: str
    DATA_GOV_SG_API_KEY: str | None
    DATA_GOV_SG_BASE_URL: str
    DATA_GOV_SG_REALTIME_BASE_URL: str
    APP_ENV: str
    APP_HOST: str
    APP_PORT: int

    @classmethod
    def fromEnv(cls) -> Settings:
        """Load and validate settings from environment variables.

        Returns:
            Settings: Validated runtime settings.

        Failure handling:
            Raise a configuration error when required production values are
            missing; never log secret values.
        """
        ...
