"""Frozen criterion definitions used by scoring."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CriterionDirection(str, Enum):
    """Stereotype: Strategy. Whether a criterion is minimised or maximised."""

    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"


@dataclass(frozen=True)
class CriterionDefinition:
    """Stereotype: Strategy. Metadata and fixed normalisation domain for a criterion."""

    criterionId: str
    criterionName: str
    unit: str
    direction: CriterionDirection
    bufferM: int | None = None
    defaultWeight: float | None = None
    minValue: float | None = None
    maxValue: float | None = None


class CriterionCatalog:
    """Stereotype: Strategy. Container for the criterion definitions."""

    definitions: dict[str, CriterionDefinition]

    def __init__(self, definitions: dict[str, CriterionDefinition]) -> None:
        """Create the catalogue from criterion definitions."""
        self.definitions = dict(definitions)

    def getCriterion(self, criterionId: str) -> CriterionDefinition | None:
        """Return a criterion definition by ID."""
        return self.definitions.get(criterionId)

    def getAllCriteria(self) -> list[CriterionDefinition]:
        """Return all definitions in stable order."""
        return list(self.definitions.values())


def buildDefaultCriterionCatalog() -> CriterionCatalog:
    """Return the frozen v1 criterion catalogue with absolute Singapore bounds."""
    definitions = [
        CriterionDefinition(
            "PRICE", "Housing affordability", "SGD", CriterionDirection.MINIMIZE,
            None, 5.0, 200_000.0, 1_500_000.0,
        ),
        CriterionDefinition(
            "COMMUTE_TIME", "Commute duration", "minutes", CriterionDirection.MINIMIZE,
            None, 5.0, 0.0, 90.0,
        ),
        CriterionDefinition(
            "SCHOOL_PROXIMITY", "School access", "count", CriterionDirection.MAXIMIZE,
            1000, 5.0, 0.0, 4.0,
        ),
        CriterionDefinition(
            "GREEN_COVERAGE", "Green coverage", "percent", CriterionDirection.MAXIMIZE,
            500, 5.0, 0.0, 100.0,
        ),
        CriterionDefinition(
            "AMENITIES_DENSITY", "Amenity access", "count", CriterionDirection.MAXIMIZE,
            None, 5.0, 0.0, 10.0,
        ),
    ]
    return CriterionCatalog({definition.criterionId: definition for definition in definitions})
