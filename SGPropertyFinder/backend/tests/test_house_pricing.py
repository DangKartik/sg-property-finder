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

    def test_prices_always_use_town_proxy(self) -> None:
        result = self.control.retrieveHousePricing("TAMPINES01", ["4 ROOM"])
        pricing = result.data["4 ROOM"]
        self.assertTrue(pricing.isTownProxy)
        self.assertGreater(pricing.transactionCount, 0)
        self.assertEqual(result.warnings, [])

    def test_town_proxy_is_used_for_small_samples(self) -> None:
        result = self.control.retrieveHousePricing("BEDOK01", ["4 ROOM"])
        pricing = result.data["4 ROOM"]
        self.assertTrue(pricing.isTownProxy)
        self.assertGreater(pricing.transactionCount, 0)
        self.assertEqual(result.warnings, [])

    def test_twelve_month_window_excludes_old_transaction(self) -> None:
        result = self.control.retrieveHousePricing("TAMPINES01", ["4 ROOM"])
        pricing = result.data["4 ROOM"]
        self.assertTrue(pricing.isTownProxy)
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
        self.assertTrue(result.data["4 ROOM"].isTownProxy)


if __name__ == "__main__":
    unittest.main()
