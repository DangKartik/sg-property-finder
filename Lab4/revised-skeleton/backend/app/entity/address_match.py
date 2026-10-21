from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.types import Coordinates


@dataclass
class AddressMatch:
    formattedAddress: str
    postalCode: str
    coordinates: Coordinates
    confidenceScore: float | None = None

    def getFormattedAddress(self) -> str: ...
    def getPostalCode(self) -> str: ...
    def getCoordinates(self) -> Coordinates: ...
    def getConfidenceScore(self) -> float | None: ...
