"""Formal black-box tests for profile validation (equivalence classes + BVA).

The suite treats the validation boundary as a black box: it submits JSON-style
profile payloads through ``handlers.validateProfile`` and inspects only the
returned envelope. No validator internals are called directly.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.api import handlers
from app.control.input_validation_control import InputValidationControl
from tests.support import FakeOneMap, profilePayload


class ExplodingOneMap:
    """Address adapter that simulates a OneMap outage."""

    def searchAddress(self, query: str):
        raise RuntimeError("OneMap unavailable")


def validate(payload, adapter=None):
    """Submit one payload through the validation boundary."""
    context = SimpleNamespace(
        validator=InputValidationControl(adapter or FakeOneMap())
    )
    return handlers.validateProfile(payload, context)


class BlackBoxValidationTests(unittest.TestCase):
    """EP and BVA cases for ``POST /api/v1/profiles/validate`` semantics."""

    def assertAccepted(self, payload) -> None:
        result = validate(payload)
        self.assertTrue(result.success, result.error)
        self.assertIsNotNone(result.data)
        self.assertTrue(
            result.data["isValid"],
            [error["message"] for error in result.data["errors"]],
        )
        self.assertEqual(result.data["errors"], [])

    def assertRejected(self, payload, message: str, field: str) -> None:
        result = validate(payload)
        self.assertTrue(result.success, result.error)
        self.assertFalse(result.data["isValid"])
        messages = [error["message"] for error in result.data["errors"]]
        fields = [error["field"] for error in result.data["errors"]]
        self.assertIn(message, messages)
        self.assertIn(field, fields)

    def assertParseRejected(self, payload) -> None:
        result = validate(payload)
        self.assertFalse(result.success)
        self.assertEqual(result.error.code, "INVALID_PROFILE")

    # ------------------------------------------------------------------
    # Baseline and equivalence classes
    # ------------------------------------------------------------------
    def test_bb_val_01_valid_profile_is_accepted(self) -> None:
        self.assertAccepted(profilePayload())

    def test_bb_val_02_empty_profile_name_is_rejected(self) -> None:
        payload = profilePayload()
        payload["profileName"] = ""
        self.assertRejected(payload, "Enter a profile name.", "profileName")

    def test_bb_val_03_whitespace_profile_name_is_rejected(self) -> None:
        payload = profilePayload()
        payload["profileName"] = "   "
        self.assertRejected(payload, "Enter a profile name.", "profileName")

    def test_bb_val_04_negative_budget_minimum_is_rejected(self) -> None:
        payload = profilePayload()
        payload["budgetMin"] = -1
        self.assertRejected(
            payload,
            "Budget minimum cannot be negative.",
            "budgetMin",
        )

    def test_bb_val_05_zero_budget_maximum_is_rejected(self) -> None:
        payload = profilePayload()
        payload["budgetMax"] = 0
        self.assertRejected(
            payload,
            "Budget maximum must be greater than zero.",
            "budgetMax",
        )

    def test_bb_val_06_equal_budget_bounds_are_rejected(self) -> None:
        payload = profilePayload()
        payload["budgetMin"] = 500000
        payload["budgetMax"] = 500000
        self.assertRejected(
            payload,
            "Budget maximum must be greater than the minimum.",
            "budgetMax",
        )

    def test_bb_val_07_empty_flat_type_list_is_rejected(self) -> None:
        payload = profilePayload()
        payload["selectedFlatTypes"] = []
        self.assertRejected(
            payload,
            "Select at least one flat type to continue.",
            "selectedFlatTypes",
        )

    def test_bb_val_08_missing_workplace_and_anchor_is_rejected(self) -> None:
        payload = profilePayload()
        payload["workplaceAddress"] = None
        payload["anchorCoordinates"] = None
        self.assertRejected(
            payload,
            "Enter a workplace address or select a map anchor.",
            "workplaceAddress",
        )

    def test_bb_val_09_anchor_without_address_is_accepted(self) -> None:
        payload = profilePayload()
        payload["workplaceAddress"] = None
        self.assertAccepted(payload)

    def test_bb_val_10_address_without_anchor_is_accepted(self) -> None:
        payload = profilePayload()
        payload["anchorCoordinates"] = None
        self.assertAccepted(payload)

    def test_bb_val_11_unresolvable_address_is_rejected(self) -> None:
        payload = profilePayload()
        payload["workplaceAddress"] = "999999 Fake Street"
        payload["anchorCoordinates"] = None
        result = validate(payload, FakeOneMap(matches=[]))
        self.assertTrue(result.success, result.error)
        self.assertFalse(result.data["isValid"])
        self.assertIn(
            "Address not Found. Enter a valid postal code or building name.",
            [error["message"] for error in result.data["errors"]],
        )

    def test_bb_val_12_address_lookup_failure_is_rejected(self) -> None:
        payload = profilePayload()
        payload["anchorCoordinates"] = None
        result = validate(payload, ExplodingOneMap())
        self.assertTrue(result.success, result.error)
        self.assertFalse(result.data["isValid"])
        self.assertIn(
            "Unable to verify the address. Try again.",
            [error["message"] for error in result.data["errors"]],
        )

    def test_bb_val_13_empty_criteria_weights_are_rejected(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"] = []
        self.assertRejected(
            payload,
            "Rate at least one criterion.",
            "criteriaWeights",
        )

    def test_bb_val_14_unknown_criterion_is_rejected(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"][0]["criterionId"] = "NOT_A_CRITERION"
        self.assertRejected(
            payload,
            "Unknown criterion: NOT_A_CRITERION.",
            "criteriaWeights",
        )

    def test_bb_val_15_missing_commute_mode_defaults_to_public_transport(self) -> None:
        payload = profilePayload()
        payload.pop("preferredCommuteMode")
        self.assertAccepted(payload)

    def test_bb_val_16_invalid_commute_mode_is_rejected_at_parse(self) -> None:
        payload = profilePayload()
        payload["preferredCommuteMode"] = "CYCLING"
        self.assertParseRejected(payload)

    def test_bb_val_17_multiple_flat_types_are_accepted(self) -> None:
        payload = profilePayload()
        payload["selectedFlatTypes"] = ["3 ROOM", "4 ROOM", "EXECUTIVE"]
        self.assertAccepted(payload)

    def test_bb_val_18_lowercase_flat_types_are_normalised(self) -> None:
        payload = profilePayload()
        payload["selectedFlatTypes"] = ["4 room"]
        self.assertAccepted(payload)

    # ------------------------------------------------------------------
    # Boundary-value analysis: importance ratings
    # ------------------------------------------------------------------
    def test_bb_val_19_weight_zero_is_rejected(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"][0]["weightValue"] = 0
        self.assertRejected(
            payload,
            "Importance for PRICE must be between 1 and 10.",
            "criteriaWeights",
        )

    def test_bb_val_20_weight_one_is_accepted(self) -> None:
        payload = profilePayload()
        for weight in payload["criteriaWeights"]:
            weight["weightValue"] = 1
        self.assertAccepted(payload)

    def test_bb_val_21_weight_ten_is_accepted(self) -> None:
        payload = profilePayload()
        for weight in payload["criteriaWeights"]:
            weight["weightValue"] = 10
        self.assertAccepted(payload)

    def test_bb_val_22_weight_eleven_is_rejected(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"][0]["weightValue"] = 11
        self.assertRejected(
            payload,
            "Importance for PRICE must be between 1 and 10.",
            "criteriaWeights",
        )

    # ------------------------------------------------------------------
    # Boundary-value analysis: budgets
    # ------------------------------------------------------------------
    def test_bb_val_23_budget_min_zero_is_accepted(self) -> None:
        payload = profilePayload()
        payload["budgetMin"] = 0
        self.assertAccepted(payload)

    def test_bb_val_24_budget_max_one_above_minimum_is_accepted(self) -> None:
        payload = profilePayload()
        payload["budgetMin"] = 500000
        payload["budgetMax"] = 500001
        self.assertAccepted(payload)

    # ------------------------------------------------------------------
    # Boundary-value analysis: hard amenity minimums
    # ------------------------------------------------------------------
    def test_bb_val_25_each_minimum_accepts_zero(self) -> None:
        payload = profilePayload()
        for field in (
            "minimumPrimarySchools",
            "minimumSecondarySchools",
            "minimumTertiarySchools",
            "minimumMalls",
            "minimumHospitals",
        ):
            payload[field] = 0
        self.assertAccepted(payload)

    def test_bb_val_26_each_minimum_accepts_fifty(self) -> None:
        for field in (
            "minimumPrimarySchools",
            "minimumSecondarySchools",
            "minimumTertiarySchools",
            "minimumMalls",
            "minimumHospitals",
        ):
            with self.subTest(field=field):
                payload = profilePayload()
                payload[field] = 50
                self.assertAccepted(payload)

    def test_bb_val_27_each_minimum_rejects_fifty_one(self) -> None:
        cases = (
            ("minimumPrimarySchools", "Primary school"),
            ("minimumSecondarySchools", "Secondary school"),
            ("minimumTertiarySchools", "Tertiary school"),
            ("minimumMalls", "Mall"),
            ("minimumHospitals", "Hospital"),
        )
        for field, label in cases:
            with self.subTest(field=field):
                payload = profilePayload()
                payload[field] = 51
                self.assertRejected(
                    payload,
                    f"{label} minimum must be between 0 and 50.",
                    field,
                )

    def test_bb_val_28_each_minimum_rejects_negative_values_at_parse(self) -> None:
        for field in (
            "minimumPrimarySchools",
            "minimumSecondarySchools",
            "minimumTertiarySchools",
            "minimumMalls",
            "minimumHospitals",
        ):
            with self.subTest(field=field):
                payload = profilePayload()
                payload[field] = -1
                self.assertParseRejected(payload)

    def test_bb_val_29_each_minimum_rejects_non_integer_values_at_parse(self) -> None:
        for field in (
            "minimumPrimarySchools",
            "minimumSecondarySchools",
            "minimumTertiarySchools",
            "minimumMalls",
            "minimumHospitals",
        ):
            with self.subTest(field=field):
                payload = profilePayload()
                payload[field] = 1.5
                self.assertParseRejected(payload)

    def test_bb_val_30_each_minimum_rejects_boolean_values_at_parse(self) -> None:
        for field in (
            "minimumPrimarySchools",
            "minimumSecondarySchools",
            "minimumTertiarySchools",
            "minimumMalls",
            "minimumHospitals",
        ):
            with self.subTest(field=field):
                payload = profilePayload()
                payload[field] = True
                self.assertParseRejected(payload)

    def test_bb_val_31_numeric_string_minimum_is_accepted(self) -> None:
        payload = profilePayload()
        payload["minimumMalls"] = "5"
        self.assertAccepted(payload)

    def test_bb_val_32_each_minimum_accepts_interior_values(self) -> None:
        for field in (
            "minimumPrimarySchools",
            "minimumSecondarySchools",
            "minimumTertiarySchools",
            "minimumMalls",
            "minimumHospitals",
        ):
            for value in (1, 49):
                with self.subTest(field=field, value=value):
                    payload = profilePayload()
                    payload[field] = value
                    self.assertAccepted(payload)

    def test_bb_val_33_budget_min_one_is_accepted(self) -> None:
        payload = profilePayload()
        payload["budgetMin"] = 1
        self.assertAccepted(payload)

    def test_bb_val_34_budget_max_one_is_accepted(self) -> None:
        payload = profilePayload()
        payload["budgetMin"] = 0
        payload["budgetMax"] = 1
        self.assertAccepted(payload)

    def test_bb_val_35_single_criterion_is_accepted(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"] = [payload["criteriaWeights"][0]]
        self.assertAccepted(payload)

    def test_bb_val_36_all_commute_modes_are_accepted(self) -> None:
        for mode in ("PUBLIC_TRANSIT", "DRIVING", "WALKING"):
            with self.subTest(mode=mode):
                payload = profilePayload()
                payload["preferredCommuteMode"] = mode
                self.assertAccepted(payload)

    def test_bb_val_37_fractional_weight_within_range_is_accepted(self) -> None:
        payload = profilePayload()
        payload["criteriaWeights"][0]["weightValue"] = 1.5
        self.assertAccepted(payload)


if __name__ == "__main__":
    unittest.main()
