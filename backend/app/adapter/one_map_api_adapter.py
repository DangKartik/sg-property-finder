"""OneMap API adapter with automatic token refresh."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.adapter.one_map_token_manager import OneMapTokenManager
from app.core.time import nextWeekdayPeak
from app.entity.address_match import AddressMatch
from app.entity.enums import TransitMode
from app.entity.types import Coordinates

if TYPE_CHECKING:
    from app.entity.types import JSON


class OneMapApiError(RuntimeError):
    """Raised when a OneMap API request fails."""

    def __init__(self, message: str, statusCode: int | None = None) -> None:
        super().__init__(message)
        self.statusCode = statusCode


class OneMapApiAdapter:
    """Stereotype: Adapter. Wraps OneMap auth, routing, search and themes."""

    baseUrl: str
    email: str
    password: str
    accessToken: str | None
    tokenExpiry: datetime | None
    tokenManager: OneMapTokenManager

    def __init__(
        self,
        baseUrl: str,
        email: str = "",
        password: str = "",
        tokenManager: OneMapTokenManager | None = None,
        timeoutSeconds: int = 25,
    ) -> None:
        """Create the adapter and its token manager."""
        self.baseUrl = baseUrl.rstrip("/")
        self.email = email
        self.password = password
        self.accessToken = None
        self.tokenExpiry = None
        self.timeoutSeconds = timeoutSeconds
        self.tokenManager = tokenManager or OneMapTokenManager(self.baseUrl, email, password)
        self._asyncClient: Any | None = None

    def getAccessToken(self) -> str:
        """Return a valid token, refreshing automatically when needed."""
        token = self.tokenManager.getAccessToken()
        self.accessToken = token
        self.tokenExpiry = self.tokenManager.tokenExpiry
        return token

    def refreshToken(self) -> None:
        """Force a token refresh."""
        self.accessToken = self.tokenManager.refreshToken()
        self.tokenExpiry = self.tokenManager.tokenExpiry

    def invalidateToken(self) -> None:
        """Discard the cached token so the next call refreshes it."""
        self.tokenManager.invalidate()
        self.accessToken = None
        self.tokenExpiry = None

    def _getJson(self, url: str, params: dict[str, Any] | None, token: str) -> dict[str, Any]:
        """Perform an authorized GET and parse JSON."""
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(url, headers={"Authorization": token, "Accept": "application/json"}, method="GET")
        try:
            with urlopen(request, timeout=self.timeoutSeconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise OneMapApiError(f"OneMap request failed with HTTP {exc.code}", exc.code) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise OneMapApiError("OneMap request failed (network or response error)") from exc
        if not isinstance(payload, dict):
            raise OneMapApiError("OneMap returned a non-object payload")
        return payload

    def _authorizedJson(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call a OneMap endpoint, retrying once after a 401."""
        url = f"{self.baseUrl}{path}"
        token = self.getAccessToken()
        try:
            return self._getJson(url, params, token)
        except OneMapApiError as exc:
            if exc.statusCode != 401:
                raise
            self.invalidateToken()
            token = self.getAccessToken()
            return self._getJson(url, params, token)

    def searchPlaces(self, query: str, pageNum: int = 1) -> dict[str, Any]:
        """Return the raw OneMap search payload for one result page.

        Args:
            query: Postal code, address or place name.
            pageNum: One-based result page.

        Returns:
            dict[str, Any]: The raw OneMap search response.
        """
        return self._authorizedJson(
            "/api/common/elastic/search",
            {
                "searchVal": query,
                "returnGeom": "Y",
                "getAddrDetails": "Y",
                "pageNum": pageNum,
            },
        )

    def searchAddress(self, query: str) -> list[AddressMatch]:
        """Return detailed address matches for user confirmation."""
        payload = self.searchPlaces(query)
        matches: list[AddressMatch] = []
        for result in payload.get("results", []) or []:
            try:
                latitude = float(result["LATITUDE"])
                longitude = float(result["LONGITUDE"])
            except (KeyError, TypeError, ValueError):
                continue
            formatted = str(result.get("SEARCHVAL") or result.get("ADDRESS") or "")
            matches.append(
                AddressMatch(
                    formattedAddress=formatted,
                    postalCode=str(result.get("POSTAL") or ""),
                    coordinates=Coordinates(latitude, longitude),
                    confidenceScore=round(
                        SequenceMatcher(None, query.lower(), formatted.lower()).ratio(),
                        4,
                    ),
                )
            )
        return matches

    @staticmethod
    def _routingParams(
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
    ) -> dict[str, Any]:
        """Build OneMap routing query parameters."""
        route_type = {
            TransitMode.PUBLIC_TRANSIT: "pt",
            TransitMode.DRIVING: "drive",
            TransitMode.WALKING: "walk",
        }[mode]
        params: dict[str, Any] = {
            "start": origin.toOneMapString(),
            "end": destination.toOneMapString(),
            "routeType": route_type,
        }
        if mode is TransitMode.PUBLIC_TRANSIT:
            departure = departureTime or nextWeekdayPeak()
            if departure.tzinfo is None:
                from app.core.time import SGT

                departure = departure.replace(tzinfo=SGT)
            params.update(
                {
                    "date": departure.strftime("%m-%d-%Y"),
                    "time": departure.strftime("%H:%M:%S"),
                    "mode": "TRANSIT",
                    "maxWalkDistance": 1000,
                    "numItineraries": 3,
                }
            )
        return params

    def getRoutingData(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
    ) -> JSON:
        """Return raw OneMap routing JSON."""
        return self._authorizedJson(
            "/api/public/routingsvc/route",
            self._routingParams(origin, destination, mode, departureTime),
        )

    async def getRoutingDataAsync(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
    ) -> JSON:
        """Return raw routing JSON using httpx when installed.

        Falls back to a threadpool call when httpx is unavailable.
        """
        try:
            import httpx
        except ImportError:
            return await asyncio.to_thread(
                self.getRoutingData, origin, destination, mode, departureTime
            )

        url = f"{self.baseUrl}/api/public/routingsvc/route"
        params = self._routingParams(origin, destination, mode, departureTime)
        token = await asyncio.to_thread(self.getAccessToken)
        try:
            if self._asyncClient is None:
                self._asyncClient = httpx.AsyncClient(timeout=self.timeoutSeconds)
            client = self._asyncClient
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": token, "Accept": "application/json"},
            )
            if response.status_code == 401:
                self.invalidateToken()
                token = await asyncio.to_thread(self.getAccessToken)
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": token, "Accept": "application/json"},
                )
            if response.status_code >= 400:
                raise OneMapApiError(
                    f"OneMap request failed with HTTP {response.status_code}",
                    response.status_code,
                )
            payload = response.json()
        except OneMapApiError:
            raise
        except Exception as exc:
            raise OneMapApiError("OneMap async request failed") from exc
        if not isinstance(payload, dict):
            raise OneMapApiError("OneMap returned a non-object payload")
        return payload

    async def aclose(self) -> None:
        """Close the shared async HTTP client, if one was created."""
        if self._asyncClient is not None:
            await self._asyncClient.aclose()
            self._asyncClient = None

    def getThemeData(
        self,
        queryName: str,
        extents: list[Coordinates] | None = None,
    ) -> JSON:
        """Return raw OneMap theme data."""
        params: dict[str, Any] = {"queryName": queryName}
        if extents:
            lats = [c.latitude for c in extents]
            lons = [c.longitude for c in extents]
            params["extents"] = f"{min(lats)},{min(lons)},{max(lats)},{max(lons)}"
        return self._authorizedJson("/api/public/themesvc/retrieveTheme", params)

    def getNearbyTransport(self, origin: Coordinates, radiusM: int) -> JSON:
        """Return nearby transport options.

        OneMap's nearby-transport service is not required by the Phase 2
        endpoints; this method is intentionally deferred until the exact
        service contract is confirmed.
        """
        raise NotImplementedError("Nearby transport is not part of the Phase 2 endpoint set")
