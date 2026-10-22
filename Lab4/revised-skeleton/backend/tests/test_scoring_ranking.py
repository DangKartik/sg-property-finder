"""Unit tests for MCDA scoring and ranking."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.control.commute_control import CommuteControl
from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.control.ranking_control import RankingControl
from app.entity.commute_estimate import CommuteEstimate
from app.entity.enums import TransitMode
from app.entity.types import Coordinates, RetrievalResult
from app.strategy.weighted_scoring_strategy import WeightedScoringStrategy
from tests.support import FIXTURES, FakeOneMap, attach_indicators, load_registry, make_profile


class ScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = attach_indicators(load_registry())
        self.strategy = WeightedScoringStrategy()
        self.profile = make_profile()
        self.commutes = {
            "TAMPINES01": CommuteEstimate(35, 14.2, 1, TransitMode.PUBLIC_TRANSIT),
            "BEDOK01": CommuteEstimate(28, 11.8, 1, TransitMode.PUBLIC_TRANSIT),
            "JURONG01": CommuteEstimate(45, 19.5, 2, TransitMode.PUBLIC_TRANSIT),
        }

    def test_scores_are_between_zero_and_hundred(self) -> None:
        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), self.profile, self.commutes
        )
        self.assertEqual(len(items), 3)
        self.assertTrue(all(0 <= item.totalScore <= 100 for item in items))
        self.assertEqual([item.rank for item in items], [1, 2, 3])

    def test_budget_filter_removes_expensive_subzones(self) -> None:
        profile = make_profile(budgetMax=450000)
        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), profile, self.commutes
        )
        ids = {item.subzoneId for item in items}
        self.assertEqual(ids, {"BEDOK01", "JURONG01"})

    def test_missing_criterion_is_excluded_and_weights_renormalised(self) -> None:
        self.registry.getSubzone("JURONG01").indicators.greenCoveragePercent500m = None
        warnings = []
        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), self.profile, self.commutes, warnings
        )
        jurong = next(item for item in items if item.subzoneId == "JURONG01")
        green = next(score for score in jurong.criterionScores if score.criterionId == "GREEN_COVERAGE")
        self.assertTrue(green.isMissing)
        self.assertAlmostEqual(sum(score.weight for score in jurong.criterionScores if not score.isMissing), 1.0, places=3)
        self.assertTrue(any("GREEN_COVERAGE" in warning.message for warning in warnings))

    def test_missing_amenity_source_excludes_school_and_amenity_criteria(self) -> None:
        tampines = self.registry.getSubzone("TAMPINES01")
        tampines.indicators.amenityDataAvailable = False
        warnings = []
        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), self.profile, self.commutes, warnings
        )
        tampines_item = next(item for item in items if item.subzoneId == "TAMPINES01")
        missing = {
            score.criterionId
            for score in tampines_item.criterionScores
            if score.isMissing
        }
        self.assertTrue({"SCHOOL_PROXIMITY", "AMENITIES_DENSITY"}.issubset(missing))
        self.assertAlmostEqual(
            sum(
                score.weight
                for score in tampines_item.criterionScores
                if not score.isMissing
            ),
            1.0,
            places=3,
        )

    def test_fixed_domain_normalisation_is_candidate_independent(self) -> None:
        for subzone in self.registry.getAllSubzones():
            subzone.indicators.greenCoveragePercent500m = 30.0
        items = self.strategy.scoreCandidates(
            self.registry.getAllSubzones(), self.profile, self.commutes
        )
        for item in items:
            green = next(score for score in item.criterionScores if score.criterionId == "GREEN_COVERAGE")
            self.assertAlmostEqual(green.normalisedScore, 0.3, places=3)

    def test_tie_break_uses_shortest_commute(self) -> None:
        subzones = self.registry.getAllSubzones()[:2]
        for subzone in subzones:
            subzone.indicators.medianResalePrice = 400000
            subzone.indicators.medianPriceByFlatType = {"4 ROOM": 400000}
            subzone.indicators.primarySchoolCount1km = 1
            subzone.indicators.secondarySchoolCount1km = 0
            subzone.indicators.greenCoveragePercent500m = 30.0
            subzone.indicators.mallCount1km = 1
        profile = make_profile(weights={"PRICE": 100})
        commutes = {
            "TAMPINES01": CommuteEstimate(20, 10, 1, TransitMode.PUBLIC_TRANSIT),
            "BEDOK01": CommuteEstimate(40, 20, 1, TransitMode.PUBLIC_TRANSIT),
        }
        items = self.strategy.scoreCandidates(subzones, profile, commutes)
        self.assertEqual(items[0].subzoneId, "TAMPINES01")


class RankingTests(unittest.TestCase):
    def test_ranking_control_returns_sorted_set(self) -> None:
        registry = attach_indicators(load_registry())
        commute = CommuteControl(
            FakeOneMap(),
            DataAvailabilityNotifier(),
            matrixPath=FIXTURES / "commute_matrix.json",
        )
        control = RankingControl(
            registry,
            WeightedScoringStrategy(),
            commute,
            DataAvailabilityNotifier(),
            dataSnapshotId="TEST-SNAPSHOT",
            dataAsOf=datetime.now(timezone.utc),
        )
        result = control.generateRankedRecommendations(make_profile())
        self.assertEqual(len(result.items), 3)
        self.assertEqual([item.rank for item in result.items], [1, 2, 3])
        self.assertEqual(result.dataSnapshotId, "TEST-SNAPSHOT")
        self.assertEqual(result.profileSnapshot["profileId"], "profile-1")
        scores = [item.totalScore for item in result.items]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_subzones_without_commute_estimates_remain_in_ranking(self) -> None:
        class PartialCommute:
            def retrieveCommutesSync(self, origin, subzones, mode, departureTime=None, topK=50):
                return RetrievalResult(
                    {
                        "TAMPINES01": CommuteEstimate(
                            35, 14.2, 1, TransitMode.PUBLIC_TRANSIT
                        )
                    },
                    [],
                )

        control = RankingControl(
            attach_indicators(load_registry()),
            WeightedScoringStrategy(),
            PartialCommute(),
            DataAvailabilityNotifier(),
        )
        result = control.generateRankedRecommendations(make_profile())
        self.assertEqual(len(result.items), 3)
        bedok = next(item for item in result.items if item.subzoneId == "BEDOK01")
        commute = next(
            score
            for score in bedok.criterionScores
            if score.criterionId == "COMMUTE_TIME"
        )
        self.assertTrue(commute.isMissing)


if __name__ == "__main__":
    unittest.main()
