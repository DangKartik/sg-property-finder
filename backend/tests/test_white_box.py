"""White-box control-flow, basis-path and data-flow tests for scoring/ranking.

The graph, basis-path and definition-use models are documented in
``docs/WHITE_BOX_TESTING.md``. The tests exercise every feasible decision
outcome and record the values that cross the ranking -> scoring boundary.
"""

from __future__ import annotations

import unittest

from app.control.ranking_control import RankingControl
from app.core.time import CBD_LATITUDE, CBD_LONGITUDE
from app.entity.commute_estimate import CommuteEstimate
from app.entity.data_availability_warning import DataAvailabilityWarning
from app.entity.enums import DataAvailabilityCode, TransitMode, WarningSeverity
from app.entity.recommendation_item import RecommendationItem
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


class RecordingWeightedScoringStrategy(WeightedScoringStrategy):
    """Record data that crosses the ranking -> scoring boundary."""

    def __init__(self, items: list[RecommendationItem] | None = None) -> None:
        super().__init__()
        self.items = list(items or [])
        self.calls: list[dict[str, object]] = []

    def scoreCandidates(
        self,
        subzones,
        profile,
        commutes,
        warnings=None,
    ) -> list[RecommendationItem]:
        self.calls.append(
            {
                "subzones": list(subzones),
                "profile": profile,
                "commutes": commutes,
                "warnings": list(warnings) if warnings is not None else None,
            }
        )
        return list(self.items)


class RawValueRecordingStrategy(WeightedScoringStrategy):
    """Record which subzones and commutes reach the raw-value step."""

    def __init__(self) -> None:
        super().__init__()
        self.rawCalls: list[tuple[str, str, int | None]] = []

    def _rawValue(self, criterion_id, subzone, profile, commute):
        self.rawCalls.append(
            (
                criterion_id,
                subzone.subzoneCode,
                commute.durationMinutes if commute is not None else None,
            )
        )
        return super()._rawValue(criterion_id, subzone, profile, commute)


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

    def test_wb_rr_08_insufficient_data_subzone_is_excluded(self) -> None:
        self.registry.getSubzone("BEDOK01").dataAvailable = False
        control, commute = self.control([])

        result = control.generateRankedRecommendations(self.profile, limit=None)

        self.assertNotIn("BEDOK01", [item.subzoneId for item in result.items])
        self.assertEqual(
            [subzone.subzoneCode for subzone in commute.calls[0]["subzones"]],
            ["TAMPINES01", "JURONG01"],
        )


class ScoreCandidatesBasisPathTests(unittest.TestCase):
    """Basis paths for WeightedScoringStrategy.scoreCandidates."""

    def setUp(self) -> None:
        self.registry = attach_indicators(load_registry())
        self.strategy = WeightedScoringStrategy()
        self.profile = make_profile()
        self.commutes = {
            "TAMPINES01": CommuteEstimate(35, 14.2, 1, TransitMode.PUBLIC_TRANSIT),
            "BEDOK01": CommuteEstimate(28, 11.8, 1, TransitMode.PUBLIC_TRANSIT),
            "JURONG01": CommuteEstimate(45, 19.5, 2, TransitMode.PUBLIC_TRANSIT),
        }

    def test_wb_sc_bp_01_all_criteria_available_produces_items(self) -> None:
        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), self.profile, self.commutes
        )

        self.assertEqual(len(items), 3)
        for item in items:
            self.assertEqual(
                sum(1 for score in item.criterionScores if not score.isMissing),
                5,
            )
            self.assertAlmostEqual(
                sum(score.weight for score in item.criterionScores),
                1.0,
                places=3,
            )

    def test_wb_sc_bp_02_amenity_minimum_removes_candidate(self) -> None:
        profile = make_profile()
        profile.minimumTertiarySchools = 1
        profile.minimumHospitals = 1

        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), profile, self.commutes
        )

        self.assertEqual([item.subzoneId for item in items], ["TAMPINES01"])

    def test_wb_sc_bp_03_zero_weights_produce_no_items(self) -> None:
        profile = make_profile(
            weights={
                "PRICE": 0,
                "COMMUTE_TIME": 0,
                "SCHOOL_PROXIMITY": 0,
                "GREEN_COVERAGE": 0,
                "AMENITIES_DENSITY": 0,
            }
        )
        warnings: list[DataAvailabilityWarning] = []

        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), profile, self.commutes, warnings
        )

        self.assertEqual(items, [])
        self.assertTrue(
            any(warning.datasetCode == "SCORING" for warning in warnings)
        )

    def test_wb_sc_bp_04_missing_criterion_renormalises_weights(self) -> None:
        self.registry.getSubzone("JURONG01").indicators.greenCoveragePercent500m = None
        warnings: list[DataAvailabilityWarning] = []

        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), self.profile, self.commutes, warnings
        )

        jurong = next(item for item in items if item.subzoneId == "JURONG01")
        green = next(
            score
            for score in jurong.criterionScores
            if score.criterionId == "GREEN_COVERAGE"
        )
        self.assertTrue(green.isMissing)
        self.assertAlmostEqual(
            sum(
                score.weight
                for score in jurong.criterionScores
                if not score.isMissing
            ),
            1.0,
            places=3,
        )
        self.assertTrue(any("GREEN_COVERAGE" in warning.message for warning in warnings))

    def test_wb_sc_bp_05_no_available_criteria_skips_item(self) -> None:
        subzone = self.registry.getSubzone("TAMPINES01")
        indicators = subzone.indicators
        assert indicators is not None
        indicators.medianResalePrice = None
        indicators.medianPriceByFlatType = {}
        indicators.greenCoveragePercent500m = None
        indicators.amenityDataAvailable = False
        warnings: list[DataAvailabilityWarning] = []

        items = self.strategy.scoreCandidates(
            [subzone], self.profile, {}, warnings
        )

        self.assertEqual(items, [])
        self.assertTrue(
            any(
                warning.subzoneCode == "TAMPINES01"
                and warning.message == "No criteria have a positive weight and available data"
                for warning in warnings
            )
        )

    def test_wb_sc_bp_06_budget_filter_removes_all_candidates(self) -> None:
        profile = make_profile(budgetMax=1000)

        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), profile, self.commutes
        )

        self.assertEqual(items, [])


