"""Commute routing with a precomputed CBD matrix and async custom routing."""

from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.core.cache import TTLCache
from app.core.geometry import haversineKm
from app.core.polyline import mergeEncodedPolylines
from app.core.time import CBD_LATITUDE, CBD_LONGITUDE, nextWeekdayPeak
from app.entity.commute_estimate import CommuteEstimate
from app.entity.enums import DataAvailabilityCode, TransitMode
from app.entity.types import Coordinates, RetrievalResult

if TYPE_CHECKING:
    from app.adapter.one_map_api_adapter import OneMapApiAdapter
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.entity.subzone import Subzone


class CommuteError(RuntimeError):
    """Raised when a commute estimate cannot be produced."""


# Fallback speeds used only when live routing is unavailable or a matrix entry
# is missing. They are deliberately conservative urban averages.
_FALLBACK_SPEED_KMH = {
    TransitMode.PUBLIC_TRANSIT: 20.0,
    TransitMode.DRIVING: 30.0,
    TransitMode.WALKING: 4.8,
}
_FALLBACK_OVERHEAD_MINUTES = {
    TransitMode.PUBLIC_TRANSIT: 10.0,
    TransitMode.DRIVING: 5.0,
    TransitMode.WALKING: 0.0,
}
_HEURISTIC_DISTANCE_MULTIPLIERS = {
    TransitMode.PUBLIC_TRANSIT: 1.0,
    TransitMode.DRIVING: 1.35,
    TransitMode.WALKING: 1.20,
}
_MAX_LIVE_CONCURRENCY = 12


