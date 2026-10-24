"""Additional tests for cache, map control, async commute and factories."""

from __future__ import annotations

import asyncio
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from app.control.commute_control import CommuteControl
from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.control.map_control import MapControl
from app.core.cache import TTLCache
from app.core.polyline import decodePolyline, encodePolyline
from app.entity.enums import TransitMode
from app.entity.types import Coordinates
from app.services.live_environment import LiveEnvironmentProvider
from app.services.profile_factory import preferenceProfileFromDto, profileDtoFromDict
from tests.support import FIXTURES, FakeOneMap, load_registry, profilePayload


class CacheTests(unittest.TestCase):
    def test_entries_expire(self) -> None:
        now = [0.0]
        cache = TTLCache(ttl=10, clock=lambda: now[0])
        cache["key"] = "value"
        self.assertEqual(cache.get("key"), "value")
        now[0] = 11.0
        self.assertIsNone(cache.get("key"))


class MapControlTests(unittest.TestCase):
    def test_map_payload_and_overlay(self) -> None:
        registry = load_registry()
        adapter = FakeOneMap()
        commute = CommuteControl(adapter, DataAvailabilityNotifier(), matrixPath=FIXTURES / "commute_matrix.json")
        control = MapControl(registry, adapter, commute)
        data = control.generateMapData({"TAMPINES01": 90.0})
        self.assertEqual(len(data.geojson["features"]), 3)
        self.assertEqual(data.scores["TAMPINES01"], 90.0)
        self.assertTrue(control.fetchSubzoneBoundary("TAMPINES01").contains(1.35, 103.94))
        overlay = control.getCommuteOverlay(
            Coordinates(1.28, 103.85),
            Coordinates(1.35, 103.94),
            TransitMode.PUBLIC_TRANSIT,
        )
        self.assertEqual(overlay.durationMinutes, 20)
        self.assertEqual(overlay.distanceKm, 8.0)

    def test_public_transport_overlay_merges_all_leg_geometries(self) -> None:
        class MultiLegAdapter:
            def getRoutingData(self, origin, destination, mode, departureTime=None):
                return {
                    "plan": {
                        "itineraries": [
                            {
                                "duration": 1800,
                                "legs": [
                                    {
                                        "distance": 400,
                                        "legGeometry": {
                                            "points": encodePolyline(
                                                [(1.28, 103.85), (1.285, 103.855)]
                                            )
                                        },
                                    },
                                    {
                                        "distance": 3600,
                                        "legGeometry": {
                                            "points": encodePolyline(
                                                [
                                                    (1.285, 103.855),
                                                    (1.29, 103.86),
                                                    (1.295, 103.865),
                                                ]
                                            )
                                        },
                                    },
                                ],
                            }
                        ]
                    }
                }

        control = MapControl(load_registry(), MultiLegAdapter(), None)  # type: ignore[arg-type]
        overlay = control.getCommuteOverlay(
            Coordinates(1.28, 103.85),
            Coordinates(1.295, 103.865),
            TransitMode.PUBLIC_TRANSIT,
        )

        self.assertEqual(overlay.distanceKm, 4.0)
        points = decodePolyline(overlay.geometry)
        self.assertEqual(len(points), 4)
        self.assertAlmostEqual(points[-1][0], 1.295, places=5)
        self.assertAlmostEqual(points[-1][1], 103.865, places=5)
        self.assertTrue(all(point[1] < 104 for point in points))


