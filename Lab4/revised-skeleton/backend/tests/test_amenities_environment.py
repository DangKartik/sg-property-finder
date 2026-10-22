"""Unit tests for amenity counts and environment baselines."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
from app.control.amenity_retrieval_control import AmenityRetrievalControl
from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.control.environment_retrieval_control import EnvironmentRetrievalControl
from tests.support import FIXTURES, load_registry


class AmenityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry()
        self.control = AmenityRetrievalControl(
            DataGovSgAdapter(),
            DataAvailabilityNotifier(),
            amenitiesPath=FIXTURES / "amenities.json",
            subzoneRegistry=self.registry,
        )

    def test_counts_are_calculated_with_configured_radii(self) -> None:
        result = self.control.retrieveIndicators("TAMPINES01")
        indicators = result.data
        self.assertTrue(indicators.amenityDataAvailable)
        self.assertEqual(indicators.parkCount500m, 1)
        self.assertEqual(indicators.primarySchoolCount1km, 1)
        self.assertEqual(indicators.secondarySchoolCount1km, 1)
        self.assertEqual(indicators.hospitalCount2km, 1)
        self.assertEqual(indicators.mallCount1km, 1)
        self.assertEqual(indicators.mrtStationCount800m, 1)
        self.assertLess(indicators.nearestParkM, 500)

    def test_amenity_list_is_sorted_by_distance(self) -> None:
        amenities = self.control.retrieveAmenityInfo("TAMPINES01").data
        distances = [item.distanceKm for item in amenities]
        self.assertEqual(distances, sorted(distances))
        self.assertTrue(all(item.distanceKm <= 2.0 for item in amenities))

    def test_unknown_subzone_returns_warning(self) -> None:
        result = self.control.retrieveAmenityInfo("UNKNOWN")
        self.assertEqual(result.data, [])
        self.assertTrue(result.warnings)

    def test_missing_source_marks_amenity_indicators_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "amenities.json"
            path.write_text("{not valid json", encoding="utf-8")
            control = AmenityRetrievalControl(
                DataGovSgAdapter(),
                DataAvailabilityNotifier(),
                amenitiesPath=path,
                subzoneRegistry=self.registry,
            )
            result = control.retrieveIndicators("TAMPINES01")
            self.assertFalse(result.data.amenityDataAvailable)
            self.assertTrue(result.warnings)


class EnvironmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.control = EnvironmentRetrievalControl(
            DataGovSgAdapter(),
            DataAvailabilityNotifier(),
            baselinePath=FIXTURES / "environment_baselines.json",
            liveProvider=lambda code: {"pm25": 18.0, "uvi": 7, "forecastCode": "TL"},
        )

    def test_static_and_live_values_are_separated(self) -> None:
        result = self.control.retrieveEnvironmentInfo("TAMPINES01")
        info = result.data
        self.assertEqual(info.greenCoveragePercent, 35.5)
        self.assertEqual(info.weatherPattern, "Partly Cloudy")
        self.assertEqual(info.pm25, 18.0)
        self.assertEqual(info.uvi, 7.0)

    def test_scoring_indicators_use_baseline_not_live_pm25(self) -> None:
        result = self.control.retrieveIndicators("TAMPINES01")
        self.assertEqual(result.data.greenCoveragePercent500m, 35.5)
        self.assertEqual(result.data.pm25Baseline, 12.0)
        self.assertEqual(result.data.pm25Live, 18.0)

    def test_missing_baseline_returns_warning(self) -> None:
        result = self.control.retrieveEnvironmentInfo("UNKNOWN")
        self.assertEqual(result.data.greenCoveragePercent, 0.0)
        self.assertTrue(result.warnings)

    def test_regional_and_default_baselines(self) -> None:
        payload = {
            "EAST": {"greenCoveragePercent": 39.0, "pm25Baseline": 15.0},
            "DEFAULT": {"greenCoveragePercent": 42.5, "pm25Baseline": 14.2},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "environment.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            control = EnvironmentRetrievalControl(
                DataGovSgAdapter(),
                DataAvailabilityNotifier(),
                baselinePath=path,
                subzoneRegistry=load_registry(),
            )
            east = control.retrieveEnvironmentInfo("TAMPINES01")
            self.assertEqual(east.data.greenCoveragePercent, 39.0)
            fallback = control.retrieveEnvironmentInfo("UNKNOWN")
            self.assertEqual(fallback.data.greenCoveragePercent, 42.5)


if __name__ == "__main__":
    unittest.main()
