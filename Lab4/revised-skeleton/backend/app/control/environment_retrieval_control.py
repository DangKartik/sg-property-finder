"""Environment retrieval control module."""

from __future__ import annotations
from typing import TYPE_CHECKING
from app.control.retrieval_control import RetrievalControl
if TYPE_CHECKING:
    from app.entity.environment_info import EnvironmentInfo
    from app.entity.types import RawResponse, RetrievalResult

class EnvironmentRetrievalControl(RetrievalControl):
    """Stereotype: Control. Control that retrieves and parses environmental datasets for a subzone."""

    def retrieveEnvironmentInfo(self, subzoneCode: str) -> RetrievalResult[EnvironmentInfo]:
        """Return environmental information and any warnings.

        Args:
            subzoneCode: str

        Returns:
            RetrievalResult[EnvironmentInfo].

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

    def parseResponse(self, data: RawResponse) -> EnvironmentInfo:
        """Parse response into domain objects.

        Args:
            data: RawResponse

        Returns:
            EnvironmentInfo.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
