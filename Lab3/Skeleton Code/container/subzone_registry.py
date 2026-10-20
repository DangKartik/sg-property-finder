from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.subzone import Subzone


class SubzoneRegistry:
    """«container» Holds all subzones loaded from the external datasets."""

    subzones: dict[str, Subzone]  # private

    def __init__(self, subzones: dict[str, Subzone]) -> None:
        """Create a SubzoneRegistry with its attributes (TODO: add validation if needed)."""
        self.subzones = subzones

    def getSubzone(self, id: str) -> Subzone:
        """Get subzone (public).

        Args:
            id: str
        Returns:
            Subzone
        """
        raise NotImplementedError  # TODO

    def getAllSubzones(self) -> list[Subzone]:
        """Get all subzones (public).

        Returns:
            list[Subzone]
        """
        raise NotImplementedError  # TODO

    def loadSubzones(self, data: list[Subzone]) -> None:
        """Load subzones (public).

        Args:
            data: list[Subzone]
        """
        raise NotImplementedError  # TODO
