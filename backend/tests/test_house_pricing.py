"""Unit tests for HDB pricing retrieval."""

from __future__ import annotations

import unittest

from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.control.house_pricing_retrieval_control import HousePricingRetrievalControl
from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
from tests.support import FIXTURES, load_registry


class HousePricingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry()
        self.control = HousePricingRetrievalControl(
            DataGovSgAdapter(),
            DataAvailabilityNotifier(),
            dataPath=FIXTURES / "hdb_resale.csv",
            subzoneRegistry=self.registry,
            asOf="2025-12",
        )

    def test_subzone_price_when_sample_is_sufficient(self) -> None:
        result = self.control.retrieveHousePricing("TAMPINES01", ["4 ROOM"])
        pricing = result.data["4 ROOM"]
        self.assertFalse(pricing.isTownProxy)
        self.assertEqual(pricing.transactionCount, 6)
        self.assertAlmostEqual(pricing.averagePrice, 525000.0, places=2)
        self.assertEqual(result.warnings, [])

    def test_town_proxy_when_subzone_sample_is_small(self) -> None:
        result = self.control.retrieveHousePricing("BEDOK01", ["4 ROOM"])
        pricing = result.data["4 ROOM"]
        self.assertTrue(pricing.isTownProxy)
        self.assertEqual(pricing.transactionCount, 8)
        self.assertTrue(any("town proxy" in warning.message for warning in result.warnings))

    def test_twelve_month_window_excludes_old_transaction(self) -> None:
        result = self.control.retrieveHousePricing("TAMPINES01", ["4 ROOM"])
        pricing = result.data["4 ROOM"]
        self.assertGreater(pricing.averagePrice, 400000)
        self.assertEqual(pricing.dataWindowMonths, 12)

    def test_missing_flat_type_returns_warning(self) -> None:
        result = self.control.retrieveHousePricing("JURONG01", ["5 ROOM"])
        self.assertEqual(result.data, {})
        self.assertTrue(result.warnings)
        self.assertEqual(result.warnings[0].subzoneCode, "JURONG01")

    def test_multiple_flat_type_keys(self) -> None:
        result = self.control.retrieveHousePricing("TAMPINES01", ["3 ROOM", "4 ROOM"])
        self.assertEqual(set(result.data), {"3 ROOM", "4 ROOM"})
        self.assertTrue(result.data["3 ROOM"].isTownProxy)
        self.assertFalse(result.data["4 ROOM"].isTownProxy)


if __name__ == "__main__":
    unittest.main()
