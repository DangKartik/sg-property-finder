"""Black-box state-transition tests for the short-lived PDF report lifecycle.

The report endpoint is modelled as a finite-state machine:

    EMPTY --generate--> AVAILABLE --expire--> EXPIRED
    AVAILABLE --download/export--> AVAILABLE
    EXPIRED --generate--> AVAILABLE
    EMPTY/EXPIRED --read--> MISSING

Only the public API is used: ``ReportControl`` creates reports and
``ReportStore``/``handlers.reportPath`` read them. The clock is injected into
the store so expiry can be tested without sleeping. The expected/actual matrix
is in ``docs/BLACK_BOX_TESTING.md``.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from app.api import handlers
from app.container.report_store import ReportStore
from app.control.data_availability_notifier import DataAvailabilityNotifier
from app.control.report_control import ReportControl
from app.entity.recommendation_set import RecommendationSet


class MutableClock:
    """Controllable UTC clock for report-expiry transitions."""

    def __init__(self, now: datetime) -> None:
        self.current = now

    def __call__(self) -> datetime:
        return self.current

    def advance(self, **kwargs: int) -> None:
        self.current += timedelta(**kwargs)


class ReportLifecycleStateTests(unittest.TestCase):
    """State-transition coverage for ``POST /reports/pdf`` and downloads."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="sgpropfinder-state-")
        self.clock = MutableClock(datetime.now(timezone.utc))
        self.store = ReportStore(clock=self.clock)
        self.control = ReportControl(
            DataAvailabilityNotifier(),
            reportStore=self.store,
            reportDir=self.temp_dir,
            clock=self.clock,
        )
        self.recommendations = RecommendationSet(
            profileId="profile-state",
            generatedTime=self.clock.current,
            dataSnapshotId="BB-STATE",
            dataAsOf=self.clock.current,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def generate(self):
        """Transition EMPTY -> AVAILABLE by generating a real PDF."""
        return self.control.generatePdfReport(self.recommendations, [])

    def assertReportAvailable(self, report_id: str) -> Path:
        path = self.store.getPath(report_id)
        self.assertIsNotNone(path)
        assert path is not None
        self.assertTrue(path.exists())
        return path

    # ------------------------------------------------------------------
    # Independent transition tests: each starts from a fresh state.
    # ------------------------------------------------------------------
    def test_bb_state_01_generate_moves_empty_to_available(self) -> None:
        self.assertIsNone(self.store.getPath("unknown"))
        report = self.generate()

        self.assertIsNotNone(report.reportId)
        self.assertGreater(report.expiresAt, report.generatedTime)
        self.assertTrue(report.fileName.endswith(".pdf"))
        self.assertTrue(report.sizeBytes > 0)
        self.assertReportAvailable(report.reportId)

    def test_bb_state_02_read_available_keeps_state(self) -> None:
        report = self.generate()
        context = SimpleNamespace(reportStore=self.store)

        first = handlers.reportPath(report.reportId, context)
        second = handlers.reportPath(report.reportId, context)

        self.assertIsNotNone(first)
        self.assertEqual(first, second)
        assert first is not None
        self.assertTrue(first.exists())

    def test_bb_state_03_expiry_moves_available_to_expired(self) -> None:
        report = self.generate()
        path = self.assertReportAvailable(report.reportId)

        self.clock.advance(minutes=16)

        self.assertIsNone(self.store.getPath(report.reportId))
        self.assertFalse(path.exists())
        # Reading the expired state again must remain MISSING.
        self.assertIsNone(self.store.getPath(report.reportId))

    def test_bb_state_04_export_available_keeps_state(self) -> None:
        report = self.generate()
        target = Path(self.temp_dir) / "exported.pdf"

        self.assertTrue(self.control.exportToFile(report, str(target)))
        self.assertTrue(target.exists())
        self.assertTrue(target.read_bytes().startswith(b"%PDF"))
        self.assertIsNotNone(self.store.getPath(report.reportId))

    def test_bb_state_05_export_expired_returns_false(self) -> None:
        report = self.generate()
        target = Path(self.temp_dir) / "expired-export.pdf"
        self.clock.advance(minutes=16)

        self.assertFalse(self.control.exportToFile(report, str(target)))
        self.assertFalse(target.exists())

    def test_bb_state_06_regenerate_after_expiry_moves_expired_to_available(self) -> None:
        first = self.generate()
        self.clock.advance(minutes=16)
        self.assertIsNone(self.store.getPath(first.reportId))

        second = self.generate()

        self.assertNotEqual(second.reportId, first.reportId)
        self.assertIsNone(self.store.getPath(first.reportId))
        self.assertReportAvailable(second.reportId)

    def test_bb_state_07_unknown_report_id_stays_missing(self) -> None:
        self.assertIsNone(self.store.getPath("does-not-exist"))
        self.assertIsNone(
            handlers.reportPath(
                "does-not-exist",
                SimpleNamespace(reportStore=self.store),
            )
        )

    # ------------------------------------------------------------------
    # Cascading test: steps depend on the previous transition succeeding.
    # ------------------------------------------------------------------
    def test_bb_state_08_cascading_report_lifecycle(self) -> None:
        report = self.generate()  # EMPTY -> AVAILABLE
        self.assertReportAvailable(report.reportId)

        target = Path(self.temp_dir) / "cascade.pdf"
        self.assertTrue(self.control.exportToFile(report, str(target)))  # READ
        self.assertTrue(target.exists())

        self.clock.advance(minutes=16)  # AVAILABLE -> EXPIRED
        self.assertIsNone(self.store.getPath(report.reportId))
        # The exported copy is independent of the server-side report file.
        self.assertTrue(target.exists())

        replacement = self.generate()  # EXPIRED -> AVAILABLE
        self.assertReportAvailable(replacement.reportId)
        self.assertIsNone(self.store.getPath(report.reportId))


if __name__ == "__main__":
    unittest.main()
