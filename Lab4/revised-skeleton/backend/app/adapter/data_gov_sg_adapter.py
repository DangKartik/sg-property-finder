from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.types import JSON, RawResponse


class DataGovSgAdapter:
    apiEndpoint: str
    apiKey: str | None

    def __init__(self, apiEndpoint: str, apiKey: str | None = None) -> None: ...
    def fetchDataset(self, datasetId: str) -> RawResponse: ...
    def fetchDatasetMetadata(self, datasetId: str) -> JSON: ...
    def pollDownload(self, datasetId: str) -> str: ...
    def fetchRealtime(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> JSON: ...
