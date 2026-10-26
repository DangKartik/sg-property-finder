"""Unit tests for external adapters using in-memory HTTP stubs."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from app.adapter.data_gov_sg_adapter import DataGovSgAdapter, DataGovSgError
from app.adapter.one_map_api_adapter import OneMapApiAdapter
from app.entity.enums import TransitMode
from app.entity.types import Coordinates
from tests.support import FIXTURES, FakeTokenManager


class FakeResponse:
    status = 200

    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Type": "application/json"}

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class OneMapAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = OneMapApiAdapter(
            "https://www.onemap.gov.sg",
            tokenManager=FakeTokenManager(),
        )

    @patch("app.adapter.one_map_api_adapter.urlopen")
    def test_search_address_returns_typed_matches(self, mock_urlopen) -> None:
        mock_urlopen.return_value = FakeResponse(
            {
                "results": [
                    {
                        "SEARCHVAL": "RAFFLES PLACE MRT",
                        "POSTAL": "048618",
                        "LATITUDE": "1.2841",
                        "LONGITUDE": "103.8514",
                    }
                ]
            }
        )
        matches = self.adapter.searchAddress("Raffles Place")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].postalCode, "048618")
        self.assertAlmostEqual(matches[0].coordinates.latitude, 1.2841)
        self.assertGreater(matches[0].confidenceScore, 0.0)
        self.assertLessEqual(matches[0].confidenceScore, 1.0)

    @patch("app.adapter.one_map_api_adapter.urlopen")
    def test_routing_returns_raw_payload(self, mock_urlopen) -> None:
        mock_urlopen.return_value = FakeResponse(
            {
                "route_summary": {"total_time": 600, "total_distance": 3000},
                "route_geometry": "abc",
            }
        )
        payload = self.adapter.getRoutingData(
            Coordinates(1.28, 103.85),
            Coordinates(1.30, 103.90),
            TransitMode.PUBLIC_TRANSIT,
        )
        self.assertEqual(payload["route_summary"]["total_time"], 600)


class StubDataGov(DataGovSgAdapter):
    def __init__(self, responses: dict[str, tuple[int, dict[str, str], bytes]]) -> None:
        super().__init__(fallbackDir=FIXTURES)
        self.responses = responses
        self.calls = 0

    def _httpGet(self, url: str, headers: dict[str, str] | None = None):
        self.calls += 1
        if url not in self.responses:
            raise DataGovSgError(f"no stub for {url}")
        return self.responses[url]


class DataGovAdapterTests(unittest.TestCase):
    def test_metadata_poll_and_fetch(self) -> None:
        metadata_url = "https://api-production.data.gov.sg/v2/public/api/datasets/demo/metadata"
        poll_url = "https://api-open.data.gov.sg/v1/public/api/datasets/demo/poll-download"
        download_url = "https://download.test/demo.json"
        adapter = StubDataGov(
            {
                metadata_url: (
                    200,
                    {},
                    b'{"data":{"lastUpdatedAt":"2025-12-01T00:00:00+08:00","recordCount":123}}',
                ),
                poll_url: (201, {}, json.dumps({"data": {"url": download_url}}).encode()),
                download_url: (200, {"Content-Type": "application/json"}, b'{"rows":[{"x":1}]}'),
            }
        )
        metadata = adapter.fetchDatasetMetadata("demo")
        self.assertEqual(metadata.recordCount, 123)
        self.assertIn("2025-12-01", metadata.dataAsOf.isoformat())
        response = adapter.fetchDataset("demo")
        self.assertEqual(response.body["rows"], [{"x": 1}])
        self.assertFalse(adapter.lastWasFallback)

    def test_local_fallback_is_used_on_failure(self) -> None:
        adapter = StubDataGov({})
        result = adapter.fetchDataset("hdb_resale")
        self.assertTrue(adapter.lastWasFallback)
        self.assertEqual(len(result.body["rows"]), 28)
        self.assertTrue(adapter.lastMetadata.dataSnapshotId.startswith("LOCAL:"))

    def test_realtime_endpoint(self) -> None:
        url = "https://api-open.data.gov.sg/v2/real-time/api/pm25"
        adapter = StubDataGov({url: (200, {}, b'{"code":0,"data":{"items":[]}}')})
        payload = adapter.fetchRealtime("pm25")
        self.assertEqual(payload["code"], 0)

    def test_cache_prevents_second_download(self) -> None:
        metadata_url = "https://api-production.data.gov.sg/v2/public/api/datasets/demo/metadata"
        poll_url = "https://api-open.data.gov.sg/v1/public/api/datasets/demo/poll-download"
        download_url = "https://download.test/demo.json"
        adapter = StubDataGov(
            {
                metadata_url: (
                    200,
                    {},
                    b'{"data":{"lastUpdatedAt":"2025-12-01T00:00:00+08:00","recordCount":1}}',
                ),
                poll_url: (200, {}, json.dumps({"data": {"url": download_url}}).encode()),
                download_url: (200, {"Content-Type": "application/json"}, b'{"rows":[{"x":1}]}'),
            }
        )
        adapter.fetchDataset("demo")
        calls_after_first = adapter.calls
        adapter.fetchDataset("demo")
        self.assertEqual(adapter.calls, calls_after_first)


if __name__ == "__main__":
    unittest.main()
