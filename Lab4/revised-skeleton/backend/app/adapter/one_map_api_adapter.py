"""OneMap API adapter with automatic token refresh."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.adapter.one_map_token_manager import OneMapTokenManager

if TYPE_CHECKING:
    from app.entity.address_match import AddressMatch
    from app.entity.enums import TransitMode
    from app.entity.types import Coordinates, JSON


class OneMapApiAdapter:
    """Stereotype: Adapter. Wraps OneMap authentication, routing, address search and themes.

    The adapter owns a `OneMapTokenManager`; call `getAccessToken()` before an
    authorized request. The manager caches the token and refreshes it
    automatically before expiry. If OneMap returns 401, call
    `invalidateToken()` and retry once.
    """

    baseUrl: str
    email: str
    password: str
    accessToken: str | None
    tokenExpiry: datetime | None
    tokenManager: OneMapTokenManager

    def __init__(self, baseUrl: str, email: str, password: str) -> None:
        """Create the adapter and its token manager.

        Args:
            baseUrl: OneMap base URL.
            email: Registered OneMap account email.
            password: Registered OneMap account password.

        Returns:
            None.

        Failure handling:
            Raise `OneMapAuthenticationError` when credentials are missing.
        """
        self.baseUrl = baseUrl.rstrip("/")
        self.email = email
        self.password = password
        self.accessToken = None
        self.tokenExpiry = None
        self.tokenManager = OneMapTokenManager(self.baseUrl, email, password)

    def getAccessToken(self) -> str:
        """Return a valid token, refreshing automatically when needed.

        Returns:
            str: Valid OneMap access token.

        Failure handling:
            Raise `OneMapAuthenticationError` when refresh fails.
        """
        token = self.tokenManager.getAccessToken()
        self.accessToken = token
        self.tokenExpiry = self.tokenManager.tokenExpiry
        return token

    def refreshToken(self) -> None:
        """Force a token refresh.

        Returns:
            None.

        Failure handling:
            Raise `OneMapAuthenticationError` when authentication fails.
        """
        self.accessToken = self.tokenManager.refreshToken()
        self.tokenExpiry = self.tokenManager.tokenExpiry

    def invalidateToken(self) -> None:
        """Discard the cached token so the next call refreshes it.

        Returns:
            None.

        Failure handling:
            Safe to call at any time.
        """
        self.tokenManager.invalidate()
        self.accessToken = None
        self.tokenExpiry = None

    def getRoutingData(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
    ) -> JSON:
        """Return raw OneMap routing JSON.

        Args:
            origin: Start coordinate.
            destination: End coordinate.
            mode: Travel mode.
            departureTime: Optional departure time; required for PT.

        Returns:
            JSON: Raw OneMap routing response.

        Failure handling:
            Implement in Phase 2; call `getAccessToken()` first, invalidate and
            retry once on HTTP 401, and raise a typed error on quota/network
            failure.
        """
        ...

    def searchAddress(self, query: str) -> list[AddressMatch]:
        """Return detailed address matches for user confirmation.

        Args:
            query: Address, building name or postal code.

        Returns:
            list[AddressMatch]: Confirmed address candidates.

        Failure handling:
            Implement in Phase 2; call `getAccessToken()` first, invalidate and
            retry once on HTTP 401, and raise a typed error on failure.
        """
        ...

    def getThemeData(
        self,
        queryName: str,
        extents: list[Coordinates] | None = None,
    ) -> JSON:
        """Return raw OneMap theme data.

        Args:
            queryName: OneMap theme query name.
            extents: Optional bounding coordinates.

        Returns:
            JSON: Raw theme response.

        Failure handling:
            Implement in Phase 2; use the shared authorized request helper.
        """
        ...

    def getNearbyTransport(self, origin: Coordinates, radiusM: int) -> JSON:
        """Return nearby transport options for a coordinate.

        Args:
            origin: Search centre.
            radiusM: Search radius in metres.

        Returns:
            JSON: Raw nearby-transport response.

        Failure handling:
            Implement in Phase 2; use the shared authorized request helper.
        """
        ...
