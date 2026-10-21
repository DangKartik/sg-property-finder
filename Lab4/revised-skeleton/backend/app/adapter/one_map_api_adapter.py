from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.address_match import AddressMatch
    from app.entity.types import Coordinates, JSON, TransitMode


class OneMapApiAdapter:
    baseUrl: str
    email: str
    password: str
    accessToken: str | None
    tokenExpiry: datetime | None

    def __init__(self, baseUrl: str, email: str, password: str) -> None: ...
    def refreshToken(self) -> None: ...
    def getRoutingData(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
    ) -> JSON: ...
    def searchAddress(self, query: str) -> list[AddressMatch]: ...
    def getThemeData(
        self,
        queryName: str,
        extents: list[Coordinates] | None = None,
    ) -> JSON: ...
    def getNearbyTransport(self, origin: Coordinates, radiusM: int) -> JSON: ...
