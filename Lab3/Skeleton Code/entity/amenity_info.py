from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.types import Coordinates


class AmenityInfo:
    """«entity» One amenity (school, hospital, park, mall...) located in a subzone."""

    amenityId: str  # private
    category: str  # private
    name: str  # private
    location: Coordinates  # private

    def __init__(self, amenityId: str, category: str, name: str, location: Coordinates) -> None:
        """Create a AmenityInfo with its attributes (TODO: add validation if needed)."""
        self.amenityId = amenityId
        self.category = category
        self.name = name
        self.location = location

    def getCategory(self) -> str:
        """Get category (public).

        Returns:
            str
        """
        raise NotImplementedError  # TODO

    def getName(self) -> str:
        """Get name (public).

        Returns:
            str
        """
        raise NotImplementedError  # TODO
