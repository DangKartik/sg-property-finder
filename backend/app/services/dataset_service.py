"""Live data.gov.sg dataset service with local snapshots and freshness checks."""

from __future__ import annotations

import csv
import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.adapter.data_gov_sg_adapter import DataGovSgAdapter

SUBZONE_DATASET_ID = "d_8594ae9ff96d0c708bc2af633048edfb"
HDB_DATASET_ID = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"


@dataclass
class DatasetStatus:
    """Freshness metadata exposed to the frontend."""

    datasetId: str
    dataSnapshotId: str
    dataAsOf: datetime
    source: str
    isStale: bool
    recordCount: int
    lastError: str | None = None


class DatasetService:
    """Loads live data.gov.sg datasets with local snapshots as fallback.

    Data is kept in process memory and refreshed from data.gov.sg when the local
    snapshot is older than `maxAgeHours`. The frontend can cache the JSON
    responses in IndexedDB using the `X-Data-As-Of`/`ETag` headers exposed by the
    API later.
    """

    def __init__(
        self,
        dataGovAdapter: DataGovSgAdapter,
        dataDir: Path | str,
        maxAgeHours: int = 24,
    ) -> None:
        """Create the service.

        Args:
            dataGovAdapter: Live data.gov.sg adapter.
            dataDir: Directory containing fallback snapshots.
            maxAgeHours: Maximum snapshot age before a live refresh is attempted.
        """
        self.dataGovAdapter = dataGovAdapter
        self.dataDir = Path(dataDir)
        self.dataDir.mkdir(parents=True, exist_ok=True)
        self.maxAgeHours = maxAgeHours
        self._lock = threading.Lock()
        self._subzones: dict[str, Any] | None = None
        self._hdbRows: list[dict[str, Any]] | None = None
        self._status: dict[str, DatasetStatus] = {}

    def getSubzones(self, preferLive: bool = False) -> dict[str, Any]:
        """Return the subzone FeatureCollection.

        Local snapshots are used first for fast startup; pass `preferLive=True`
        to force a live fetch. The startup refresh calls `refreshIfStale()`.
        """
        with self._lock:
            if self._subzones is not None:
                return self._subzones
            if not preferLive:
                local = self._loadLocalSubzones()
                if local is not None:
                    self._subzones = local
                    return local
            try:
                payload = self._fetchLiveSubzones()
                self._subzones = payload
                return payload
            except Exception as exc:
                local = self._loadLocalSubzones()
                if local is None:
                    raise RuntimeError("Subzone data unavailable from API and local snapshot") from exc
                self._subzones = local
                self._markLocal(
                    "subzones",
                    SUBZONE_DATASET_ID,
                    self.dataDir / "subzones.geojson",
                    str(exc),
                    len(local.get("features", [])),
                )
                return local

    def getHdbRows(self, preferLive: bool = False) -> list[dict[str, Any]]:
        """Return HDB resale rows, using a local snapshot when available."""
        with self._lock:
            if self._hdbRows is not None:
                return self._hdbRows
            if not preferLive:
                local = self._loadLocalHdb()
                if local is not None:
                    self._hdbRows = local
                    return local
            try:
                rows = self._fetchLiveHdb()
                self._hdbRows = rows
                return rows
            except Exception as exc:
                local = self._loadLocalHdb()
                if local is None:
                    raise RuntimeError("HDB data unavailable from API and local snapshot") from exc
                self._hdbRows = local
                self._markLocal(
                    "hdb",
                    HDB_DATASET_ID,
                    self.dataDir / "hdb_resale.csv",
                    str(exc),
                    len(local),
                )
                return local

    def refreshIfStale(self, maxAgeHours: int | None = None) -> dict[str, DatasetStatus]:
        """Refresh from data.gov.sg when local snapshots are older than the limit."""
        limit = maxAgeHours if maxAgeHours is not None else self.maxAgeHours
        subzone_path = self.dataDir / "subzones.geojson"
        hdb_path = self.dataDir / "hdb_resale.csv"
        subzone_age = _ageHours(subzone_path)
        hdb_age = _ageHours(hdb_path)
        if (subzone_age is None or subzone_age > limit) or (hdb_age is None or hdb_age > limit):
            return self.refresh()
        with self._lock:
            if "subzones" not in self._status:
                payload = self._loadLocalSubzones()
                self._markLocal(
                    "subzones",
                    SUBZONE_DATASET_ID,
                    subzone_path,
                    None,
                    len(payload.get("features", [])) if payload else 0,
                )
            if "hdb" not in self._status:
                rows = self._loadLocalHdb()
                self._markLocal("hdb", HDB_DATASET_ID, hdb_path, None, len(rows or []))
            return dict(self._status)

    def refresh(self) -> dict[str, DatasetStatus]:
        """Fetch both datasets from data.gov.sg and update local snapshots."""
        with self._lock:
            try:
                subzones = self._fetchLiveSubzones()
                self._subzones = subzones
            except Exception as exc:
                self._status["subzones"] = self._status.get("subzones") or DatasetStatus(
                    datasetId=SUBZONE_DATASET_ID,
                    dataSnapshotId="LOCAL",
                    dataAsOf=datetime.now(timezone.utc),
                    source="local-snapshot",
                    isStale=True,
                    recordCount=len(self._loadLocalSubzones().get("features", [])) if self._loadLocalSubzones() else 0,
                    lastError=str(exc),
                )
            try:
                rows = self._fetchLiveHdb()
                self._hdbRows = rows
            except Exception as exc:
                self._status["hdb"] = self._status.get("hdb") or DatasetStatus(
                    datasetId=HDB_DATASET_ID,
                    dataSnapshotId="LOCAL",
                    dataAsOf=datetime.now(timezone.utc),
                    source="local-snapshot",
                    isStale=True,
                    recordCount=len(self._loadLocalHdb() or []),
                    lastError=str(exc),
                )
            return dict(self._status)

    def status(self) -> dict[str, Any]:
        """Return freshness metadata for API/status responses."""
        with self._lock:
            return {name: asdict(status) for name, status in self._status.items()}

    def _fetchLiveSubzones(self) -> dict[str, Any]:
        response = self.dataGovAdapter.fetchDataset(SUBZONE_DATASET_ID)
        payload = response.body
        if payload.get("type") != "FeatureCollection":
            raise ValueError("Subzone API payload is not a FeatureCollection")
        target = self.dataDir / "subzones.geojson"
        target.write_text(json.dumps(payload), encoding="utf-8")
        metadata = self.dataGovAdapter.lastMetadata
        self._status["subzones"] = DatasetStatus(
            datasetId=SUBZONE_DATASET_ID,
            dataSnapshotId=metadata.dataSnapshotId if metadata else "LIVE",
            dataAsOf=metadata.dataAsOf if metadata else datetime.now(timezone.utc),
            source="data.gov.sg:live",
            isStale=False,
            recordCount=len(payload.get("features", [])),
        )
        return payload

    def _fetchLiveHdb(self) -> list[dict[str, Any]]:
        response = self.dataGovAdapter.fetchDataset(HDB_DATASET_ID)
        rows = response.body.get("rows", response.body.get("items", []))
        rows = [dict(row) for row in rows if isinstance(row, dict)]
        if not rows:
            raise ValueError("HDB API payload contained no rows")
        target = self.dataDir / "hdb_resale.csv"
        fieldnames = list(rows[0].keys())
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        metadata = self.dataGovAdapter.lastMetadata
        self._status["hdb"] = DatasetStatus(
            datasetId=HDB_DATASET_ID,
            dataSnapshotId=metadata.dataSnapshotId if metadata else "LIVE",
            dataAsOf=metadata.dataAsOf if metadata else datetime.now(timezone.utc),
            source="data.gov.sg:live",
            isStale=False,
            recordCount=len(rows),
        )
        return rows

    def _loadLocalSubzones(self) -> dict[str, Any] | None:
        path = self.dataDir / "subzones.geojson"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("type") != "FeatureCollection":
            return None
        if "subzones" not in self._status:
            self._markLocal(
                "subzones",
                SUBZONE_DATASET_ID,
                path,
                None,
                len(payload.get("features", [])),
            )
        return payload

    def _loadLocalHdb(self) -> list[dict[str, Any]] | None:
        path = self.dataDir / "hdb_resale.csv"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
        if "hdb" not in self._status:
            self._markLocal("hdb", HDB_DATASET_ID, path, None, len(rows))
        return rows

    def _markLocal(
        self,
        name: str,
        dataset_id: str,
        path: Path,
        error: str | None,
        record_count: int = 0,
    ) -> None:
        if not path.exists():
            return
        self._status[name] = DatasetStatus(
            datasetId=dataset_id,
            dataSnapshotId=f"LOCAL:{path.stat().st_mtime_ns}",
            dataAsOf=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
            source="local-snapshot",
            isStale=(_ageHours(path) or 0) > self.maxAgeHours,
            recordCount=record_count,
            lastError=error,
        )


def _ageHours(path: Path) -> float | None:
    if not path.exists():
        return None
    age = datetime.now(timezone.utc) - datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return age.total_seconds() / 3600.0
