from typing import TYPE_CHECKING, Optional

from app.entity.enums import TransitMode
from app.entity.types import ValidationResult
from app.strategy.criterion_catalog import buildDefaultCriterionCatalog

if TYPE_CHECKING:
    from app.adapter.one_map_api_adapter import OneMapApiAdapter
    from app.schemas.profile_dto import ProfileDTO


class InputValidationControl:
    def __init__(self, oneMapAdapter: Optional[OneMapApiAdapter] = None):
        self.oneMapAdapter = oneMapAdapter

    def validateProfileData(self, data: 'ProfileDTO') -> ValidationResult:
        result = ValidationResult(isValid=True, errors=[])

        # Profile name
        profile_name = getattr(data, 'profileName', None)
        if not profile_name or not str(profile_name).strip():
            result.addError("profileName", "Profile name must not be empty or contain only whitespace.")

        # Budget
        budget_min = getattr(data, 'budgetMin', None)
        budget_max = getattr(data, 'budgetMax', None)

        if not isinstance(budget_min, (int, float)) or budget_min < 0:
            result.addError("budgetMin", "budgetMin must be greater than or equal to 0.")

        if not isinstance(budget_max, (int, float)) or budget_max <= 0:
            result.addError("budgetMax", "budgetMax must be greater than 0.")

        if isinstance(budget_min, (int, float)) and isinstance(budget_max, (int, float)):
            if budget_max <= budget_min:
                result.addError("budgetMax", "budgetMax must be strictly greater than budgetMin.")

        # Flat types
        selected_flat_types = getattr(data, 'selectedFlatTypes', None)
        if not selected_flat_types or len(selected_flat_types) == 0:
            result.addError("selectedFlatTypes", "selectedFlatTypes must contain at least one selected flat type.")

        # Workplace address
        workplace_address = getattr(data, 'workplaceAddress', None)
        anchor_coordinates = getattr(data, 'anchorCoordinates', None)
        has_address = bool(workplace_address and str(workplace_address).strip())
        has_coordinates = bool(anchor_coordinates)

        if not has_address and not has_coordinates:
            result.addError(
                "workplaceAddress",
                "The user must provide either a non-empty workplaceAddress or anchorCoordinates."
            )
        elif has_address and self.oneMapAdapter is not None:
            try:
                matches = self.oneMapAdapter.searchAddress(workplace_address)
                if not matches:
                    result.addError("workplaceAddress", "The provided workplace address could not be found.")
            except Exception as e:
                result.addError("workplaceAddress", f"Address verification failed: {str(e)}")

        # Criteria weights
        criteria_weights = getattr(data, 'criteriaWeights', None)
        if not criteria_weights:
            result.addError("criteriaWeights", "At least one criterion weight must be provided.")
        else:
            catalog = buildDefaultCriterionCatalog().getAllCriteria()

            # Defensively handle the catalog returning either a dict or a list of objects
            valid_ids = set(catalog.keys()) if isinstance(catalog, dict) else {getattr(c, 'id', c) for c in catalog}

            # Defensively handle criteriaWeights as a dict or an iterable of objects
            items = criteria_weights.items() if isinstance(criteria_weights, dict) else [
                (getattr(cw, 'criterionId', cw), getattr(cw, 'weight', cw)) for cw in criteria_weights
            ]

            for c_id, weight in items:
                if c_id not in valid_ids:
                    result.addError("criteriaWeights", f"Unknown criterion ID: {c_id}")
                if not isinstance(weight, (int, float)) or not (1.0 <= weight <= 10.0):
                    result.addError("criteriaWeights", f"Criterion weight for '{c_id}' must be between 1.0 and 10.0, inclusive.")

        # Minimum amenities
        amenity_fields = [
            "minimumPrimarySchools",
            "minimumSecondarySchools",
            "minimumTertiarySchools",
            "minimumMalls",
            "minimumHospitals"
        ]
        for field in amenity_fields:
            val = getattr(data, field, None)

            # Checking specifically for type 'int' excludes 'bool', since type(True) is bool, not int.
            if type(val) is not int:
                result.addError(field, f"{field} must be an integer, excluding Boolean values.")
            elif not (0 <= val <= 50):
                result.addError(field, f"{field} must be between 0 and 50, inclusive.")

        # Preferred commute mode
        commute_mode = getattr(data, 'preferredCommuteMode', None)
        if not isinstance(commute_mode, TransitMode):
            try:
                TransitMode(commute_mode)
            except (ValueError, TypeError):
                result.addError("preferredCommuteMode", "preferredCommuteMode must be a valid member of the TransitMode enumeration.")

        return result