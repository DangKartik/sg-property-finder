"""House pricing retrieval control module."""

from __future__ import annotations
from typing import TYPE_CHECKING
from app.control.retrieval_control import RetrievalControl
if TYPE_CHECKING:
    from app.entity.house_pricing import HousePricing
    from app.entity.types import RawResponse, RetrievalResult

class HousePricingRetrievalControl(RetrievalControl):
    """Stereotype: Control. Control that retrieves and parses HDB resale pricing by flat type."""

    def retrieveHousePricing(self, subzoneCode: str, flatTypes: list[str] | None=None) -> RetrievalResult[dict[str, HousePricing]]:
        """Return pricing keyed by flat type; use the town proxy and warnings when needed.

        Args:
            subzoneCode: str
            flatTypes: list[str] | None

        Returns:
            RetrievalResult[dict[str, HousePricing]].

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def fetchData(self, resourceId: str) -> RawResponse:
        """Fetch data; surface failures to the caller.

        Args:
            resourceId: str

        Returns:
            RawResponse.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    def parseResponse(self, data: RawResponse) -> dict[str, HousePricing]:
        """Parse response into domain objects.

        Args:
            data: RawResponse

        Returns:
            dict[str, HousePricing].

        Failure handling:
            Not applicable at the skeleton level."""
        ...
