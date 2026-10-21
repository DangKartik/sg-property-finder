"""Unit tests for transport-agnostic REST handlers."""

from __future__ import annotations

import unittest

from app.api import handlers
from app.bootstrap import buildContext
from app.config import Settings
from tests.support import FIXTURES, FakeOneMap, profilePayload


class ApiHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
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
        self.context = buildContext(settings, dataDir=FIXTURES, oneMapAdapter=FakeOneMap())

    def test_context_enriches_subzone_indicators(self) -> None:
        indicators = self.context.registry.getSubzone("TAMPINES01").indicators
        self.assertIsNotNone(indicators)
        self.assertIsNotNone(indicators.medianResalePrice)
        self.assertIsNotNone(indicators.greenCoveragePercent500m)

    def test_search_address(self) -> None:
        result = handlers.searchAddress("Raffles Place", self.context)
        self.assertTrue(result.success)
        self.assertEqual(len(result.data), 1)

    def test_validate_profile(self) -> None:
        valid = handlers.validateProfile(profilePayload(), self.context)
        self.assertTrue(valid.success)
        self.assertTrue(valid.data["isValid"])

        invalid_payload = profilePayload()
        invalid_payload["selectedFlatTypes"] = []
        invalid = handlers.validateProfile(invalid_payload, self.context)
        self.assertTrue(invalid.success)
        self.assertFalse(invalid.data["isValid"])

    def test_commute_overlay(self) -> None:
        result = handlers.commuteOverlay(
            {
                "origin": {"latitude": 1.283, "longitude": 103.8513},
                "destination": {"latitude": 1.35, "longitude": 103.94},
                "mode": "PUBLIC_TRANSIT",
            },
            self.context,
        )
        self.assertTrue(result.success, result.error)
        self.assertEqual(result.data["durationMinutes"], 20)

    def test_recommendations(self) -> None:
        result = handlers.recommendations(profilePayload(), self.context)
        self.assertTrue(result.success, result.error)
        self.assertEqual(len(result.data["items"]), 3)

    def test_factsheet(self) -> None:
        result = handlers.factsheet("TAMPINES01", profilePayload(), self.context)
        self.assertTrue(result.success, result.error)
        self.assertIn("4 ROOM", result.data["pricing"])

    def test_comparison(self) -> None:
        result = handlers.comparison(
            profilePayload(), ["TAMPINES01", "BEDOK01"], self.context
        )
        self.assertTrue(result.success, result.error)
        self.assertEqual(len(result.data["details"]), 2)

    def test_comparison_requires_two_subzones(self) -> None:
        result = handlers.comparison(profilePayload(), ["TAMPINES01"], self.context)
        self.assertFalse(result.success)
        self.assertEqual(result.error.code, "INVALID_COMPARISON")

    def test_comparison_is_capped_at_four_subzones(self) -> None:
        result = handlers.comparison(
            profilePayload(),
            ["TAMPINES01", "BEDOK01", "JURONG01", "X", "Y"],
            self.context,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error.code, "INVALID_COMPARISON")

    def test_geometry_and_criteria(self) -> None:
        geometry = handlers.geometry(self.context)
        self.assertEqual(len(geometry.data["features"]), 3)
        criteria = handlers.criteria(self.context)
        self.assertEqual(len(criteria.data), 5)

    def test_report_generation(self) -> None:
        result = handlers.generateReport(profilePayload(), ["TAMPINES01"], self.context)
        self.assertTrue(result.success, result.error)
        self.assertIn("report", result.data)
        self.assertIn("shareUrl", result.data)

    def test_invalid_profile_returns_validation_error(self) -> None:
        payload = profilePayload()
        payload["selectedFlatTypes"] = []
        result = handlers.recommendations(payload, self.context)
        self.assertFalse(result.success)
        self.assertEqual(result.error.code, "VALIDATION_ERROR")


if __name__ == "__main__":
    unittest.main()
