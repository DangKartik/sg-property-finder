"""Town mapping module."""

from __future__ import annotations

class TownMapping:
    """Stereotype: Container. Container resolving URA planning areas to their HDB town pricing keys."""
    mapping: dict[str, str]

    def __init__(self, mapping: dict[str, str]) -> None:
        """Initialise the TownMapping with its dependencies.

        Args:
            mapping: dict[str, str]

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def resolveTown(self, planningAreaName: str) -> str | None:
        """Return the HDB town for a planning area, or None when no proxy exists.

        Args:
            planningAreaName: str

        Returns:
            str | None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
