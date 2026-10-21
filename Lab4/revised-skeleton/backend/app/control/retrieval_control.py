"""Retrieval control module."""

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
    """Stereotype: Control. Abstract control implementing the template-method flow for dataset retrieval."""
    dataGovAdapter: DataGovSgAdapter
    notifier: DataAvailabilityNotifier

    def __init__(self, dataGovAdapter: DataGovSgAdapter, notifier: DataAvailabilityNotifier) -> None:
        """Initialise the RetrievalControl with its dependencies.

        Args:
            dataGovAdapter: DataGovSgAdapter
            notifier: DataAvailabilityNotifier

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    @abstractmethod
    def fetchData(self, resourceId: str) -> RawResponse:
        """Fetch raw data for a dataset; raise or return a warning when unavailable.

        Args:
            resourceId: str

        Returns:
            RawResponse.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    @abstractmethod
    def parseResponse(self, data: RawResponse) -> object:
        """Parse a raw response into domain objects.

        Args:
            data: RawResponse

        Returns:
            object.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def handleMissingData(self, datasetCode: str, subzoneCode: str | None=None, code: DataAvailabilityCode | None=None, source: str='data.gov.sg', isStale: bool=False, isRetryable: bool=False) -> DataAvailabilityWarning:
        """Create a warning for missing data without retaining request state.

        Args:
            datasetCode: str
            subzoneCode: str | None
            code: DataAvailabilityCode | None
            source: str
            isStale: bool
            isRetryable: bool

        Returns:
            DataAvailabilityWarning.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
