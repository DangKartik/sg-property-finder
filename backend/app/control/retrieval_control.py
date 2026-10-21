"""Template-method base for dataset retrieval."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.entity.data_availability_warning import DataAvailabilityWarning
    from app.entity.enums import DataAvailabilityCode
    from app.entity.types import RawResponse


class RetrievalControl(ABC):
    """Stereotype: Control. Template-method base for data.gov.sg retrieval."""

    dataGovAdapter: DataGovSgAdapter
    notifier: DataAvailabilityNotifier

    def __init__(self, dataGovAdapter: DataGovSgAdapter, notifier: DataAvailabilityNotifier) -> None:
        """Store the adapter and stateless notifier."""
        self.dataGovAdapter = dataGovAdapter
        self.notifier = notifier

    @abstractmethod
    def fetchData(self, resourceId: str) -> RawResponse:
        """Fetch raw data for a dataset; raise or return a warning when unavailable."""
        ...

    @abstractmethod
    def parseResponse(self, data: RawResponse) -> object:
        """Parse a raw response into domain objects."""
        ...

    def handleMissingData(
        self,
        datasetCode: str,
        subzoneCode: str | None = None,
        code: DataAvailabilityCode | None = None,
        source: str = "data.gov.sg",
        isStale: bool = False,
        isRetryable: bool = False,
        message: str | None = None,
    ) -> DataAvailabilityWarning:
        """Create a warning for missing data without retaining request state."""
        return self.notifier.notifyDataUnavailable(
            datasetCode=datasetCode,
            subzoneCode=subzoneCode,
            code=code,
            source=source,
            isStale=isStale,
            isRetryable=isRetryable,
            message=message,
        )
