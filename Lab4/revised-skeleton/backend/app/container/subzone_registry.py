"""Subzone registry module."""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.subzone import Subzone

class SubzoneRegistry:
    """Stereotype: Container. Container holding the in-memory registry of subzones loaded from data assets."""
    subzones: dict[str, Subzone]

    def __init__(self, subzones: dict[str, Subzone]) -> None:
        """Initialise the SubzoneRegistry with its dependencies.

        Args:
            subzones: dict[str, Subzone]

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def registerSubzone(self, subzone: Subzone) -> None:
        """Register or replace a subzone in the in-memory registry.

        Args:
            subzone: Subzone

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getSubzone(self, subzoneCode: str) -> Subzone:
        """Return a subzone by code; raise if it is not registered.

        Args:
            subzoneCode: str

        Returns:
            Subzone.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getAllSubzones(self) -> list[Subzone]:
        """Return all registered subzones.

        Args:
            None.

        Returns:
            list[Subzone].

        Failure handling:
            Not applicable at the skeleton level."""
        ...
