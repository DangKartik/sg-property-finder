from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.types import Coordinates


class DataGovSgAdapter:
    """«adapter» Adapter hiding the data.gov.sg API behind a simple interface; the API key stays private here."""

    apiKey: str  # private
    baseUrl: str  # private

    def __init__(self, apiKey: str, baseUrl: str) -> None:
        """Create a DataGovSgAdapter with its attributes (TODO: add validation if needed)."""
        self.apiKey = apiKey
        self.baseUrl = baseUrl

    def fetchRoute(self, start: Coordinates, end: Coordinates) -> str:
        """Fetch route (public).

        Args:
            start: Coordinates
            end: Coordinates
        Returns:
            str
        Note: Diagram puts fetchRoute on the data.gov.sg adapter (it reads like a OneMap call).
        """
        raise NotImplementedError  # TODO

    def fetchSubzonePolygons(self) -> str:
        """Fetch subzone polygons (public).

        Returns:
            str
        Note: Diagram puts fetchSubzonePolygons on the data.gov.sg adapter.
        """
        raise NotImplementedError  # TODO
