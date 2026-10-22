"""Factsheet aggregation control."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.time import nextWeekdayPeak
from app.entity.commute_estimate import CommuteEstimate
from app.entity.enums import DataAvailabilityCode
from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO

if TYPE_CHECKING:
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.amenity_retrieval_control import AmenityRetrievalControl
    from app.control.commute_control import CommuteControl
    from app.control.environment_retrieval_control import EnvironmentRetrievalControl
    from app.control.house_pricing_retrieval_control import HousePricingRetrievalControl
    from app.entity.preference_profile import PreferenceProfile


class NeighborhoodDetailsControl:
    """Stereotype: Control. Aggregates a subzone fact sheet."""

    def __init__(
        self,
        amenityControl: AmenityRetrievalControl,
        envControl: EnvironmentRetrievalControl,
        pricingControl: HousePricingRetrievalControl,
        commuteControl: CommuteControl,
        subzoneRegistry: SubzoneRegistry | None = None,
    ) -> None:
        """Store the retrieval controls and optional subzone registry."""
        self.amenityControl = amenityControl
        self.envControl = envControl
        self.pricingControl = pricingControl
        self.commuteControl = commuteControl
        self.subzoneRegistry = subzoneRegistry

    def fetchNeighborhoodDetails(
        self,
        subzoneCode: str,
        profile: PreferenceProfile,
    ) -> NeighborhoodDetailDTO:
        """Return pricing, amenities, environment and commute for one subzone."""
        subzone = None
        if self.subzoneRegistry is not None:
            subzone = self.subzoneRegistry.getSubzone(subzoneCode)

        pricing_result = self.pricingControl.retrieveHousePricing(
            subzoneCode, profile.selectedFlatTypes
        )
        amenity_result = self.amenityControl.retrieveAmenityInfo(subzoneCode)
        env_result = self.envControl.retrieveEnvironmentInfo(subzoneCode)
        warnings = [
            *pricing_result.warnings,
            *amenity_result.warnings,
            *env_result.warnings,
        ]

        try:
            destination = subzone.centroid if subzone is not None else None
            if destination is None:
                raise ValueError("Subzone registry is required for commute calculation")
            commute = self.commuteControl.retrieveCommute(
                profile.anchorCoordinates,
                destination,
                profile.preferredCommuteMode,
                nextWeekdayPeak(),
                subzoneCode,
                warnings=warnings,
            )
        except Exception:
            commute = CommuteEstimate(
                durationMinutes=0,
                distanceKm=0.0,
                transferCount=0,
                travelMode=profile.preferredCommuteMode,
                departureTime=nextWeekdayPeak(),
            )
            from app.control.data_availability_notifier import DataAvailabilityNotifier

            warnings.append(
                DataAvailabilityNotifier().notifyDataUnavailable(
                    "COMMUTE",
                    subzoneCode,
                    DataAvailabilityCode.PARTIAL_DATA,
                    source="OneMap",
                    isRetryable=True,
                    message="Commute estimate unavailable; shown as a placeholder",
                )
            )

        pricing_note = None
        if any(entry.isTownProxy for entry in pricing_result.data.values()):
            pricing_note = (
                "Pricing data represents the median resale price for the overarching HDB Town."
            )
        return NeighborhoodDetailDTO(
            subzoneCode=subzoneCode,
            subzoneName=subzone.subzoneName if subzone is not None else subzoneCode,
            pricing=pricing_result.data,
            amenities=amenity_result.data,
            environment=env_result.data,
            commute=commute,
            warnings=warnings,
            generatedTime=datetime.now(timezone.utc),
            indicators=subzone.indicators if subzone is not None else None,
            pricingNote=pricing_note,
        )
