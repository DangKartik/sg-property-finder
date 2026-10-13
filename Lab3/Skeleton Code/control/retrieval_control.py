from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.control.data_availability_notifier import DataAvailabilityNotifier
    from sgpropfinder.adapter.data_gov_sg_adapter import DataGovSgAdapter
    from sgpropfinder.entity.types import RawResponse


class RetrievalControl(ABC):
    """«control»"""

    dataGovAdapter: DataGovSgAdapter
    notifier: DataAvailabilityNotifier

    @abstractmethod
    def fetchData(self, resourceId: str) -> dict:
        ...

    def handleMissingData(self, datasetName: str) -> None:
        raise NotImplementedError  # TODO

    @abstractmethod
    def parseResponse(self, data: RawResponse) -> object:
        ...