class AsyncCommuteTests(unittest.TestCase):
    def test_custom_workplace_uses_live_shortlist_with_estimates(self) -> None:
        base = load_registry().getSubzone("TAMPINES01")
        subzones = [
            replace(
                base,
                subzoneCode=f"S{index:02d}",
                centroid=Coordinates(1.30 + index * 0.001, 103.80 + index * 0.001),
            )
            for index in range(60)
        ]
        adapter = FakeOneMap()
        control = CommuteControl(adapter, DataAvailabilityNotifier())
        result = asyncio.run(
            control.retrieveCommutes(
                Coordinates(1.30, 103.80),
                subzones,
                TransitMode.PUBLIC_TRANSIT,
                topK=50,
            )
        )
        self.assertEqual(len(result.data), 60)
        self.assertEqual(adapter.routing_calls, 50)
        self.assertEqual(len(result.warnings), 10)
        self.assertTrue(
            all("Outside live-routing shortlist" in warning.message for warning in result.warnings)
        )

    def test_driving_uses_hybrid_shortlist(self) -> None:
        base = load_registry().getSubzone("TAMPINES01")
        subzones = [
            replace(
                base,
                subzoneCode=f"H{index:02d}",
                centroid=Coordinates(1.30 + index * 0.001, 103.80 + index * 0.001),
            )
            for index in range(60)
        ]
        adapter = FakeOneMap()
        control = CommuteControl(adapter, DataAvailabilityNotifier())
        result = asyncio.run(
            control.retrieveCommutes(
                Coordinates(1.2830, 103.8513),
                subzones,
                TransitMode.DRIVING,
                topK=50,
            )
        )
        self.assertEqual(len(result.data), 60)
        self.assertEqual(adapter.routing_calls, 50)
        self.assertEqual(len(result.warnings), 10)
        self.assertTrue(
            all("Outside live-routing shortlist" in warning.message for warning in result.warnings)
        )

    def test_async_adapter_method_is_preferred(self) -> None:
        class AsyncFake:
            def __init__(self) -> None:
                self.calls = 0

            async def getRoutingDataAsync(self, origin, destination, mode, departureTime=None):
                self.calls += 1
                return {
                    "route_summary": {"total_time": 600, "total_distance": 3000},
                    "route_geometry": "async-route",
                    "route_instructions": [],
                }

        base = load_registry().getSubzone("TAMPINES01")
        subzones = [
            replace(base, subzoneCode="ASYNC01", centroid=Coordinates(1.30, 103.80)),
        ]
        adapter = AsyncFake()
        control = CommuteControl(adapter, DataAvailabilityNotifier())
        result = asyncio.run(
            control.retrieveCommutes(
                Coordinates(1.30, 103.80),
                subzones,
                TransitMode.PUBLIC_TRANSIT,
                topK=5,
            )
        )
        self.assertEqual(adapter.calls, 1)
        self.assertEqual(result.data["ASYNC01"].durationMinutes, 10)


class LiveEnvironmentTests(unittest.TestCase):
    def test_live_values_are_read_and_cached(self) -> None:
        class StubDataGov:
            def __init__(self) -> None:
                self.calls = 0

            def fetchRealtime(self, path, params=None):
                self.calls += 1
                if path == "pm25":
                    return {"data": {"items": [{"readings": {"pm25_one_hourly": {"national": 19}}}]}}
                if path == "uv":
                    return {"data": {"records": [{"index": [{"value": 8}]}]}}
                return {"data": {"records": [{"general": {"forecast": {"code": "TL"}}}]}}

        adapter = StubDataGov()
        provider = LiveEnvironmentProvider(adapter)
        values = provider.get("TAMPINES01")
        self.assertEqual(values["pm25"], 19)
        self.assertEqual(values["uvi"], 8)
        self.assertEqual(values["forecastCode"], "TL")
        provider.get("BEDOK01")
        self.assertEqual(adapter.calls, 3)


class ProfileFactoryTests(unittest.TestCase):
    def test_payload_to_domain_profile(self) -> None:
        dto = profileDtoFromDict(profilePayload())
        profile = preferenceProfileFromDto(dto)
        self.assertEqual(profile.profileName, "API Profile")
        self.assertEqual(len(profile.criteriaWeights), 5)
        self.assertEqual(profile.preferredCommuteMode, TransitMode.PUBLIC_TRANSIT)
        self.assertEqual(profile.minimumPrimarySchools, 0)

    def test_minimum_counts_round_trip(self) -> None:
        payload = profilePayload()
        payload.update(
            {
                "minimumPrimarySchools": 2,
                "minimumSecondarySchools": 1,
                "minimumTertiarySchools": 1,
                "minimumMalls": 3,
                "minimumHospitals": 1,
            }
        )
        profile = preferenceProfileFromDto(profileDtoFromDict(payload))
        self.assertEqual(profile.minimumPrimarySchools, 2)
        self.assertEqual(profile.minimumSecondarySchools, 1)
        self.assertEqual(profile.minimumTertiarySchools, 1)
        self.assertEqual(profile.minimumMalls, 3)
        self.assertEqual(profile.minimumHospitals, 1)


if __name__ == "__main__":
    unittest.main()
