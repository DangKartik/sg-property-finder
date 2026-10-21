from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.entity.types import DataAvailabilityCode, RawResponse
    from app.schemas.data_availability_warning import DataAvailabilityWarning


class RetrievalControl(ABC):
    dataGovAdapter: DataGovSgAdapter
    notifier: DataAvailabilityNotifier

    def __init__(
        self,
        dataGovAdapter: DataGovSgAdapter,
        notifier: DataAvailabilityNotifier,
    ) -> None: ...
    @abstractmethod
    def fetchData(self, resourceId: str) -> RawResponse: ...
    @abstractmethod
    def parseResponse(self, data: RawResponse) -> object: ...
    def handleMissingData(
        self,
        datasetCode: str,
        subzoneCode: str | None = None,
        code: DataAvailabilityCode | None = None,
        source: str = "data.gov.sg",
        isStale: bool = False,
        isRetryable: bool = False,
    ) -> DataAvailabilityWarning: ...
