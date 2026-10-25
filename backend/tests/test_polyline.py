"""Tests for encoded-polyline decoding and leg merging."""

from __future__ import annotations

import unittest

from app.core.polyline import decodePolyline, encodePolyline, mergeEncodedPolylines


class PolylineTests(unittest.TestCase):
    def test_decodes_canonical_google_polyline(self) -> None:
        points = decodePolyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
        self.assertEqual(len(points), 3)
        self.assertAlmostEqual(points[0][0], 38.5, places=5)
        self.assertAlmostEqual(points[0][1], -120.2, places=5)
        self.assertAlmostEqual(points[1][0], 40.7, places=5)
        self.assertAlmostEqual(points[1][1], -120.95, places=5)
        self.assertAlmostEqual(points[2][0], 43.252, places=5)
        self.assertAlmostEqual(points[2][1], -126.453, places=5)

    def test_round_trip_preserves_coordinates(self) -> None:
        points = [(1.28, 103.85), (1.285, 103.855), (1.29, 103.86)]
        decoded = decodePolyline(encodePolyline(points))
        self.assertEqual(len(decoded), len(points))
        for expected, actual in zip(points, decoded):
            self.assertAlmostEqual(actual[0], expected[0], places=5)
            self.assertAlmostEqual(actual[1], expected[1], places=5)

    def test_merge_rebases_independently_encoded_legs(self) -> None:
        first_leg = encodePolyline([(1.28, 103.85), (1.285, 103.855)])
        second_leg = encodePolyline([(1.285, 103.855), (1.29, 103.86), (1.295, 103.865)])

        merged = decodePolyline(mergeEncodedPolylines([first_leg, second_leg]))

        self.assertEqual(len(merged), 4)
        self.assertAlmostEqual(merged[0][0], 1.28, places=5)
        self.assertAlmostEqual(merged[0][1], 103.85, places=5)
        self.assertAlmostEqual(merged[-1][0], 1.295, places=5)
        self.assertAlmostEqual(merged[-1][1], 103.865, places=5)
        self.assertTrue(all(point[1] < 104 for point in merged))

    def test_merge_skips_empty_legs(self) -> None:
        leg = encodePolyline([(1.28, 103.85), (1.285, 103.855)])
        merged = decodePolyline(mergeEncodedPolylines([None, leg, ""]))
        self.assertEqual(len(merged), 2)


if __name__ == "__main__":
    unittest.main()
