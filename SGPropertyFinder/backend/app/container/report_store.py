"""Short-lived PDF report store."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


class ReportStore:
    """Stereotype: Container. Maps report IDs to temporary PDF files."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        """Create an empty store.

        Args:
            clock: Optional UTC clock used by expiry checks. Tests inject a
                controllable clock; production uses ``datetime.now``.
        """
        self._reports: dict[str, tuple[Path, datetime]] = {}
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def add(self, reportId: str, path: Path, expiresAt: datetime) -> None:
        """Register a generated report."""
        self._reports[reportId] = (path, expiresAt)

    def getPath(self, reportId: str) -> Path | None:
        """Return a non-expired report path, removing expired entries."""
        entry = self._reports.get(reportId)
        if entry is None:
            return None
        path, expires_at = entry
        if expires_at <= self._clock():
            self._reports.pop(reportId, None)
            path.unlink(missing_ok=True)
            return None
        return path
