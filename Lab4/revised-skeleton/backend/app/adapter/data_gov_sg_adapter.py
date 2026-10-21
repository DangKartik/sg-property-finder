"""Data gov sg adapter module."""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.types import JSON, RawResponse

class DataGovSgAdapter:
    """Stereotype: Adapter. Adapter that wraps data.gov.sg metadata, download polling and real-time APIs."""
    apiEndpoint: str
    apiKey: str | None

    def __init__(self, apiEndpoint: str, apiKey: str | None=None) -> None:
        """Initialise the DataGovSgAdapter with its dependencies.

        Args:
            apiEndpoint: str
            apiKey: str | None

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def fetchDataset(self, datasetId: str) -> RawResponse:
        """Fetch dataset metadata/content and return a raw response.

        Args:
            datasetId: str

        Returns:
            RawResponse.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    def fetchDatasetMetadata(self, datasetId: str) -> JSON:
        """Fetch dataset metadata including the source update timestamp.

        Args:
            datasetId: str

        Returns:
            JSON.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    def pollDownload(self, datasetId: str) -> str:
        """Resolve the signed download URL for a static dataset.

        Args:
            datasetId: str

        Returns:
            str.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    def fetchRealtime(self, path: str, params: dict[str, str] | None=None) -> JSON:
        """Fetch a real-time data.gov.sg endpoint by path.

        Args:
            path: str
            params: dict[str, str] | None

        Returns:
            JSON.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...