class ScoringDataFlowWhiteBoxTests(unittest.TestCase):
    """Definition-use tests for WeightedScoringStrategy.scoreCandidates."""

    def setUp(self) -> None:
        self.registry = attach_indicators(load_registry())
        self.profile = make_profile()
        self.commutes = {
            "TAMPINES01": CommuteEstimate(35, 14.2, 1, TransitMode.PUBLIC_TRANSIT),
            "BEDOK01": CommuteEstimate(28, 11.8, 1, TransitMode.PUBLIC_TRANSIT),
            "JURONG01": CommuteEstimate(45, 19.5, 2, TransitMode.PUBLIC_TRANSIT),
        }

    def test_wb_df_sc_01_eligible_definition_guards_raw_value_collection(self) -> None:
        strategy = RawValueRecordingStrategy()
        profile = make_profile(budgetMax=450000)

        items = strategy.scoreCandidates(
            self.registry.getAllSubzones(), profile, self.commutes
        )

        self.assertEqual({item.subzoneId for item in items}, {"BEDOK01", "JURONG01"})
        # The budget filter defines `eligible`; an excluded subzone must never
        # reach the raw-value collection loop.
        self.assertNotIn("TAMPINES01", {code for _, code, _ in strategy.rawCalls})

    def test_wb_df_sc_02_missing_commute_definition_reaches_missing_criterion(self) -> None:
        strategy = RawValueRecordingStrategy()
        commutes = {
            "TAMPINES01": self.commutes["TAMPINES01"],
            "BEDOK01": self.commutes["BEDOK01"],
        }

        items = strategy.scoreCandidates(
            self.registry.getAllSubzones(), self.profile, commutes
        )

        jurong = next(item for item in items if item.subzoneId == "JURONG01")
        commute_score = next(
            score
            for score in jurong.criterionScores
            if score.criterionId == "COMMUTE_TIME"
        )
        self.assertTrue(commute_score.isMissing)
        self.assertIn(("COMMUTE_TIME", "JURONG01", None), strategy.rawCalls)
        self.assertAlmostEqual(
            sum(
                score.weight
                for score in jurong.criterionScores
                if not score.isMissing
            ),
            1.0,
            places=3,
        )

    def test_wb_df_sc_03_warning_list_definition_is_mutated_by_missing_data(self) -> None:
        strategy = WeightedScoringStrategy()
        self.registry.getSubzone("JURONG01").indicators.greenCoveragePercent500m = None
        warnings: list[DataAvailabilityWarning] = []

        strategy.scoreCandidates(
            self.registry.getAllSubzones(),
            self.profile,
            self.commutes,
            warnings,
        )

        # `warning_list = warnings` aliases the caller's list; missing data is
        # appended to that same definition.
        self.assertTrue(
            any(
                warning.subzoneCode == "JURONG01"
                and "GREEN_COVERAGE" in warning.message
                for warning in warnings
            )
        )