class CommuteControl:
    """Stereotype: Control. Retrieves matrix and live OneMap commute estimates."""

    def __init__(
        self,
        oneMapAdapter: OneMapApiAdapter,
        notifier: DataAvailabilityNotifier | None = None,
        matrixPath: Path | str | None = None,
        cache: TTLCache[str, CommuteEstimate] | None = None,
    ) -> None:
        """Create the commute control.

        Args:
            oneMapAdapter: OneMap routing adapter.
            notifier: Optional warning factory.
            matrixPath: Optional precomputed CBD matrix JSON.
            cache: Optional shared commute cache.
        """
        self.oneMapAdapter = oneMapAdapter
        self.notifier = notifier
        self.matrixPath = Path(matrixPath) if matrixPath else None
        self.cache = cache or TTLCache(maxsize=2048, ttl=7 * 24 * 3600)
        self.matrix: dict[str, Any] = {}
        self.insufficientDataSubzoneCodes: set[str] = set()
        if self.matrixPath and self.matrixPath.exists():
            payload = json.loads(self.matrixPath.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                self.matrix = payload.get("subzones") or payload.get("matrix") or payload
                metadata = payload.get("metadata") or {}
                for error in metadata.get("errors") or []:
                    code = str(error.get("subzoneCode") or "").strip()
                    if code:
                        self.insufficientDataSubzoneCodes.add(code)
            else:
                self.matrix = {}

    def isNearCbd(self, origin: Coordinates) -> bool:
        """Return whether the origin is within 1 km of Raffles Place."""
        return haversineKm(origin.latitude, origin.longitude, CBD_LATITUDE, CBD_LONGITUDE) <= 1.0

    def retrieveCommute(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
        destinationSubzoneCode: str | None = None,
        warnings: list[Any] | None = None,
    ) -> CommuteEstimate:
        """Return a commute estimate for one destination.

        The precomputed matrix is used only for public transport when the origin
        is near the CBD. Driving and walking always use live OneMap routing, with
        a straight-line fallback when routing fails. A missing public-transport
        matrix entry also uses the fallback.
        """
        departure = departureTime or nextWeekdayPeak()
        key = _cacheKey(origin, destination, mode, departure, destinationSubzoneCode)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        if (
            destinationSubzoneCode
            and self.isNearCbd(origin)
            and mode is TransitMode.PUBLIC_TRANSIT
        ):
            matrix_estimate = self._matrixEstimate(destinationSubzoneCode, mode)
            if matrix_estimate is not None:
                self.cache[key] = matrix_estimate
                return matrix_estimate
            estimate = self._straightLineEstimate(origin, destination, mode, departure)
            if warnings is not None:
                warnings.append(
                    self._fallbackWarning(
                        destinationSubzoneCode,
                        mode,
                        "Commute matrix entry missing",
                    )
                )
            return estimate

        try:
            estimate = self._liveEstimate(origin, destination, mode, departure)
        except CommuteError:
            estimate = self._straightLineEstimate(origin, destination, mode, departure)
            if warnings is not None:
                warnings.append(
                    self._fallbackWarning(
                        destinationSubzoneCode,
                        mode,
                        "OneMap routing failed",
                    )
                )
            return estimate

        self.cache[key] = estimate
        return estimate

    async def retrieveCommutes(
        self,
        origin: Coordinates,
        subzones: list[Subzone],
        mode: TransitMode,
        departureTime: datetime | None = None,
        topK: int = 50,
    ) -> RetrievalResult[dict[str, CommuteEstimate]]:
        """Return commute estimates for a candidate set.

        Public transport near the CBD uses the precomputed matrix (with a
        straight-line fallback for missing entries). Otherwise the nearest
        `topK` subzones are routed live, while the remainder receive a spatial
        heuristic estimate with the mode's road/path multiplier. This keeps the
        commute criterion available for every candidate instead of letting
        out-of-shortlist subzones skip it and renormalise their other weights.
        """
        departure = departureTime or nextWeekdayPeak()
        warnings: list[Any] = []
        near_cbd = self.isNearCbd(origin)

        if near_cbd and mode is TransitMode.PUBLIC_TRANSIT:
            estimates: dict[str, CommuteEstimate] = {}
            for subzone in subzones:
                estimate = self._matrixEstimate(subzone.subzoneCode, mode)
                if estimate is None:
                    estimate = self._straightLineEstimate(
                        origin,
                        subzone.centroid,
                        mode,
                        departure,
                    )
                    warnings.append(
                        self._fallbackWarning(
                            subzone.subzoneCode,
                            mode,
                            "Commute matrix entry missing",
                        )
                    )
                estimates[subzone.subzoneCode] = estimate
            return RetrievalResult(estimates, warnings)

        ranked = sorted(
            subzones,
            key=lambda subzone: haversineKm(
                origin.latitude,
                origin.longitude,
                subzone.centroid.latitude,
                subzone.centroid.longitude,
            ),
        )
        live_subzones = ranked[:topK]
        heuristic_subzones = ranked[topK:]

        semaphore = asyncio.Semaphore(_MAX_LIVE_CONCURRENCY)

        async def one(
            subzone: Subzone,
        ) -> tuple[str, CommuteEstimate, Any | None]:
            async with semaphore:
                try:
                    estimate = await self._cachedLiveEstimateAsync(
                        origin,
                        subzone.centroid,
                        mode,
                        departure,
                        subzone.subzoneCode,
                    )
                    return subzone.subzoneCode, estimate, None
                except Exception:
                    estimate = self._straightLineEstimate(
                        origin,
                        subzone.centroid,
                        mode,
                        departure,
                    )
                    return (
                        subzone.subzoneCode,
                        estimate,
                        self._fallbackWarning(
                            subzone.subzoneCode,
                            mode,
                            "OneMap routing failed",
                        ),
                    )

        results = await asyncio.gather(*(one(subzone) for subzone in live_subzones))
        estimates: dict[str, CommuteEstimate] = {}
        for code, estimate, warning in results:
            estimates[code] = estimate
            if warning is not None:
                warnings.append(warning)

        for subzone in heuristic_subzones:
            estimates[subzone.subzoneCode] = self._straightLineEstimate(
                origin,
                subzone.centroid,
                mode,
                departure,
            )
            warnings.append(
                self._fallbackWarning(
                    subzone.subzoneCode,
                    mode,
                    "Outside live-routing shortlist",
                )
            )
        return RetrievalResult(estimates, warnings)

    def retrieveCommutesSync(
        self,
        origin: Coordinates,
        subzones: list[Subzone],
        mode: TransitMode,
        departureTime: datetime | None = None,
        topK: int = 50,
    ) -> RetrievalResult[dict[str, CommuteEstimate]]:
        """Synchronous wrapper around `retrieveCommutes` for non-async callers."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.retrieveCommutes(origin, subzones, mode, departureTime, topK))
        raise CommuteError("retrieveCommutesSync cannot run inside an active event loop")

    def _matrixEstimate(self, subzoneCode: str, mode: TransitMode) -> CommuteEstimate | None:
        if mode is not TransitMode.PUBLIC_TRANSIT:
            return None
        entry = self.matrix.get(subzoneCode)
        if entry is None:
            return None
        if any(key in entry for key in ("CBD", "RAFFLES_PLACE", "DEFAULT")):
            entry = entry.get("CBD") or entry.get("RAFFLES_PLACE") or entry.get("DEFAULT") or {}
        duration = entry.get("durationMinutes", entry.get("duration_minutes"))
        distance = entry.get("distanceKm", entry.get("distance_km"))
        if duration is None or distance is None:
            return None
        return CommuteEstimate(
            durationMinutes=int(duration),
            distanceKm=float(distance),
            transferCount=int(entry.get("transferCount", entry.get("transfers", 0))),
            travelMode=mode,
            departureTime=nextWeekdayPeak(),
            routeGeometry=None,
        )

    def _liveEstimate(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departure: datetime,
    ) -> CommuteEstimate:
        """Call OneMap synchronously and parse the route."""
        try:
            payload = self.oneMapAdapter.getRoutingData(origin, destination, mode, departure)
        except Exception as exc:
            raise CommuteError("OneMap routing failed") from exc
        return self._parseRoute(payload, mode, departure)

    async def _liveEstimateAsync(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departure: datetime,
    ) -> CommuteEstimate:
        """Call OneMap asynchronously (httpx when available) and parse the route."""
        try:
            async_method = getattr(self.oneMapAdapter, "getRoutingDataAsync", None)
            if async_method is not None:
                payload = await async_method(origin, destination, mode, departure)
            else:
                payload = await asyncio.to_thread(
                    self.oneMapAdapter.getRoutingData,
                    origin,
                    destination,
                    mode,
                    departure,
                )
        except Exception as exc:
            raise CommuteError("OneMap routing failed") from exc
        return self._parseRoute(payload, mode, departure)

    async def _cachedLiveEstimateAsync(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departure: datetime,
        subzoneCode: str | None,
    ) -> CommuteEstimate:
        """Return a cached live estimate or fetch and cache a new one."""
        key = _cacheKey(origin, destination, mode, departure, subzoneCode)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        estimate = await self._liveEstimateAsync(origin, destination, mode, departure)
        self.cache[key] = estimate
        return estimate

    @staticmethod
    def _straightLineEstimate(
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departure: datetime,
    ) -> CommuteEstimate:
        """Estimate a commute from straight-line distance, mode multiplier and speed."""
        distance_km = haversineKm(
            origin.latitude,
            origin.longitude,
            destination.latitude,
            destination.longitude,
        ) * _HEURISTIC_DISTANCE_MULTIPLIERS[mode]
        speed_kmh = _FALLBACK_SPEED_KMH[mode]
        overhead = _FALLBACK_OVERHEAD_MINUTES[mode]
        duration = max(1, math.ceil((distance_km / speed_kmh) * 60.0 + overhead))
        return CommuteEstimate(
            durationMinutes=duration,
            distanceKm=round(distance_km, 3),
            transferCount=0,
            travelMode=mode,
            departureTime=departure,
            routeGeometry=None,
        )

    def _fallbackWarning(
        self,
        subzoneCode: str | None,
        mode: TransitMode,
        reason: str,
    ):
        """Build the warning attached to an estimated commute."""
        return self._warning(
            subzoneCode,
            f"{reason}; using straight-line {mode.value.lower()} estimate",
            code=DataAvailabilityCode.ESTIMATED_COMMUTE_FALLBACK,
            source="Spatial estimate",
        )

    @staticmethod
    def _parseRoute(payload: dict[str, Any], mode: TransitMode, departure: datetime) -> CommuteEstimate:
        summary = payload.get("route_summary") or {}
        if not summary:
            plans = payload.get("plan", {}).get("itineraries", [])
            if plans:
                best = plans[0]
                duration_seconds = best.get("duration", 0)
                legs = best.get("legs", [])
                distance_m = sum(leg.get("distance", 0) for leg in legs)
                transfers = max(0, len(legs) - 1)
                return CommuteEstimate(
                    durationMinutes=max(1, math.ceil(float(duration_seconds) / 60)),
                    distanceKm=round(float(distance_m) / 1000, 3),
                    transferCount=transfers,
                    travelMode=mode,
                    departureTime=departure,
                    routeGeometry=mergeEncodedPolylines(
                        leg.get("legGeometry", {}).get("points") for leg in legs
                    ),
                )
            raise CommuteError("OneMap routing response had no summary")

        duration_seconds = float(summary.get("total_time", 0))
        distance_m = float(summary.get("total_distance", 0))
        instructions = payload.get("route_instructions") or []
        transfers = max(0, len([item for item in instructions if isinstance(item, list) and item and str(item[0]).upper() in {"SUBWAY", "BUS", "RAIL"}]) - 1)
        return CommuteEstimate(
            durationMinutes=max(1, math.ceil(duration_seconds / 60)),
            distanceKm=round(distance_m / 1000, 3),
            transferCount=transfers,
            travelMode=mode,
            departureTime=departure,
            routeGeometry=payload.get("route_geometry"),
        )

    def _warning(
        self,
        subzoneCode: str | None,
        message: str,
        code: DataAvailabilityCode = DataAvailabilityCode.PARTIAL_DATA,
        source: str = "OneMap",
    ):
        if self.notifier is None:
            from app.control.data_availability_notifier import DataAvailabilityNotifier

            self.notifier = DataAvailabilityNotifier()
        return self.notifier.notifyDataUnavailable(
            "COMMUTE",
            subzoneCode,
            code,
            source=source,
            isRetryable=True,
            message=message,
        )


def _cacheKey(
    origin: Coordinates,
    destination: Coordinates,
    mode: TransitMode,
    departure: datetime,
    subzoneCode: str | None,
) -> str:
    return "|".join(
        [
            f"{origin.latitude:.4f},{origin.longitude:.4f}",
            f"{destination.latitude:.4f},{destination.longitude:.4f}",
            mode.value,
            departure.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M"),
            subzoneCode or "",
        ]
    )
