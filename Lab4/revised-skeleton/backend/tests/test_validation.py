"""Black-box style validation tests for InputValidationControl."""

from __future__ import annotations

import unittest

from app.control.input_validation_control import InputValidationControl
from app.entity.address_match import AddressMatch
from app.entity.types import Coordinates
from app.services.profile_factory import profileDtoFromDict
from tests.support import FakeOneMap, profilePayload


class ValidationTests(unittest.TestCase):
    def test_missing_flat_type_is_rejected(self) -> None:
        payload = profilePayload()
        payload["selectedFlatTypes"] = []
        result = InputValidationControl().validateProfileData(profileDtoFromDict(payload))
        self.assertFalse(result.isValid)
        self.assertIn(
            "Select at least one flat type to continue.",
            [error.message for error in result.errors],
        )

    def test_unresolvable_address_is_rejected(self) -> None:
        payload = profilePayload()
        payload["workplaceAddress"] = "999999 Fake St"
        payload["anchorCoordinates"] = None
        result = InputValidationControl(FakeOneMap(matches=[])).validateProfileData(
            profileDtoFromDict(payload)
        )
        self.assertFalse(result.isValid)
        self.assertIn(
            "Address not Found. Enter a valid postal code or building name.",
            [error.message for error in result.errors],
        )

    def test_weight_total_above_hundred_is_rejected(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"][-1]["weightValue"] = 20.1
        result = InputValidationControl().validateProfileData(profileDtoFromDict(payload))
        self.assertFalse(result.isValid)
        self.assertIn("Criteria weights must total 100%.", [error.message for error in result.errors])

    def test_weight_total_at_boundary_is_accepted(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"][-1]["weightValue"] = 20.1
        payload["criteriaWeights"][0]["weightValue"] = 19.9
        result = InputValidationControl().validateProfileData(profileDtoFromDict(payload))
        self.assertTrue(result.isValid)

    def test_valid_profile_is_accepted(self) -> None:
        result = InputValidationControl(FakeOneMap()).validateProfileData(
            profileDtoFromDict(profilePayload())
        )
        self.assertTrue(result.isValid, [error.message for error in result.errors])


if __name__ == "__main__":
    unittest.main()
