from __future__ import annotations

from control.retrieval_control import RetrievalControl

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.amenity_info import AmenityInfo
    from entity.types import RawResponse


class EnvironmentalRetrievalControl(RetrievalControl):
    """«control» Retrieves and parses environmental data for a subzone."""

    def parseResponse(self, data: RawResponse) -> list[AmenityInfo]:
        """Parse response (protected).

        Args:
            data: RawResponse
        Returns:
            list[AmenityInfo]
        Note: Diagram shows List<AmenityInfo> here; EnvironmentInfo is probably intended.
        """
        raise NotImplementedError  # TODO

    def fetchEnvironmentForSubzone(self, subzoneId: str) -> list[AmenityInfo]:
        """Fetch environment for subzone (public).

        Args:
            subzoneId: str
        Returns:
            list[AmenityInfo]
        Note: Diagram shows List<AmenityInfo> here; EnvironmentInfo is probably intended.
        """
        raise NotImplementedError  # TODO
