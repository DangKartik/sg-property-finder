from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from control.neighborhood_details_control import NeighborhoodDetailsControl


class FactSheetUI:
    """«boundary» Fact sheet with amenities, pricing, environment and commute details of one subzone."""

    detailsControl: NeighborhoodDetailsControl  # private

    def __init__(self, detailsControl: NeighborhoodDetailsControl) -> None:
        """Create a FactSheetUI with its attributes (TODO: add validation if needed)."""
        self.detailsControl = detailsControl

    def displaySubzoneDetails(self, subzoneId: str) -> None:
        """Display subzone details (public).

        Args:
            subzoneId: str
        """
        raise NotImplementedError  # TODO
