"""Profile input validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.entity.enums import TransitMode
from app.entity.types import ValidationResult
from app.strategy.criterion_catalog import buildDefaultCriterionCatalog

if TYPE_CHECKING:
    from app.adapter.one_map_api_adapter import OneMapApiAdapter
    from app.schemas.profile_dto import ProfileDTO


class InputValidationControl:
    """Stereotype: Control. Validates profile input before persistence or ranking."""

    def __init__(self, oneMapAdapter: OneMapApiAdapter | None = None) -> None:
        """Create the validator, optionally with address verification."""
        self.oneMapAdapter = oneMapAdapter

    def validateProfileData(self, data: ProfileDTO) -> ValidationResult:
        """Validate budget, flat types, address, mode and weights."""
        result = ValidationResult(isValid=True, errors=[])

        if not data.profileName or not data.profileName.strip():
            result.addError("profileName", "Enter a profile name.")

        if data.budgetMin < 0:
            result.addError("budgetMin", "Budget minimum cannot be negative.")
        if data.budgetMax <= 0:
            result.addError("budgetMax", "Budget maximum must be greater than zero.")
        if data.budgetMax <= data.budgetMin:
            result.addError("budgetMax", "Budget maximum must be greater than the minimum.")

        if not data.selectedFlatTypes:
            result.addError("selectedFlatTypes", "Select at least one flat type to continue.")

        if not data.workplaceAddress and data.anchorCoordinates is None:
            result.addError("workplaceAddress", "Enter a workplace address or select a map anchor.")

        if data.workplaceAddress and self.oneMapAdapter is not None:
            try:
                matches = self.oneMapAdapter.searchAddress(data.workplaceAddress)
            except Exception:
                result.addError("workplaceAddress", "Unable to verify the address. Try again.")
                matches = []
            if not matches:
                result.addError(
                    "workplaceAddress",
                    "Address not Found. Enter a valid postal code or building name.",
                )

        valid_criteria = {
            definition.criterionId
            for definition in buildDefaultCriterionCatalog().getAllCriteria()
        }
        if not data.criteriaWeights:
            result.addError("criteriaWeights", "Rate at least one criterion.")
        else:
            for weight in data.criteriaWeights:
                if weight.getCriterionId() not in valid_criteria:
                    result.addError(
                        "criteriaWeights",
                        f"Unknown criterion: {weight.getCriterionId()}.",
                    )
                value = weight.getWeightValue()
                if value < 1.0 or value > 10.0:
                    result.addError(
                        "criteriaWeights",
                        f"Importance for {weight.getCriterionId()} must be between 1 and 10.",
                    )

        for field_name, label in (
            ("minimumPrimarySchools", "Primary school"),
            ("minimumSecondarySchools", "Secondary school"),
            ("minimumTertiarySchools", "Tertiary school"),
            ("minimumMalls", "Mall"),
            ("minimumHospitals", "Hospital"),
        ):
            value = getattr(data, field_name)
            if not isinstance(value, int) or isinstance(value, bool):
                result.addError(field_name, f"{label} minimum must be a whole number.")
            elif value < 0 or value > 50:
                result.addError(
                    field_name,
                    f"{label} minimum must be between 0 and 50.",
                )

        if not isinstance(data.preferredCommuteMode, TransitMode):
            result.addError("preferredCommuteMode", "Select a valid commute mode.")

        return result
