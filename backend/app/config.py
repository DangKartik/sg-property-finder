"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    """Stereotype: configuration. Runtime settings sourced from `.env`.

    The class keeps secrets out of source control and never logs their values.
    `fromEnv()` loads `SGPropertyFinder/.env` without overriding variables
    already present in the process environment.
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
    DATA_MAX_AGE_HOURS: int = 24

    @staticmethod
    def _loadEnvFile(path: Path) -> None:
        """Load a `.env` file without overriding existing environment variables.

        Args:
            path: Path to the `.env` file.

        Returns:
            None.

        Failure handling:
            Missing files are ignored. Malformed lines are ignored so a bad
            local line cannot prevent the application from starting.
        """
        if not path.exists():
            return

        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)

    @classmethod
    def fromEnv(cls) -> Settings:
        """Load and validate settings from environment variables.

        Returns:
            Settings: Validated runtime settings.

        Failure handling:
            Raise a configuration error when a required non-secret value is
            invalid. Never include secret values in error messages or logs.
        """
        project_root = Path(__file__).resolve().parents[2]
        cls._loadEnvFile(project_root / ".env")

        port_text = os.environ.get("APP_PORT", "8000")
        try:
            port = int(port_text)
        except ValueError as exc:
            raise ValueError("APP_PORT must be an integer") from exc
        try:
            max_age_hours = int(os.environ.get("DATA_MAX_AGE_HOURS", "24"))
        except ValueError as exc:
            raise ValueError("DATA_MAX_AGE_HOURS must be an integer") from exc

        return cls(
            ONEMAP_API_KEY=os.environ.get("ONEMAP_API_KEY") or None,
            ONEMAP_EMAIL=os.environ.get("ONEMAP_EMAIL") or None,
            ONEMAP_PASSWORD=os.environ.get("ONEMAP_PASSWORD") or None,
            ONEMAP_BASE_URL=os.environ.get("ONEMAP_BASE_URL", "https://www.onemap.gov.sg").rstrip("/"),
            DATA_GOV_SG_API_KEY=os.environ.get("DATA_GOV_SG_API_KEY") or None,
            DATA_GOV_SG_BASE_URL=os.environ.get(
                "DATA_GOV_SG_BASE_URL", "https://api-production.data.gov.sg"
            ).rstrip("/"),
            DATA_GOV_SG_REALTIME_BASE_URL=os.environ.get(
                "DATA_GOV_SG_REALTIME_BASE_URL",
                "https://api-open.data.gov.sg/v2/real-time/api",
            ).rstrip("/"),
            APP_ENV=os.environ.get("APP_ENV", "development"),
            APP_HOST=os.environ.get("APP_HOST", "127.0.0.1"),
            APP_PORT=port,
            DATA_MAX_AGE_HOURS=max_age_hours,
        )
