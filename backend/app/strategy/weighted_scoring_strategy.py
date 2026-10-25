"""Weighted multi-criteria suitability scoring."""

from __future__ import annotations

from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.entity.commute_estimate import CommuteEstimate
from app.entity.criterion_score import CriterionScore
from app.entity.data_availability_warning import DataAvailabilityWarning
from app.entity.enums import DataAvailabilityCode
from app.entity.preference_profile import PreferenceProfile
from app.entity.recommendation_item import RecommendationItem
from app.entity.subzone import Subzone
from app.strategy.criterion_catalog import CriterionCatalog, CriterionDirection, buildDefaultCriterionCatalog
from app.strategy.scoring_strategy import ScoringStrategy


class WeightedScoringStrategy(ScoringStrategy):
    """Stereotype: Strategy. Min-max weighted suitability scoring."""

    criterionCatalog: CriterionCatalog

    def __init__(self, criterionCatalog: CriterionCatalog | None = None) -> None:
        """Create the strategy with the frozen criterion catalogue."""
        self.criterionCatalog = criterionCatalog or buildDefaultCriterionCatalog()
        self.notifier = DataAvailabilityNotifier()

    def computeSuitabilityScore(
        self,
        subzone: Subzone,
        profile: PreferenceProfile,
        commute: CommuteEstimate,
    ) -> float:
        """Compute a 0-100 score for one subzone in a one-candidate cohort."""
        items = self.scoreCandidates([subzone], profile, {subzone.subzoneCode: commute})
        return items[0].totalScore if items else 0.0

    def scoreCandidates(
        self,
        subzones: list[Subzone],
        profile: PreferenceProfile,
        commutes: dict[str, CommuteEstimate],
        warnings: list[DataAvailabilityWarning] | None = None,
    ) -> list[RecommendationItem]:
        """Score, filter and rank a candidate cohort.

        The hard budget filter removes subzones whose selected-flat-type median
        price exceeds `budgetMax`. Criteria with no value are excluded and the
        remaining weights are renormalised.
        """
        warning_list = warnings if warnings is not None else []
        eligible = [
            subzone
            for subzone in subzones
            if self._budgetEligible(subzone, profile)
            and self._meetsMinimumAmenities(subzone, profile)
        ]
        criteria = self.criterionCatalog.getAllCriteria()

        # Relative weight normalisation: user ratings are 1–10, but the MCDA
        # engine works with weights that sum to 1.0. Missing-data reweighting
        # below then renormalises again over the available criteria.
        raw_weights = {
            definition.criterionId: max(
                0.0, profile.getWeightForCriterion(definition.criterionId)
            )
            for definition in criteria
        }
        total_rating = sum(raw_weights.values())
        normalized_weights = {
            criterion_id: (rating / total_rating if total_rating > 0 else 0.0)
            for criterion_id, rating in raw_weights.items()
        }

        raw_by_criterion: dict[str, dict[str, tuple[float, str]]] = {}
        for definition in criteria:
            values: dict[str, tuple[float, str]] = {}
            for subzone in eligible:
                commute = commutes.get(subzone.subzoneCode)
                raw = self._rawValue(definition.criterionId, subzone, profile, commute)
                if raw is not None:
                    values[subzone.subzoneCode] = raw
            raw_by_criterion[definition.criterionId] = values

        items: list[RecommendationItem] = []
        for subzone in eligible:
            commute = commutes.get(subzone.subzoneCode)
            criterion_scores: list[CriterionScore] = []
            available_weight = 0.0
            raw_rows: list[tuple[str, float, str, float, bool]] = []

            for definition in criteria:
                weight = normalized_weights[definition.criterionId]
                values = raw_by_criterion[definition.criterionId]
                raw = values.get(subzone.subzoneCode)
                if raw is None:
                    raw_rows.append((definition.criterionId, 0.0, "unavailable", weight, True))
                    warning_list.append(
                        self.notifier.notifyDataUnavailable(
                            definition.criterionId,
                            subzone.subzoneCode,
                            DataAvailabilityCode.MISSING_SOURCE_DATA,
                            message=(
                                f"{definition.criterionId} ({definition.criterionName}) unavailable; "
                                "weight renormalised"
                            ),
                        )
                    )
                else:
                    raw_rows.append((definition.criterionId, raw[0], raw[1], weight, False))
                    available_weight += weight

            if available_weight <= 0:
                warning_list.append(
                    self.notifier.notifyDataUnavailable(
                        "SCORING",
                        subzone.subzoneCode,
                        DataAvailabilityCode.MISSING_SOURCE_DATA,
                        message="No criteria have a positive weight and available data",
                    )
                )
                continue

            weighted_total = 0.0
            for criterion_id, raw_value, source, weight, missing in raw_rows:
                if missing:
                    criterion_scores.append(
                        CriterionScore(
                            criterionId=criterion_id,
                            rawValue=0.0,
                            normalisedScore=0.0,
                            weight=0.0,
                            weightedScore=0.0,
                            isMissing=True,
                            source=source,
                        )
                    )
                    continue
                definition = self.criterionCatalog.getCriterion(criterion_id)
                if definition is None:
                    continue
                normalised = self._normalise(
                    definition, raw_value, raw_by_criterion[criterion_id]
                )
                renormalised_weight = weight / available_weight
                weighted = normalised * renormalised_weight
                weighted_total += weighted
                criterion_scores.append(
                    CriterionScore(
                        criterionId=criterion_id,
                        rawValue=round(raw_value, 2),
                        normalisedScore=round(normalised, 4),
                        weight=round(renormalised_weight, 4),
                        weightedScore=round(weighted, 4),
                        isMissing=False,
                        source=source,
                    )
                )

            items.append(
                RecommendationItem(
                    subzoneId=subzone.subzoneCode,
                    subzoneName=subzone.subzoneName,
                    rank=0,
                    totalScore=round(weighted_total * 100, 1),
                    criterionScores=criterion_scores,
                )
            )

        items.sort(
            key=lambda item: (
                -item.totalScore,
                (commutes.get(item.subzoneId).durationMinutes if commutes.get(item.subzoneId) else 9999),
                self._priceSortKey(item.subzoneId, subzones),
                item.subzoneId,
            )
        )
        for index, item in enumerate(items, start=1):
            item.rank = index
        return items

    def _rawValue(
        self,
        criterion_id: str,
        subzone: Subzone,
        profile: PreferenceProfile,
        commute: CommuteEstimate | None,
    ) -> tuple[float, str] | None:
        indicators = subzone.indicators
        if indicators is None:
            return None
        if criterion_id == "PRICE":
            prices = [
                indicators.medianPriceByFlatType.get(flat_type)
                for flat_type in profile.selectedFlatTypes
                if indicators.medianPriceByFlatType.get(flat_type) is not None
            ]
            price = min(prices) if prices else indicators.medianResalePrice
            return (float(price), "data.gov.sg HDB Resale") if price is not None else None
        if criterion_id == "COMMUTE_TIME":
            return (float(commute.durationMinutes), "OneMap") if commute is not None else None
        if criterion_id == "SCHOOL_PROXIMITY":
            if not indicators.amenityDataAvailable:
                return None
            count = indicators.primarySchoolCount1km + indicators.secondarySchoolCount1km
            return (float(count), "MOE Schools")
        if criterion_id == "GREEN_COVERAGE":
            green = indicators.greenCoveragePercent500m
            return (float(green), "NParks Parks") if green is not None else None
        if criterion_id == "AMENITIES_DENSITY":
            if not indicators.amenityDataAvailable:
                return None
            count = (
                indicators.mallCount1km
                + indicators.polyclinicCount2km
                + indicators.hospitalCount2km
                + indicators.mrtStationCount800m
            )
            return (float(count), "OneMap Themes")
        return None

    def _budgetEligible(self, subzone: Subzone, profile: PreferenceProfile) -> bool:
        if subzone.indicators is None:
            return True
        prices = [
            subzone.indicators.medianPriceByFlatType.get(flat_type)
            for flat_type in profile.selectedFlatTypes
            if subzone.indicators.medianPriceByFlatType.get(flat_type) is not None
        ]
        if prices:
            return min(prices) <= profile.budgetMax
        if subzone.indicators.medianResalePrice is not None:
            return subzone.indicators.medianResalePrice <= profile.budgetMax
        return True

    def _meetsMinimumAmenities(
        self, subzone: Subzone, profile: PreferenceProfile
    ) -> bool:
        """Return whether a subzone meets every hard amenity minimum.

        The filter is skipped when amenity data is unavailable; the scoring
        strategy already excludes those criteria and attaches warnings in that
        case, so discarding every subzone would be misleading.
        """
        indicators = subzone.indicators
        if indicators is None or not indicators.amenityDataAvailable:
            return True
        return (
            indicators.primarySchoolCount1km >= profile.minimumPrimarySchools
            and indicators.secondarySchoolCount1km >= profile.minimumSecondarySchools
            and indicators.tertiarySchoolCount1km >= profile.minimumTertiarySchools
            and indicators.mallCount1km >= profile.minimumMalls
            and indicators.hospitalCount2km >= profile.minimumHospitals
        )

    @staticmethod
    def _priceSortKey(subzone_id: str, subzones: list[Subzone]) -> float:
        for subzone in subzones:
            if subzone.subzoneCode == subzone_id and subzone.indicators is not None:
                if subzone.indicators.medianResalePrice is not None:
                    return subzone.indicators.medianResalePrice
        return float("inf")

    @staticmethod
    def _normalise(
        definition,
        value: float,
        values: dict[str, tuple[float, str]],
    ) -> float:
        if definition.minValue is not None and definition.maxValue is not None:
            low, high = definition.minValue, definition.maxValue
        else:
            numbers = [item[0] for item in values.values()]
            if not numbers:
                return 0.0
            low, high = min(numbers), max(numbers)
        if high == low:
            return 1.0
        clamped = max(low, min(high, value))
        if definition.direction is CriterionDirection.MINIMIZE:
            return (high - clamped) / (high - low)
        return (clamped - low) / (high - low)
