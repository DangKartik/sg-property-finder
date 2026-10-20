from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from control.retrieval_control import RetrievalControl
    from entity.types import FactSheetData


class NeighborhoodDetailsControl:
    """«control» Collects amenity, environment and pricing data into one fact sheet."""

    amenityRetrieval: RetrievalControl  # private
    envRetrieval: RetrievalControl  # private
    priceRetrieval: RetrievalControl  # private

    def __init__(self, amenityRetrieval: RetrievalControl, envRetrieval: RetrievalControl, priceRetrieval: RetrievalControl) -> None:
        """Create a NeighborhoodDetailsControl with its attributes (TODO: add validation if needed)."""
        self.amenityRetrieval = amenityRetrieval
        self.envRetrieval = envRetrieval
        self.priceRetrieval = priceRetrieval

    def getFullFactSheet(self, subzoneId: str) -> FactSheetData:
        """Get full fact sheet (public).

        Args:
            subzoneId: str
        Returns:
            FactSheetData
        """
        raise NotImplementedError  # TODO
