"""data.gov.sg REST adapter with cache and local fallback."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.cache import TTLCache
from app.entity.dataset_metadata import DatasetMetadata
from app.entity.types import RawResponse


class DataGovSgError(RuntimeError):
    """Raised when a data.gov.sg request and its local fallback both fail."""


class DataGovSgAdapter:
    """Stereotype: Adapter. Wraps data.gov.sg metadata, downloads and real-time APIs."""

    apiEndpoint: str
    apiKey: str | None
    downloadBaseUrl: str
    realtimeBaseUrl: str
    fallbackDir: Path | None
    cache: TTLCache[str, RawResponse]
    metadataCache: TTLCache[str, DatasetMetadata]
    lastMetadata: DatasetMetadata | None
    lastWasFallback: bool

    def __init__(
        self,
        apiEndpoint: str = "https://api-production.data.gov.sg",
        apiKey: str | None = None,
        downloadBaseUrl: str = "https://api-open.data.gov.sg",
        realtimeBaseUrl: str = "https://api-open.data.gov.sg/v2/real-time/api",
        fallbackDir: Path | str | None = None,
        cache: TTLCache[str, RawResponse] | None = None,
        timeoutSeconds: int = 20,
    ) -> None:
        """Create the adapter.

        Args:
            apiEndpoint: Data.gov.sg metadata API base.
            apiKey: Optional API key for higher rate limits.
            downloadBaseUrl: Base URL for the poll-download endpoint.
            realtimeBaseUrl: Base URL for real-time APIs.
            fallbackDir: Directory containing local fallback assets.
            cache: Optional shared TTL cache.
            timeoutSeconds: HTTP timeout.
        """
        self.apiEndpoint = apiEndpoint.rstrip("/")
        self.apiKey = apiKey
        self.downloadBaseUrl = downloadBaseUrl.rstrip("/")
        self.realtimeBaseUrl = realtimeBaseUrl.rstrip("/")
        self.fallbackDir = Path(fallbackDir) if fallbackDir else None
        self.cache = cache or TTLCache(maxsize=64, ttl=300)
        self.metadataCache = TTLCache(maxsize=64, ttl=300)
        self.realtimeCache = TTLCache(maxsize=128, ttl=300)
        self.lastMetadata = None
        self.lastWasFallback = False
        self.timeoutSeconds = timeoutSeconds

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "SGPropFinder/0.1 (data.gov.sg API client)",
        }
        if self.apiKey:
            headers["x-api-key"] = self.apiKey
        return headers

    def _httpGet(self, url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
        """Perform an HTTP GET; overridable in tests."""
        request = Request(url, headers=headers or self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self.timeoutSeconds) as response:
                return response.status, dict(response.headers.items()), response.read()
        except HTTPError as exc:
            return exc.code, dict(exc.headers.items()), exc.read()
        except URLError as exc:
            raise DataGovSgError("data.gov.sg network request failed") from exc

    def _getJson(self, url: str) -> dict[str, Any]:
        status, _, body = self._httpGet(url)
        if status not in {200, 201}:
            raise DataGovSgError(f"data.gov.sg returned HTTP {status}")
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DataGovSgError("data.gov.sg returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise DataGovSgError("data.gov.sg returned a non-object payload")
        return payload

    def fetchDatasetMetadata(self, datasetId: str) -> DatasetMetadata:
        """Fetch and normalise dataset metadata."""
        cached = self.metadataCache.get(datasetId)
        if cached is not None:
            self.lastMetadata = cached
            return cached

        url = f"{self.apiEndpoint}/v2/public/api/datasets/{datasetId}/metadata"
        payload = self._getJson(url)
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        updated = _parseIso(data.get("lastUpdatedAt") or data.get("coverageStart")) or datetime.now(timezone.utc)
        count = data.get("recordCount") or data.get("rowCount") or 0
        try:
            record_count = int(count)
        except (TypeError, ValueError):
            record_count = 0
        metadata = DatasetMetadata(
            dataSnapshotId=f"{datasetId}:{updated.isoformat()}",
            dataAsOf=updated,
            sourceUrl=url,
            recordCount=record_count,
        )
        self.metadataCache[datasetId] = metadata
        self.lastMetadata = metadata
        return metadata

    def pollDownload(self, datasetId: str) -> str:
        """Resolve the signed download URL for a static dataset."""
        url = f"{self.downloadBaseUrl}/v1/public/api/datasets/{datasetId}/poll-download"
        payload = self._getJson(url)
        data = payload.get("data")
        if isinstance(data, dict):
            link = data.get("url") or data.get("downloadUrl")
        else:
            link = data if isinstance(data, str) else None
        if not link:
            raise DataGovSgError("data.gov.sg did not return a download URL")
        return str(link)

    def fetchDataset(self, datasetId: str) -> RawResponse:
        """Fetch a dataset, falling back to a local asset if the network fails."""
        cached = self.cache.get(datasetId)
        if cached is not None:
            return cached

        self.lastWasFallback = False
        try:
            metadata = self.fetchDatasetMetadata(datasetId)
            download_url = self.pollDownload(datasetId)
            status, headers, body = self._httpGet(download_url)
            if status != 200:
                raise DataGovSgError(f"dataset download returned HTTP {status}")
            parsed = _parsePayload(body, headers.get("Content-Type", ""))
            if metadata.recordCount == 0 and isinstance(parsed, dict):
                metadata.recordCount = len(
                    parsed.get("rows", parsed.get("features", parsed.get("items", [])))
                )
                self.metadataCache[datasetId] = metadata
                self.lastMetadata = metadata
            response = RawResponse(
                statusCode=status,
                body=parsed,
                headers=headers,
                fetchedAt=metadata.dataAsOf,
            )
            self.cache[datasetId] = response
            return response
        except (DataGovSgError, HTTPError, URLError, ValueError):
            fallback = self._loadFallback(datasetId)
            if fallback is None:
                raise
            self.lastWasFallback = True
            self.cache[datasetId] = fallback
            return fallback

    def fetchRealtime(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Fetch a real-time data.gov.sg endpoint with a short TTL cache."""
        cache_key = f"{path}|{sorted((params or {}).items())}"
        cached = self.realtimeCache.get(cache_key)
        if cached is not None:
            return cached
        url = f"{self.realtimeBaseUrl}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urlencode(params)}"
        payload = self._getJson(url)
        self.realtimeCache[cache_key] = payload
        return payload

    def _loadFallback(self, datasetId: str) -> RawResponse | None:
        """Load a local JSON/GeoJSON/CSV/Parquet asset when the network is unavailable."""
        if self.fallbackDir is None:
            return None
        candidates = [
            self.fallbackDir / f"{datasetId}.json",
            self.fallbackDir / f"{datasetId}.geojson",
            self.fallbackDir / f"{datasetId}.csv",
            self.fallbackDir / f"{datasetId}.parquet",
        ]
        for path in candidates:
            if not path.exists():
                continue
            if path.suffix == ".parquet":
                body = _parseParquet(path)
                content_type = "application/vnd.apache.parquet"
            else:
                text = path.read_text(encoding="utf-8")
                content_type = (
                    "application/json" if path.suffix in {".json", ".geojson"} else "text/csv"
                )
                body = _parsePayload(text.encode("utf-8"), content_type)
            data_as_of = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            self.lastMetadata = DatasetMetadata(
                dataSnapshotId=f"LOCAL:{datasetId}:{data_as_of.isoformat()}",
                dataAsOf=data_as_of,
                sourceUrl=str(path),
                recordCount=len(body.get("rows", body.get("features", []))) if isinstance(body, dict) else 0,
            )
            return RawResponse(
                statusCode=200,
                body=body,
                headers={"Content-Type": content_type, "X-Data-Source": "local-fallback"},
                fetchedAt=data_as_of,
            )
        return None


def _parseIso(value: Any) -> datetime | None:
    """Parse an ISO timestamp into an aware datetime."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _parseParquet(path: Path) -> dict[str, Any]:
    """Load a Parquet fallback when pyarrow is installed."""
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:
        raise DataGovSgError("pyarrow is required to read Parquet fallbacks") from exc
    return {"rows": pq.read_table(path).to_pylist()}


def _parsePayload(body: bytes, content_type: str) -> dict[str, Any]:
    """Parse JSON, GeoJSON or CSV bytes into a dictionary payload."""
    text = body.decode("utf-8-sig", errors="replace")
    lowered = content_type.lower()
    if "json" in lowered or text.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DataGovSgError("dataset payload is not valid JSON") from exc
        if isinstance(parsed, dict):
            return parsed
        return {"items": parsed}
    reader = csv.DictReader(io.StringIO(text))
    return {"rows": [dict(row) for row in reader]}
