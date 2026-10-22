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

    def test_weight_above_ten_is_rejected(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"][-1]["weightValue"] = 11
        result = InputValidationControl().validateProfileData(profileDtoFromDict(payload))
        self.assertFalse(result.isValid)
        self.assertIn(
            "Importance for AMENITIES_DENSITY must be between 1 and 10.",
            [error.message for error in result.errors],
        )

    def test_weight_below_one_is_rejected(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"][-1]["weightValue"] = 0
        result = InputValidationControl().validateProfileData(profileDtoFromDict(payload))
        self.assertFalse(result.isValid)
        self.assertIn(
            "Importance for AMENITIES_DENSITY must be between 1 and 10.",
            [error.message for error in result.errors],
        )

    def test_ratings_do_not_need_to_sum_to_100(self) -> None:
        payload = profilePayload()
        for index, rating in enumerate([1, 2, 3, 4, 5]):
            payload["criteriaWeights"][index]["weightValue"] = rating
        result = InputValidationControl().validateProfileData(profileDtoFromDict(payload))
        self.assertTrue(result.isValid, [error.message for error in result.errors])

    def test_valid_profile_is_accepted(self) -> None:
        result = InputValidationControl(FakeOneMap()).validateProfileData(
            profileDtoFromDict(profilePayload())
        )
        self.assertTrue(result.isValid, [error.message for error in result.errors])


if __name__ == "__main__":
    unittest.main()
