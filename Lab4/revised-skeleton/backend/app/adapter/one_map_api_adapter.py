"""One map api adapter module."""

from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.address_match import AddressMatch
    from app.entity.enums import TransitMode
    from app.entity.types import Coordinates, JSON

class OneMapApiAdapter:
    """Stereotype: Adapter. Adapter that wraps OneMap authentication, routing, address search and themes."""
    baseUrl: str
    email: str
    password: str
    accessToken: str | None
    tokenExpiry: datetime | None

    def __init__(self, baseUrl: str, email: str, password: str) -> None:
        """Initialise the OneMapApiAdapter with its dependencies.

        Args:
            baseUrl: str
            email: str
            password: str

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def refreshToken(self) -> None:
        """Refresh the OneMap access token; raise on authentication failure.

        Args:
            None.

        Returns:
            None.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    def getRoutingData(self, origin: Coordinates, destination: Coordinates, mode: TransitMode, departureTime: datetime | None=None) -> JSON:
        """Return raw OneMap routing JSON; raise on authentication, quota or network errors.

        Args:
            origin: Coordinates
            destination: Coordinates
            mode: TransitMode
            departureTime: datetime | None

        Returns:
            JSON.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    def searchAddress(self, query: str) -> list[AddressMatch]:
        """Return detailed address matches for user confirmation.

        Args:
            query: str

        Returns:
            list[AddressMatch].

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getThemeData(self, queryName: str, extents: list[Coordinates] | None=None) -> JSON:
        """Return raw OneMap theme data for the requested theme.

        Args:
            queryName: str
            extents: list[Coordinates] | None

        Returns:
            JSON.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    def getNearbyTransport(self, origin: Coordinates, radiusM: int) -> JSON:
        """Return nearby transport options for a coordinate.

        Args:
            origin: Coordinates
            radiusM: int

        Returns:
            JSON.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...
