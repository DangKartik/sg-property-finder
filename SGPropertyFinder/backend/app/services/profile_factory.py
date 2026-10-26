"""Map transport dictionaries to profile DTOs and domain entities."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.entity.criterion_weight import CriterionWeight
from app.entity.enums import TransitMode
from app.entity.preference_profile import PreferenceProfile
from app.entity.types import Coordinates
from app.schemas.profile_dto import ProfileDTO


def profileDtoFromDict(data: dict[str, Any]) -> ProfileDTO:
    """Build a ProfileDTO from a JSON request body.

    Raises:
        ValueError: If a required field is missing or malformed.
    """
    if not isinstance(data, dict):
        raise ValueError("Profile payload must be an object")
    try:
        weights = [
            CriterionWeight(
                criterionId=str(item["criterionId"]),
                weightValue=float(item["weightValue"]),
            )
            for item in data.get("criteriaWeights", [])
        ]
        anchor = data.get("anchorCoordinates")
        coordinates = (
            Coordinates(float(anchor["latitude"]), float(anchor["longitude"]))
            if isinstance(anchor, dict)
            else None
        )
        mode = TransitMode(str(data.get("preferredCommuteMode", TransitMode.PUBLIC_TRANSIT.value)))
        return ProfileDTO(
            profileId=data.get("profileId"),
            profileName=str(data.get("profileName", "")),
            budgetMin=float(data.get("budgetMin", 0)),
            budgetMax=float(data.get("budgetMax", 0)),
            selectedFlatTypes=[str(item).upper() for item in data.get("selectedFlatTypes", [])],
            workplaceAddress=data.get("workplaceAddress"),
            anchorCoordinates=coordinates,
            criteriaWeights=weights,
            preferredCommuteMode=mode,
            departureTime=_parseDatetime(data.get("departureTime")),
            isActive=bool(data.get("isActive", True)),
            creationTime=_parseDatetime(data.get("creationTime")),
            lastUpdatedTime=_parseDatetime(data.get("lastUpdatedTime")),
            minimumPrimarySchools=_parseCount(data.get("minimumPrimarySchools")),
            minimumSecondarySchools=_parseCount(data.get("minimumSecondarySchools")),
            minimumTertiarySchools=_parseCount(data.get("minimumTertiarySchools")),
            minimumMalls=_parseCount(data.get("minimumMalls")),
            minimumHospitals=_parseCount(data.get("minimumHospitals")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid profile payload: {exc}") from exc


def preferenceProfileFromDto(data: ProfileDTO) -> PreferenceProfile:
    """Build a PreferenceProfile, generating an ID and timestamps when absent."""
    now = datetime.now(timezone.utc)
    return PreferenceProfile(
        profileId=data.profileId or uuid.uuid4().hex,
        profileName=data.profileName,
        budgetMin=data.budgetMin,
        budgetMax=data.budgetMax,
        selectedFlatTypes=list(data.selectedFlatTypes),
        workplaceAddress=data.workplaceAddress or "",
        anchorCoordinates=data.anchorCoordinates or Coordinates(1.2830, 103.8513),
        creationTime=data.creationTime or now,
        lastUpdatedTime=data.lastUpdatedTime or now,
        isActive=data.isActive,
        criteriaWeights=list(data.criteriaWeights),
        preferredCommuteMode=data.preferredCommuteMode,
        minimumPrimarySchools=data.minimumPrimarySchools,
        minimumSecondarySchools=data.minimumSecondarySchools,
        minimumTertiarySchools=data.minimumTertiarySchools,
        minimumMalls=data.minimumMalls,
        minimumHospitals=data.minimumHospitals,
    )


def _parseCount(value: Any) -> int:
    """Parse a non-negative whole-number minimum count."""
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        raise ValueError("Minimum amenity counts must be whole numbers")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError("Minimum amenity counts must be whole numbers")
    number = int(value)
    if number < 0:
        raise ValueError("Minimum amenity counts cannot be negative")
    return number


def _parseDatetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
