"""Environmental baseline and live-condition retrieval."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

from app.control.retrieval_control import RetrievalControl
from app.entity.enums import DataAvailabilityCode, EnvironmentGranularity
from app.entity.environment_info import EnvironmentInfo
from app.entity.subzone_indicators import SubzoneIndicators
from app.entity.types import RawResponse, RetrievalResult

if TYPE_CHECKING:
    from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.data_availability_notifier import DataAvailabilityNotifier


class EnvironmentRetrievalControl(RetrievalControl):
    """Stereotype: Control. Retrieves static environment baselines and live readings."""

    def __init__(
        self,
        dataGovAdapter: DataGovSgAdapter,
        notifier: DataAvailabilityNotifier,
        baselinePath: Path | str | None = None,
        liveProvider: Callable[[str], dict[str, Any]] | None = None,
        subzoneRegistry: SubzoneRegistry | None = None,
    ) -> None:
        """Create the environment control.

        Args:
            dataGovAdapter: Data.gov.sg adapter.
            notifier: Stateless warning factory.
            baselinePath: Optional local JSON baseline file.
            liveProvider: Optional callback returning live PM2.5/UVI/forecast data.
            subzoneRegistry: Optional registry used to resolve regional baselines.
        """
        super().__init__(dataGovAdapter, notifier)
        self.baselinePath = Path(baselinePath) if baselinePath else None
        self.liveProvider = liveProvider
        self.subzoneRegistry = subzoneRegistry
        self._baselineCache: dict[str, Any] | None = None

    def fetchData(self, resourceId: str) -> RawResponse:
        """Fetch the environment baseline payload."""
        if self.baselinePath and self.baselinePath.exists():
            payload = json.loads(self.baselinePath.read_text(encoding="utf-8"))
            return RawResponse(
                statusCode=200,
                body=payload,
                headers={"Content-Type": "application/json"},
                fetchedAt=datetime.now(timezone.utc),
            )
        return self.dataGovAdapter.fetchDataset(resourceId)

    def parseResponse(self, data: RawResponse) -> dict[str, Any]:
        """Parse the baseline payload."""
        return data.body if isinstance(data.body, dict) else {}

    def _baseline(self) -> dict[str, Any]:
        if self._baselineCache is None:
            try:
                raw = self.fetchData("environment_baselines")
                self._baselineCache = self.parseResponse(raw)
            except Exception:
                self._baselineCache = {}
        return self._baselineCache

    def _baselineFor(self, subzoneCode: str) -> dict[str, Any]:
        """Return a subzone, regional or DEFAULT baseline."""
        baselines = self._baseline()
        if subzoneCode in baselines:
            return baselines[subzoneCode]
        region = ""
        if self.subzoneRegistry is not None:
            try:
                region = self.subzoneRegistry.getSubzone(subzoneCode).regionName
            except KeyError:
                region = ""
        region = region.upper().replace(" REGION", "").strip()
        if region and region in baselines:
            return baselines[region]
        return baselines.get("DEFAULT", {})

    def retrieveEnvironmentInfo(
        self,
        subzoneCode: str,
        includeLive: bool = True,
    ) -> RetrievalResult[EnvironmentInfo]:
        """Return static baseline values and optional live display values."""
        warnings = []
        baseline = self._baselineFor(subzoneCode)
        green = baseline.get("greenCoveragePercent", baseline.get("green_coverage_percent"))
        if green is None:
            warnings.append(
                self.handleMissingData(
                    "ENVIRONMENT_BASELINE",
                    subzoneCode,
                    DataAvailabilityCode.MISSING_SOURCE_DATA,
                    message="Green coverage baseline unavailable",
                )
            )
            green_value = 0.0
        else:
            green_value = float(green)

        live: dict[str, Any] = {}
        if includeLive and self.liveProvider is not None:
            try:
                live = self.liveProvider(subzoneCode) or {}
            except Exception:
                warnings.append(
                    self.handleMissingData(
                        "LIVE_ENVIRONMENT",
                        subzoneCode,
                        DataAvailabilityCode.PARTIAL_DATA,
                        isRetryable=True,
                        message="Live PM2.5/UVI/forecast unavailable; display-only fields omitted",
                    )
                )

        as_of = baseline.get("asOf") or baseline.get("as_of")
        parsed_as_of = _parseTimestamp(as_of)
        info = EnvironmentInfo(
            weatherPattern=str(
                baseline.get("weatherPattern", baseline.get("weather_pattern", "Regional baseline"))
            ),
            greenCoveragePercent=green_value,
            pm25=_optionalFloat(live.get("pm25", baseline.get("pm25Live"))),
            uvi=_optionalFloat(live.get("uvi", baseline.get("uvi"))),
            forecastCode=live.get("forecastCode") or baseline.get("forecastCode"),
            granularity=EnvironmentGranularity(baseline.get("granularity", "REGION")),
            asOf=parsed_as_of,
        )
        return RetrievalResult(info, warnings)

    def retrieveIndicators(
        self,
        subzoneCode: str,
        includeLive: bool = True,
    ) -> RetrievalResult[SubzoneIndicators]:
        """Return the static indicators used by ranking (green coverage, PM2.5 baseline)."""
        env_result = self.retrieveEnvironmentInfo(subzoneCode, includeLive=includeLive)
        baseline = self._baselineFor(subzoneCode)
        indicators = SubzoneIndicators(
            greenCoveragePercent500m=env_result.data.greenCoveragePercent,
            pm25Baseline=_optionalFloat(baseline.get("pm25Baseline", baseline.get("pm25_baseline"))),
            pm25Live=env_result.data.pm25,
            uvi=env_result.data.uvi,
            forecastCode=env_result.data.forecastCode,
            dataAsOf=env_result.data.asOf,
        )
        return RetrievalResult(indicators, env_result.warnings)


def _optionalFloat(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parseTimestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
