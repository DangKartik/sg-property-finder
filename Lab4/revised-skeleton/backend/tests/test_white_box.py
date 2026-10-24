"""White-box basis-path tests for scoring and ranking.

The graph models and basis paths are documented in
``docs/WHITE_BOX_TESTING.md``. These tests exercise the decision outcomes in
those graphs using deterministic stubs for the commute boundary.
"""

from __future__ import annotations

import unittest

from app.control.ranking_control import RankingControl
from app.core.time import CBD_LATITUDE, CBD_LONGITUDE
from app.entity.commute_estimate import CommuteEstimate
from app.entity.data_availability_warning import DataAvailabilityWarning
from app.entity.enums import DataAvailabilityCode, TransitMode, WarningSeverity
from app.entity.types import RetrievalResult
from app.strategy.weighted_scoring_strategy import WeightedScoringStrategy
from tests.support import attach_indicators, load_registry, make_profile


def makeWarning(subzoneCode: str | None) -> DataAvailabilityWarning:
    """Build a deterministic warning for warning-filter paths."""
    return DataAvailabilityWarning(
        subzoneCode=subzoneCode,
        datasetCode="WB_TEST",
        code=DataAvailabilityCode.PARTIAL_DATA,
        severity=WarningSeverity.WARNING,
        isStale=False,
        isRetryable=False,
        source="white-box test",
        message=f"warning for {subzoneCode or 'all subzones'}",
        asOf=None,
    )


class StubCommuteControl:
    """Return a fixed commute result and record the call arguments."""

    def __init__(
        self,
        estimates: dict[str, CommuteEstimate],
        warnings: list[DataAvailabilityWarning],
    ) -> None:
        self.estimates = estimates
        self.warnings = warnings
        self.calls: list[dict[str, object]] = []

    def retrieveCommutesSync(
        self,
        origin,
        subzones,
        mode,
        departureTime=None,
        topK: int = 50,
    ) -> RetrievalResult[dict[str, CommuteEstimate]]:
        self.calls.append(
            {
                "origin": origin,
                "subzones": list(subzones),
                "mode": mode,
                "departureTime": departureTime,
                "topK": topK,
            }
        )
        return RetrievalResult(dict(self.estimates), list(self.warnings))


class ComputeSuitabilityScoreWhiteBoxTests(unittest.TestCase):
    """Basis paths for WeightedScoringStrategy.computeSuitabilityScore."""

    def setUp(self) -> None:
        self.registry = attach_indicators(load_registry())
        self.strategy = WeightedScoringStrategy()
        self.profile = make_profile()
        self.subzone = self.registry.getSubzone("TAMPINES01")
        self.commute = CommuteEstimate(20, 10.0, 0, TransitMode.PUBLIC_TRANSIT)

    def test_wb_css_01_non_empty_items_returns_total_score(self) -> None:
        score = self.strategy.computeSuitabilityScore(
            self.subzone, self.profile, self.commute
        )
        expected = self.strategy.scoreCandidates(
            [self.subzone],
            self.profile,
            {self.subzone.subzoneCode: self.commute},
        )[0].totalScore
        self.assertEqual(score, expected)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_wb_css_02_empty_items_returns_zero(self) -> None:
        profile = make_profile()
        profile.minimumPrimarySchools = 2  # fixture has 1 primary school
        score = self.strategy.computeSuitabilityScore(
            self.subzone, profile, self.commute
        )
        self.assertEqual(score, 0.0)


class GenerateRankedRecommendationsWhiteBoxTests(unittest.TestCase):
    """Basis paths for RankingControl.generateRankedRecommendations."""

    def setUp(self) -> None:
        self.registry = attach_indicators(load_registry())
        self.strategy = WeightedScoringStrategy()
        self.profile = make_profile()
        self.estimates = {
            "TAMPINES01": CommuteEstimate(20, 10.0, 0, TransitMode.PUBLIC_TRANSIT),
            "BEDOK01": CommuteEstimate(30, 12.0, 0, TransitMode.PUBLIC_TRANSIT),
            "JURONG01": CommuteEstimate(45, 20.0, 1, TransitMode.PUBLIC_TRANSIT),
        }

    def control(
        self, warnings: list[DataAvailabilityWarning]
    ) -> tuple[RankingControl, StubCommuteControl]:
        commute = StubCommuteControl(self.estimates, warnings)
        control = RankingControl(
            self.registry,
            self.strategy,
            commute,
            dataSnapshotId="WB-SNAPSHOT",
        )
        return control, commute

    def test_wb_rr_01_anchor_limit_none_keeps_retained_warnings(self) -> None:
        warnings = [
            makeWarning(None),
            makeWarning("TAMPINES01"),
            makeWarning("UNKNOWN"),
        ]
        control, commute = self.control(warnings)

        result = control.generateRankedRecommendations(self.profile, limit=None)

        self.assertEqual(len(result.items), 3)
        self.assertEqual(
            commute.calls[0]["origin"],
            self.profile.anchorCoordinates,
        )
        self.assertEqual(
            [warning.subzoneCode for warning in result.warnings],
            [None, "TAMPINES01"],
        )
        self.assertEqual(result.dataSnapshotId, "WB-SNAPSHOT")

    def test_wb_rr_02_missing_anchor_uses_cbd(self) -> None:
        profile = make_profile()
        profile.anchorCoordinates = None
        control, commute = self.control([makeWarning("TAMPINES01")])

        result = control.generateRankedRecommendations(profile, limit=None)

        origin = commute.calls[0]["origin"]
        self.assertEqual(origin.latitude, CBD_LATITUDE)
        self.assertEqual(origin.longitude, CBD_LONGITUDE)
        self.assertEqual(len(result.items), 3)
        self.assertEqual(
            [warning.subzoneCode for warning in result.warnings],
            ["TAMPINES01"],
        )

    def test_wb_rr_03_non_none_limit_slices_items(self) -> None:
        control, _ = self.control([makeWarning("TAMPINES01")])

        result = control.generateRankedRecommendations(self.profile, limit=3)

        self.assertEqual(len(result.items), 3)
        self.assertEqual(
            [warning.subzoneCode for warning in result.warnings],
            ["TAMPINES01"],
        )

    def test_wb_rr_04_unretained_warning_is_dropped(self) -> None:
        control, _ = self.control([makeWarning("UNKNOWN")])

        result = control.generateRankedRecommendations(self.profile, limit=None)

        self.assertEqual(result.warnings, [])

    def test_wb_rr_05_limit_zero_returns_no_items(self) -> None:
        control, _ = self.control(
            [makeWarning(None), makeWarning("TAMPINES01")]
        )

        result = control.generateRankedRecommendations(self.profile, limit=0)

        self.assertEqual(result.items, [])
        self.assertEqual(
            [warning.subzoneCode for warning in result.warnings],
            [None],
        )

    def test_wb_rr_06_negative_limit_is_clamped_to_zero(self) -> None:
        control, _ = self.control([])

        result = control.generateRankedRecommendations(self.profile, limit=-5)

        self.assertEqual(result.items, [])

    def test_wb_rr_07_empty_warnings_skip_filter_loop(self) -> None:
        control, _ = self.control([])

        result = control.generateRankedRecommendations(self.profile, limit=None)

        self.assertEqual(len(result.items), 3)
        self.assertEqual(result.warnings, [])


if __name__ == "__main__":
    unittest.main()
