"""Live FastAPI route smoke tests (skipped when dependencies are missing)."""

from __future__ import annotations

import unittest
from urllib.parse import parse_qs, urlparse

try:
    from fastapi.testclient import TestClient

    FASTAPI_TEST_AVAILABLE = True
except ImportError:  # pragma: no cover
    FASTAPI_TEST_AVAILABLE = False
    TestClient = None  # type: ignore[assignment]

from app.bootstrap import buildContext
from app.config import Settings
from app.services.profile_factory import preferenceProfileFromDto, profileDtoFromDict
from tests.support import FIXTURES, FakeOneMap, profilePayload


@unittest.skipUnless(FASTAPI_TEST_AVAILABLE, "FastAPI test client dependencies are not installed")
class FastApiEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from main import createApp

        settings = Settings(
            ONEMAP_API_KEY=None,
            ONEMAP_EMAIL="test@example.com",
            ONEMAP_PASSWORD="test-password",
            ONEMAP_BASE_URL="https://www.onemap.gov.sg",
            DATA_GOV_SG_API_KEY=None,
            DATA_GOV_SG_BASE_URL="https://api-production.data.gov.sg",
            DATA_GOV_SG_REALTIME_BASE_URL="https://api-open.data.gov.sg/v2/real-time/api",
            APP_ENV="test",
            APP_HOST="127.0.0.1",
            APP_PORT=8000,
        )
        cls.context = buildContext(settings, dataDir=FIXTURES, oneMapAdapter=FakeOneMap())
        cls.client = TestClient(createApp(cls.context))

    def test_health_ready_and_criteria(self) -> None:
        self.assertEqual(self.client.get("/api/v1/health").status_code, 200)
        ready = self.client.get("/api/v1/ready")
        self.assertTrue(ready.json()["data"]["ready"])
        criteria = self.client.get("/api/v1/criteria")
        self.assertEqual(len(criteria.json()["data"]), 5)

    def test_geometry(self) -> None:
        response = self.client.get("/api/v1/subzones/geometry")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]["features"]), 3)
        self.assertIn("X-Data-As-Of", response.headers)
        self.assertIn("ETag", response.headers)
        self.assertIn("max-age", response.headers["Cache-Control"])

    def test_data_status_for_frontend_cache(self) -> None:
        response = self.client.get("/api/v1/data/status")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["subzones"]["recordCount"], 3)
        self.assertIn("dataAsOf", response.json()["data"]["subzones"])

    def test_address_recommendations_and_comparison(self) -> None:
        address = self.client.post("/api/v1/address/search", json={"query": "Raffles Place"})
        self.assertEqual(address.status_code, 200)
        self.assertTrue(address.json()["success"])

        validation = self.client.post("/api/v1/profiles/validate", json=profilePayload())
        self.assertEqual(validation.status_code, 200)
        self.assertTrue(validation.json()["data"]["isValid"])

        overlay = self.client.post(
            "/api/v1/commute/overlay",
            json={
                "origin": {"latitude": 1.283, "longitude": 103.8513},
                "destination": {"latitude": 1.35, "longitude": 103.94},
                "mode": "PUBLIC_TRANSIT",
            },
        )
        self.assertEqual(overlay.status_code, 200)
        self.assertTrue(overlay.json()["success"])

        recommendations = self.client.post("/api/v1/recommendations", json=profilePayload())
        self.assertEqual(recommendations.status_code, 200)
        self.assertTrue(recommendations.json()["success"])
        self.assertEqual(len(recommendations.json()["data"]["items"]), 3)

        comparison = self.client.post(
            "/api/v1/comparison",
            json={"profile": profilePayload(), "subzoneCodes": ["TAMPINES01", "BEDOK01"]},
        )
        self.assertEqual(comparison.status_code, 200)
        self.assertTrue(comparison.json()["success"])
        self.assertEqual(len(comparison.json()["data"]["details"]), 2)

    def test_share_decode_endpoint(self) -> None:
        profile = profilePayload()
        share_url = self.context.reportControl.generateShareableUrl(
            preferenceProfileFromDto(profileDtoFromDict(profile)),
            ["TAMPINES01", "BEDOK01"],
            "/",
        )
        share = parse_qs(urlparse(share_url).query)["share"][0]
        response = self.client.post("/api/v1/share/decode", json={"share": share})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        data = response.json()["data"]
        self.assertEqual(data["profile"]["profileName"], "API Profile")
        self.assertEqual(data["subzoneCodes"], ["TAMPINES01", "BEDOK01"])

        invalid = self.client.post("/api/v1/share/decode", json={"share": "not-base64"})
        self.assertEqual(invalid.status_code, 200)
        self.assertFalse(invalid.json()["success"])

    def test_factsheet_and_report_download(self) -> None:
        profile = profilePayload()
        share_url = self.context.reportControl.generateShareableUrl(
            preferenceProfileFromDto(profileDtoFromDict(profile)),
            ["TAMPINES01"],
            "/",
        )
        share = parse_qs(urlparse(share_url).query)["share"][0]
        factsheet = self.client.get(
            "/api/v1/subzones/TAMPINES01/factsheet", params={"share": share}
        )
        self.assertEqual(factsheet.status_code, 200)
        self.assertTrue(factsheet.json()["success"])
        self.assertIn("4 ROOM", factsheet.json()["data"]["pricing"])

        report = self.client.post(
            "/api/v1/reports/pdf",
            json={"profile": profile, "subzoneCodes": ["TAMPINES01"]},
        )
        self.assertEqual(report.status_code, 200)
        self.assertTrue(report.json()["success"])
        download_url = report.json()["data"]["report"]["downloadUrl"]
        download = self.client.get(download_url)
        self.assertEqual(download.status_code, 200)
        self.assertTrue(download.content.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
