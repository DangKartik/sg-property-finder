"""Unit tests for commute matrix, custom routing and peak-time logic."""

from __future__ import annotations

import unittest
from datetime import datetime

from app.control.commute_control import CommuteControl
from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.core.time import SGT, nextWeekdayPeak
from app.entity.enums import TransitMode
from app.entity.types import Coordinates
from tests.support import FIXTURES, FakeOneMap, load_registry


class CommuteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry()
        self.adapter = FakeOneMap()
        self.control = CommuteControl(
            self.adapter,
            DataAvailabilityNotifier(),
            matrixPath=FIXTURES / "commute_matrix.json",
        )

    def test_matrix_is_used_for_cbd_origin(self) -> None:
        estimate = self.control.retrieveCommute(
            Coordinates(1.2830, 103.8513),
            Coordinates(1.3500, 103.9400),
            TransitMode.PUBLIC_TRANSIT,
            destinationSubzoneCode="TAMPINES01",
        )
        self.assertEqual(estimate.durationMinutes, 35)
        self.assertEqual(estimate.transferCount, 1)
        self.assertEqual(self.adapter.routing_calls, 0)

    def test_custom_origin_calls_onemap(self) -> None:
        estimate = self.control.retrieveCommute(
            Coordinates(1.3000, 103.8000),
            Coordinates(1.3500, 103.9400),
            TransitMode.PUBLIC_TRANSIT,
            destinationSubzoneCode="TAMPINES01",
        )
        self.assertEqual(estimate.durationMinutes, 20)
        self.assertEqual(self.adapter.routing_calls, 1)

    def test_batch_matrix_returns_all_candidates(self) -> None:
        result = self.control.retrieveCommutesSync(
            Coordinates(1.2830, 103.8513),
            self.registry.getAllSubzones(),
            TransitMode.PUBLIC_TRANSIT,
        )
        self.assertEqual(set(result.data), {"TAMPINES01", "BEDOK01", "JURONG01"})
        self.assertEqual(result.warnings, [])

    def test_next_weekday_peak(self) -> None:
        friday_before_peak = datetime(2026, 10, 23, 8, 0, tzinfo=SGT)  # Friday
        self.assertEqual(nextWeekdayPeak(friday_before_peak).weekday(), 4)
        self.assertEqual(nextWeekdayPeak(friday_before_peak).hour, 8)
        friday_after_peak = datetime(2026, 10, 23, 9, 0, tzinfo=SGT)
        self.assertEqual(nextWeekdayPeak(friday_after_peak).weekday(), 0)

    def test_cache_reuses_estimate(self) -> None:
        origin = Coordinates(1.3000, 103.8000)
        destination = Coordinates(1.3500, 103.9400)
        self.control.retrieveCommute(origin, destination, TransitMode.PUBLIC_TRANSIT)
        self.control.retrieveCommute(origin, destination, TransitMode.PUBLIC_TRANSIT)
        self.assertEqual(self.adapter.routing_calls, 1)


if __name__ == "__main__":
    unittest.main()
