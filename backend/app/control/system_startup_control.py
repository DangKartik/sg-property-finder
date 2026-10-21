"""Application startup control."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.container.subzone_registry import SubzoneRegistry


class SystemStartupControl:
    """Stereotype: Control. Initialises application data and the subzone registry."""

    def __init__(self, subzoneRegistry: SubzoneRegistry) -> None:
        """Store the registry that startup should prepare."""
        self.subzoneRegistry = subzoneRegistry

    def initializeSystem(self) -> None:
        """Prepare the registry for requests.

        Data loading is handled by `bootstrap.buildContext`; this method exists
        as the explicit startup hook and is intentionally idempotent.
        """
        return None

    def main(self, args: list[str]) -> None:
        """Run the optional CLI startup hook."""
        self.initializeSystem()
