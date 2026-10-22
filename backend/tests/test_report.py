"""Unit tests for PDF generation, secure metadata and share URLs."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

from app.api.handlers import decodeShare
from app.container.report_store import ReportStore
from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.control.report_control import ReportControl
from app.entity.amenity_info import AmenityInfo
from app.entity.commute_estimate import CommuteEstimate
from app.entity.criterion_score import CriterionScore
from app.entity.enums import TransitMode
from app.entity.environment_info import EnvironmentInfo
from app.entity.house_pricing import HousePricing
from app.entity.recommendation_item import RecommendationItem
from app.entity.recommendation_set import RecommendationSet
from app.entity.types import Coordinates
from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO
from tests.support import make_profile


class ReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="sgpropfinder-test-")
        self.control = ReportControl(
            DataAvailabilityNotifier(),
            ReportStore(),
            reportDir=self.temp_dir,
        )
        self.profile = make_profile()
        self.data_as_of = datetime(2026, 10, 21, 8, 30, tzinfo=timezone.utc)
        self.recommendations = RecommendationSet(
            "profile-1",
            datetime.now(timezone.utc),
            "TEST-SNAPSHOT",
            self.data_as_of,
            profileSnapshot={
                "profileName": "Test Profile",
                "budgetMin": 0,
                "budgetMax": 600000,
                "selectedFlatTypes": ["4 ROOM"],
                "workplaceAddress": "Raffles Place",
                "preferredCommuteMode": "PUBLIC_TRANSIT",
                "criteriaWeights": [
                    {"criterionId": "PRICE", "weightValue": 2},
                    {"criterionId": "COMMUTE_TIME", "weightValue": 2},
                    {"criterionId": "SCHOOL_PROXIMITY", "weightValue": 2},
                    {"criterionId": "GREEN_COVERAGE", "weightValue": 2},
                    {"criterionId": "AMENITIES_DENSITY", "weightValue": 2},
                ],
            },
        )
        self.recommendations.addItem(
            RecommendationItem(
                "TAMPINES01",
                "Tampines East",
                1,
                88.5,
                [
                    CriterionScore("PRICE", 500000, 0.75, 0.2, 0.15, False, "HDB"),
                    CriterionScore("COMMUTE_TIME", 35, 0.61, 0.2, 0.122, False, "OneMap"),
                    CriterionScore("SCHOOL_PROXIMITY", 2, 0.5, 0.2, 0.1, False, "MOE"),
                    CriterionScore("GREEN_COVERAGE", 35.5, 0.355, 0.2, 0.071, False, "NParks"),
                    CriterionScore("AMENITIES_DENSITY", 3, 0.3, 0.2, 0.06, False, "OneMap"),
                ],
            )
        )
        self.details = [
            NeighborhoodDetailDTO(
                subzoneCode="TAMPINES01",
                subzoneName="Tampines East",
                pricing={
                    "4 ROOM": HousePricing(
                        500000,
                        5000,
                        "Rising",
                        2.0,
                        "4 ROOM",
                        6,
                        True,
                        asOf=self.data_as_of,
                    )
                },
                amenities=[AmenityInfo("Tampines Park", "park", Coordinates(1.35, 103.94), 0.1)],
                environment=EnvironmentInfo(
                    "Partly Cloudy", 35.5, 18.0, 7.0, "TL", asOf=self.data_as_of
                ),
                commute=CommuteEstimate(
                    35, 14.2, 1, TransitMode.PUBLIC_TRANSIT, departureTime=self.data_as_of
                ),
                warnings=[],
                generatedTime=self.data_as_of,
            )
        ]

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pdf_is_generated_with_secure_metadata(self) -> None:
        report = self.control.generatePdfReport(self.recommendations, self.details)
        path = Path(self.temp_dir) / report.fileName
        self.assertTrue(path.exists())
        self.assertGreater(report.sizeBytes, 0)
        self.assertTrue(path.read_bytes().startswith(b"%PDF"))
        self.assertTrue(report.downloadUrl.startswith("/api/v1/reports/download/"))
        self.assertGreater(report.expiresAt, report.generatedTime)
        self.assertIsNotNone(self.control.reportStore.getPath(report.reportId))

    def test_pdf_contains_weighting_scores_dates_and_caveats(self) -> None:
        report = self.control.generatePdfReport(self.recommendations, self.details)
        reader = PdfReader(str(Path(self.temp_dir) / report.fileName))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in [
            "Profile and weighting",
            "Importance (1-10)",
            "Relative weight",
            "Criterion scores",
            "Data dates",
            "Caveats",
            "town proxy",
            "Housing affordability",
        ]:
            self.assertIn(expected, text)

    def test_export_to_file(self) -> None:
        report = self.control.generatePdfReport(self.recommendations, self.details)
        target = Path(self.temp_dir) / "exported.pdf"
        self.assertTrue(self.control.exportToFile(report, str(target)))
        self.assertTrue(target.exists())

    def test_share_url_round_trip(self) -> None:
        url = self.control.generateShareableUrl(self.profile, ["TAMPINES01", "BEDOK01"], "/")
        share = url.split("share=", 1)[1]
        profile_payload, subzones = decodeShare(share)
        self.assertEqual(profile_payload["profileId"], "profile-1")
        self.assertEqual(subzones, ["TAMPINES01", "BEDOK01"])


if __name__ == "__main__":
    unittest.main()