class RankingDataFlowWhiteBoxTests(unittest.TestCase):
    """Definition-use tests for RankingControl.generateRankedRecommendations."""

    def setUp(self) -> None:
        self.registry = attach_indicators(load_registry())
        self.profile = make_profile()
        self.estimates = {
            "TAMPINES01": CommuteEstimate(20, 10.0, 0, TransitMode.PUBLIC_TRANSIT),
            "BEDOK01": CommuteEstimate(30, 12.0, 0, TransitMode.PUBLIC_TRANSIT),
        }

    def item(self, code: str, rank: int, score: float) -> RecommendationItem:
        return RecommendationItem(
            subzoneId=code,
            subzoneName=code.title(),
            rank=rank,
            totalScore=score,
        )

    def test_wb_df_rr_01_inputs_flow_from_retrieval_to_scoring_and_result(self) -> None:
        warnings = [makeWarning(None), makeWarning("TAMPINES01")]
        commute = StubCommuteControl(self.estimates, warnings)
        scoring = RecordingWeightedScoringStrategy(
            [self.item("BEDOK01", 1, 80.0), self.item("TAMPINES01", 2, 70.0)]
        )
        control = RankingControl(
            self.registry,
            scoring,
            commute,
            dataSnapshotId="WB-DF-SNAPSHOT",
        )

        result = control.generateRankedRecommendations(self.profile, limit=None)

        commute_call = commute.calls[0]
        self.assertEqual(commute_call["origin"], self.profile.anchorCoordinates)
        self.assertEqual(commute_call["mode"], self.profile.preferredCommuteMode)
        self.assertEqual(commute_call["subzones"], self.registry.getAllSubzones())

        scoring_call = scoring.calls[0]
        self.assertEqual(scoring_call["subzones"], self.registry.getAllSubzones())
        self.assertIs(scoring_call["profile"], self.profile)
        self.assertEqual(scoring_call["commutes"], self.estimates)
        self.assertEqual(
            [warning.subzoneCode for warning in scoring_call["warnings"]],
            [None, "TAMPINES01"],
        )

        self.assertEqual([item.subzoneId for item in result.items], ["BEDOK01", "TAMPINES01"])
        self.assertEqual(result.profileSnapshot["profileId"], "profile-1")
        self.assertEqual(result.dataSnapshotId, "WB-DF-SNAPSHOT")
        self.assertEqual(
            [warning.subzoneCode for warning in result.warnings],
            [None, "TAMPINES01"],
        )

    def test_wb_df_rr_02_limit_and_retained_codes_filter_warnings(self) -> None:
        warnings = [
            makeWarning(None),
            makeWarning("TAMPINES01"),
            makeWarning("BEDOK01"),
        ]
        commute = StubCommuteControl(self.estimates, warnings)
        scoring = RecordingWeightedScoringStrategy(
            [self.item("TAMPINES01", 1, 80.0), self.item("BEDOK01", 2, 70.0)]
        )
        control = RankingControl(self.registry, scoring, commute)

        result = control.generateRankedRecommendations(self.profile, limit=1)

        self.assertEqual([item.subzoneId for item in result.items], ["TAMPINES01"])
        # BEDOK01's warning is dropped because its item is outside `items`,
        # which defines `retained_codes`.
        self.assertEqual(
            [warning.subzoneCode for warning in result.warnings],
            [None, "TAMPINES01"],
        )

    def test_wb_df_rr_03_compute_passes_arguments_to_candidates(self) -> None:
        item = self.item("TAMPINES01", 1, 77.7)
        scoring = RecordingWeightedScoringStrategy([item])
        subzone = self.registry.getSubzone("TAMPINES01")
        commute = self.estimates["TAMPINES01"]

        score = scoring.computeSuitabilityScore(subzone, self.profile, commute)

        call = scoring.calls[0]
        self.assertEqual(score, 77.7)
        self.assertEqual(call["subzones"], [subzone])
        self.assertIs(call["profile"], self.profile)
        self.assertEqual(
            call["commutes"],
            {subzone.subzoneCode: commute},
        )


if __name__ == "__main__":
    unittest.main()
