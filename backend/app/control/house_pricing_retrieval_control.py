"""HDB resale pricing retrieval with a 12-month window and town proxy."""

from __future__ import annotations

import csv
import json
import statistics
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.control.retrieval_control import RetrievalControl
from app.core.cache import TTLCache
from app.entity.enums import DataAvailabilityCode
from app.entity.house_pricing import HousePricing
from app.entity.types import RawResponse, RetrievalResult

if TYPE_CHECKING:
    from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.data_availability_notifier import DataAvailabilityNotifier


class HousePricingRetrievalControl(RetrievalControl):
    """Stereotype: Control. Retrieves HDB resale pricing by flat type."""

    def __init__(
        self,
        dataGovAdapter: DataGovSgAdapter,
        notifier: DataAvailabilityNotifier,
        dataPath: Path | str | None = None,
        subzoneRegistry: SubzoneRegistry | None = None,
        asOf: date | datetime | str | None = None,
        datasetService: Any | None = None,
    ) -> None:
        """Create the pricing control.

        Args:
            dataGovAdapter: Data.gov.sg adapter for remote/cached data.
            notifier: Stateless warning factory.
            dataPath: Optional local CSV/JSON fallback with HDB rows.
            subzoneRegistry: Registry used to resolve a subzone's HDB town.
            asOf: Optional window end date; defaults to the latest month in data.
            datasetService: Optional live/snapshot dataset service.
        """
        super().__init__(dataGovAdapter, notifier)
        self.dataPath = Path(dataPath) if dataPath else None
        self.subzoneRegistry = subzoneRegistry
        self.datasetService = datasetService
        self._requestedAsOf = asOf
        self._rowsCache = TTLCache(maxsize=4, ttl=300)
        self._byTown: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self._resolvedAsOf: date | None = None

    def fetchData(self, resourceId: str) -> RawResponse:
        """Fetch HDB rows from the live service, local fallback or adapter."""
        if self.datasetService is not None:
            rows = self.datasetService.getHdbRows()
            return RawResponse(
                statusCode=200,
                body={"rows": rows},
                headers={"Content-Type": "application/json"},
                fetchedAt=datetime.now(timezone.utc),
            )
        if self.dataPath and self.dataPath.exists():
            rows = self._readLocalRows(self.dataPath)
            return RawResponse(
                statusCode=200,
                body={"rows": rows},
                headers={"Content-Type": "local"},
                fetchedAt=datetime.now(timezone.utc),
            )
        return self.dataGovAdapter.fetchDataset(resourceId)

    def parseResponse(self, data: RawResponse) -> list[dict[str, Any]]:
        """Parse HDB rows from a raw response body."""
        body = data.body
        if isinstance(body, dict):
            rows = body.get("rows", body.get("items", []))
        elif isinstance(body, list):
            rows = body
        else:
            rows = []
        return [dict(row) for row in rows if isinstance(row, dict)]

    def retrieveHousePricing(
        self,
        subzoneCode: str,
        flatTypes: list[str] | None = None,
    ) -> RetrievalResult[dict[str, HousePricing]]:
        """Return pricing keyed by flat type using the HDB town median proxy."""
        warnings = []
        if self.subzoneRegistry is None:
            warnings.append(
                self.handleMissingData("HDB_RESALE", subzoneCode, DataAvailabilityCode.MISSING_SOURCE_DATA)
            )
            return RetrievalResult({}, warnings)
        try:
            subzone = self.subzoneRegistry.getSubzone(subzoneCode)
        except KeyError:
            warnings.append(
                self.handleMissingData("HDB_RESALE", subzoneCode, DataAvailabilityCode.MISSING_SOURCE_DATA)
            )
            return RetrievalResult({}, warnings)

        rows = self._rows()
        if not rows:
            warnings.append(
                self.handleMissingData("HDB_RESALE", subzoneCode, DataAvailabilityCode.MISSING_SOURCE_DATA)
            )
            return RetrievalResult({}, warnings)

        as_of = self._resolveAsOf(rows)
        window_start = _addMonths(as_of, -11)
        available_types = sorted(
            {
                flat_type
                for (town, flat_type), _ in self._byTown.items()
                if town == subzone.townName.upper()
            }
        )
        requested = [str(t).strip().upper() for t in (flatTypes or available_types) if str(t).strip()]
        pricing: dict[str, HousePricing] = {}

        for flat_type in requested:
            # The product decision is to keep the HDB-town median proxy. The
            # published dataset has no subzone key, and subzone-level pricing is
            # not part of the current scope.
            town_rows = [
                row
                for row in self._byTown.get((subzone.townName.upper(), flat_type), [])
                if window_start <= _parseMonth(row.get("month")) <= as_of
            ]
            if town_rows:
                pricing[flat_type] = self._aggregate(town_rows, flat_type, as_of, True)
                continue

            warnings.append(
                self.handleMissingData(
                    "HDB_RESALE",
                    subzoneCode,
                    DataAvailabilityCode.MISSING_SOURCE_DATA,
                    message=f"No {flat_type} transactions in the 12-month window",
                )
            )

        return RetrievalResult(pricing, warnings)

    def _rows(self) -> list[dict[str, Any]]:
        cached = self._rowsCache.get("hdb")
        if cached is not None:
            return cached
        try:
            raw = self.fetchData("hdb_resale")
            rows = self.parseResponse(raw)
        except Exception:
            rows = []
        self._rowsCache["hdb"] = rows
        self._buildIndex(rows)
        return rows

    def _buildIndex(self, rows: list[dict[str, Any]]) -> None:
        """Index rows by (town, flat type) and (subzone, flat type)."""
        self._byTown = {}
        for row in rows:
            flat_type = _rowFlatType(row)
            if not flat_type:
                continue
            town = _rowTown(row)
            if town:
                self._byTown.setdefault((town, flat_type), []).append(row)

    def _resolveAsOf(self, rows: list[dict[str, Any]]) -> date:
        if self._resolvedAsOf is not None:
            return self._resolvedAsOf
        if self._requestedAsOf is not None:
            if isinstance(self._requestedAsOf, datetime):
                self._resolvedAsOf = self._requestedAsOf.date()
            elif isinstance(self._requestedAsOf, date):
                self._resolvedAsOf = self._requestedAsOf
            else:
                self._resolvedAsOf = _parseMonth(self._requestedAsOf)
            return self._resolvedAsOf
        months = [_parseMonth(row.get("month")) for row in rows]
        self._resolvedAsOf = max(months) if months else date.today()
        return self._resolvedAsOf

    def _aggregate(
        self,
        rows: list[dict[str, Any]],
        flat_type: str,
        as_of: date,
        town_proxy: bool,
    ) -> HousePricing:
        prices = [float(row["resale_price"]) for row in rows if row.get("resale_price") not in (None, "")]
        psqm = [
            float(row["resale_price"]) / float(row["floor_area_sqm"])
            for row in rows
            if row.get("resale_price") not in (None, "")
            and row.get("floor_area_sqm") not in (None, "", "0")
        ]
        trend_percent = self._trendPercent(rows, as_of)
        trend_label = "Rising" if trend_percent > 2 else "Falling" if trend_percent < -2 else "Stable"
        return HousePricing(
            averagePrice=round(statistics.fmean(prices), 2) if prices else 0.0,
            medianPricePerSqm=round(statistics.median(psqm), 2) if psqm else 0.0,
            priceTrend=trend_label,
            priceTrendPercent=round(trend_percent, 2),
            flatType=flat_type,
            transactionCount=len(prices),
            isTownProxy=town_proxy,
            dataWindowMonths=12,
            asOf=datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc),
            medianPrice=round(statistics.median(prices), 2) if prices else 0.0,
        )

    @staticmethod
    def _trendPercent(rows: list[dict[str, Any]], as_of: date) -> float:
        latest_start = _addMonths(as_of, -5)
        previous_start = _addMonths(as_of, -11)
        latest = [
            float(row["resale_price"])
            for row in rows
            if row.get("resale_price") not in (None, "")
            and latest_start <= _parseMonth(row.get("month")) <= as_of
        ]
        previous = [
            float(row["resale_price"])
            for row in rows
            if row.get("resale_price") not in (None, "")
            and previous_start <= _parseMonth(row.get("month")) < latest_start
        ]
        if not latest or not previous:
            return 0.0
        base = statistics.median(previous)
        return ((statistics.median(latest) - base) / base * 100) if base else 0.0

    @staticmethod
    def _readLocalRows(path: Path) -> list[dict[str, Any]]:
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload = payload.get("rows", payload.get("items", []))
            return [dict(row) for row in payload if isinstance(row, dict)]
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]


def _parseMonth(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date().replace(day=1)
    if isinstance(value, date):
        return value.replace(day=1)
    text = str(value or "").strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        try:
            return date(int(text[:4]), int(text[5:7]), int(text[8:10]))
        except ValueError:
            pass
    if len(text) >= 7 and text[4] == "-":
        try:
            return date(int(text[:4]), int(text[5:7]), 1)
        except ValueError:
            pass
    try:
        return datetime.strptime(text, "%d/%m/%Y").date().replace(day=1)
    except ValueError:
        return date.min


def _addMonths(value: date, months: int) -> date:
    month_index = value.year * 12 + (value.month - 1) + months
    year, month = divmod(month_index, 12)
    return date(year, month + 1, 1)


def _rowTown(row: dict[str, Any]) -> str:
    return str(row.get("town") or row.get("townName") or "").strip().upper()


def _rowFlatType(row: dict[str, Any]) -> str:
    return str(row.get("flat_type") or row.get("flatType") or "").strip().upper()
