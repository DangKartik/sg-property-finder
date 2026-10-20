from __future__ import annotations

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adapter.data_gov_sg_adapter import DataGovSgAdapter
    from entity.types import RawResponse


class RetrievalControl(ABC):
    """«control» abstract: Template-method base class for fetching and parsing data.gov.sg datasets."""

    dataAdapter: DataGovSgAdapter  # protected

    def __init__(self, dataAdapter: DataGovSgAdapter) -> None:
        """Create a RetrievalControl with its attributes (TODO: add validation if needed)."""
        self.dataAdapter = dataAdapter

    def fetchData(self, datasetId: str) -> RawResponse:
        """Fetch data (public).

        Args:
            datasetId: str
        Returns:
            RawResponse
        """
        raise NotImplementedError  # TODO

    @abstractmethod
    def parseResponse(self, data: RawResponse) -> object:
        """Parse response (protected).

        Args:
            data: RawResponse
        Returns:
            object
        """
