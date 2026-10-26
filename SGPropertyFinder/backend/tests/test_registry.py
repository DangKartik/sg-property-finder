"""Unit tests for the subzone registry and geometry."""

from __future__ import annotations

import unittest

from tests.support import load_registry


class SubzoneRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry()

    def test_loads_all_subzones(self) -> None:
        self.assertEqual(len(self.registry.getAllSubzones()), 3)
        self.assertEqual(self.registry.getSubzone("TAMPINES01").townName, "TAMPINES")

    def test_representative_point_is_inside_polygon(self) -> None:
        subzone = self.registry.getSubzone("TAMPINES01")
        self.assertTrue(
            subzone.boundaryPolygon.contains(
                subzone.centroid.latitude, subzone.centroid.longitude
            )
        )

    def test_point_in_polygon_lookup(self) -> None:
        found = self.registry.findSubzoneForCoordinates(1.3200, 103.9300)
        self.assertIsNotNone(found)
        self.assertEqual(found.subzoneCode, "BEDOK01")
        self.assertIsNone(self.registry.findSubzoneForCoordinates(1.0, 103.0))

    def test_unknown_subzone_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.registry.getSubzone("UNKNOWN")

    def test_feature_collection_contains_scores(self) -> None:
        collection = self.registry.toFeatureCollection({"TAMPINES01": 87.5})
        self.assertEqual(collection["type"], "FeatureCollection")
        self.assertEqual(len(collection["features"]), 3)
        properties = [f["properties"] for f in collection["features"]]
        self.assertIn(87.5, [item["score"] for item in properties])

    def test_feature_collection_marks_insufficient_data(self) -> None:
        self.registry.getSubzone("TAMPINES01").dataAvailable = False
        collection = self.registry.toFeatureCollection()
        properties = {
            feature["properties"]["subzoneCode"]: feature["properties"]
            for feature in collection["features"]
        }
        self.assertFalse(properties["TAMPINES01"]["dataAvailable"])
        self.assertTrue(properties["BEDOK01"]["dataAvailable"])


if __name__ == "__main__":
    unittest.main()
