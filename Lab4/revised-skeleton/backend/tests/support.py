"""Shared test helpers and fixture loaders."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
from app.container.subzone_registry import SubzoneRegistry
from app.container.town_mapping import TownMapping
from app.control.amenity_retrieval_control import AmenityRetrievalControl
from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.control.environment_retrieval_control import EnvironmentRetrievalControl
from app.control.house_pricing_retrieval_control import HousePricingRetrievalControl
from app.entity.address_match import AddressMatch
from app.entity.criterion_weight import CriterionWeight
from app.entity.enums import TransitMode
from app.entity.preference_profile import PreferenceProfile
from app.entity.types import Coordinates

FIXTURES = Path(__file__).parent / "fixtures"


class FakeOneMap:
    """Minimal OneMap adapter used by tests; no network calls."""

    def __init__(self, matches: list[AddressMatch] | None = None) -> None:
        self.matches = matches if matches is not None else [
            AddressMatch(
                formattedAddress="RAFFLES PLACE MRT",
                postalCode="048618",
                coordinates=Coordinates(1.2830, 103.8513),
                confidenceScore=None,
            )
        ]
        self.routing_calls = 0

    def searchAddress(self, query: str) -> list[AddressMatch]:
        return list(self.matches)

    def getRoutingData(self, origin, destination, mode, departureTime=None):
        self.routing_calls += 1
        return {
            "route_summary": {"total_time": 1200, "total_distance": 8000},
            "route_geometry": "encoded-route",
            "route_instructions": [],
        }


class FakeTokenManager:
    """Token manager stub for OneMap adapter tests."""

    def __init__(self) -> None:
        self.accessToken = "fake-token"
        self.tokenExpiry = datetime(2030, 1, 1, tzinfo=timezone.utc)
        self.invalidated = False

    def getAccessToken(self) -> str:
        return self.accessToken

    def refreshToken(self) -> str:
        return self.accessToken

    def invalidate(self) -> None:
        self.invalidated = True


def load_registry() -> SubzoneRegistry:
    """Load the three-subzone fixture registry."""
    mapping = TownMapping.fromFile(FIXTURES / "planning_area_to_hdb_town.json")
    return SubzoneRegistry.fromGeoJson(FIXTURES / "subzones.geojson", mapping)


def load_controls(registry: SubzoneRegistry | None = None):
    """Create fixture-backed retrieval controls."""
    registry = registry or load_registry()
    notifier = DataAvailabilityNotifier()
    data_gov = DataGovSgAdapter()
    amenities = AmenityRetrievalControl(
        data_gov,
        notifier,
        amenitiesPath=FIXTURES / "amenities.json",
        subzoneRegistry=registry,
    )
    environment = EnvironmentRetrievalControl(
        data_gov,
        notifier,
        baselinePath=FIXTURES / "environment_baselines.json",
        liveProvider=lambda code: {"pm25": 18.0, "uvi": 7, "forecastCode": "TL"},
    )
    pricing = HousePricingRetrievalControl(
        data_gov,
        notifier,
        dataPath=FIXTURES / "hdb_resale.csv",
        subzoneRegistry=registry,
        asOf="2025-12",
    )
    return registry, notifier, amenities, environment, pricing


def attach_indicators(registry: SubzoneRegistry) -> SubzoneRegistry:
    """Populate each subzone's indicators from the fixture controls."""
    _, _, amenities, environment, pricing = load_controls(registry)
    for subzone in registry.getAllSubzones():
        amenity_indicators = amenities.retrieveIndicators(subzone.subzoneCode).data
        environment_indicators = environment.retrieveIndicators(subzone.subzoneCode).data
        amenity_indicators.greenCoveragePercent500m = environment_indicators.greenCoveragePercent500m
        amenity_indicators.pm25Baseline = environment_indicators.pm25Baseline
        pricing_result = pricing.retrieveHousePricing(subzone.subzoneCode, ["4 ROOM"])
        pricing_entry = pricing_result.data.get("4 ROOM")
        if pricing_entry is not None:
            median_price = pricing_entry.getMedianPrice() or pricing_entry.averagePrice
            amenity_indicators.medianResalePrice = median_price
            amenity_indicators.medianPricePerSqm = pricing_entry.medianPricePerSqm
            amenity_indicators.transactionCount12m = pricing_entry.transactionCount
            amenity_indicators.priceTrendPercent = pricing_entry.priceTrendPercent
            amenity_indicators.medianPriceByFlatType = {pricing_entry.flatType: median_price}
            amenity_indicators.transactionCountByFlatType = {
                pricing_entry.flatType: pricing_entry.transactionCount
            }
        subzone.indicators = amenity_indicators
    return registry


def make_profile(
    *,
    budgetMax: float = 600000,
    weights: dict[str, float] | None = None,
    selectedFlatTypes: list[str] | None = None,
) -> PreferenceProfile:
    """Create a profile with balanced default weights."""
    now = datetime.now(timezone.utc)
    weights = weights or {
        "PRICE": 2,
        "COMMUTE_TIME": 2,
        "SCHOOL_PROXIMITY": 2,
        "GREEN_COVERAGE": 2,
        "AMENITIES_DENSITY": 2,
    }
    return PreferenceProfile(
        profileId="profile-1",
        profileName="Test Profile",
        budgetMin=0,
        budgetMax=budgetMax,
        selectedFlatTypes=selectedFlatTypes or ["4 ROOM"],
        workplaceAddress="Raffles Place",
        anchorCoordinates=Coordinates(1.2830, 103.8513),
        creationTime=now,
        lastUpdatedTime=now,
        isActive=True,
        criteriaWeights=[
            CriterionWeight(criterionId, float(weight))
            for criterionId, weight in weights.items()
        ],
        preferredCommuteMode=TransitMode.PUBLIC_TRANSIT,
    )


def profilePayload() -> dict[str, Any]:
    """Return a valid JSON-style profile payload for handler tests."""
    return {
        "profileId": "profile-api",
        "profileName": "API Profile",
        "budgetMin": 0,
        "budgetMax": 600000,
        "selectedFlatTypes": ["4 ROOM"],
        "workplaceAddress": "Raffles Place",
        "anchorCoordinates": {"latitude": 1.2830, "longitude": 103.8513},
        "criteriaWeights": [
            {"criterionId": "PRICE", "weightValue": 2},
            {"criterionId": "COMMUTE_TIME", "weightValue": 2},
            {"criterionId": "SCHOOL_PROXIMITY", "weightValue": 2},
            {"criterionId": "GREEN_COVERAGE", "weightValue": 2},
            {"criterionId": "AMENITIES_DENSITY", "weightValue": 2},
        ],
        "preferredCommuteMode": "PUBLIC_TRANSIT",
        "isActive": True,
    }
