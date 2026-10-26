"""Unit tests for live/snapshot dataset selection."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.entity.dataset_metadata import DatasetMetadata
from app.entity.types import RawResponse
from app.services.dataset_service import HDB_DATASET_ID, SUBZONE_DATASET_ID, DatasetService
from tests.support import FIXTURES


class FakeDataGov:
    def __init__(self, subzones: dict, rows: list[dict], fail: bool = False) -> None:
        self.subzones = subzones
        self.rows = rows
        self.fail = fail
        self.calls = []
        self.lastMetadata = DatasetMetadata(
            dataSnapshotId="LIVE:test",
            dataAsOf=datetime.now(timezone.utc),
            sourceUrl="https://data.gov.sg/test",
            recordCount=len(rows),
        )

    def fetchDataset(self, dataset_id: str) -> RawResponse:
        self.calls.append(dataset_id)
        if self.fail:
            raise RuntimeError("simulated data.gov.sg failure")
        body = self.subzones if dataset_id == SUBZONE_DATASET_ID else {"rows": self.rows}
        return RawResponse(200, body, {}, datetime.now(timezone.utc))


class DatasetServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="dataset-service-"))
        shutil.copy(FIXTURES / "subzones.geojson", self.temp / "subzones.geojson")
        shutil.copy(FIXTURES / "hdb_resale.csv", self.temp / "hdb_resale.csv")
        self.subzones = json.loads((FIXTURES / "subzones.geojson").read_text(encoding="utf-8"))
        with (FIXTURES / "hdb_resale.csv").open("r", encoding="utf-8") as handle:
            import csv

            self.rows = [dict(row) for row in csv.DictReader(handle)]

    def tearDown(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)

    def test_local_snapshots_are_used_first(self) -> None:
        adapter = FakeDataGov(self.subzones, self.rows)
        service = DatasetService(adapter, self.temp)
        payload = service.getSubzones()
        rows = service.getHdbRows()
        self.assertEqual(len(payload["features"]), 3)
        self.assertEqual(len(rows), 28)
        self.assertEqual(adapter.calls, [])
        self.assertEqual(service.status()["subzones"]["source"], "local-snapshot")

    def test_live_refresh_updates_snapshots(self) -> None:
        adapter = FakeDataGov(self.subzones, self.rows)
        service = DatasetService(adapter, self.temp)
        status = service.refresh()
        self.assertEqual(status["subzones"].source, "data.gov.sg:live")
        self.assertEqual(status["hdb"].recordCount, 28)
        self.assertIn(SUBZONE_DATASET_ID, adapter.calls)
        self.assertIn(HDB_DATASET_ID, adapter.calls)

    def test_live_failure_keeps_local_snapshot(self) -> None:
        adapter = FakeDataGov(self.subzones, self.rows, fail=True)
        service = DatasetService(adapter, self.temp)
        service.refresh()
        status = service.status()
        self.assertEqual(status["subzones"]["lastError"], "simulated data.gov.sg failure")
        self.assertTrue(status["subzones"]["isStale"])


if __name__ == "__main__":
    unittest.main()
