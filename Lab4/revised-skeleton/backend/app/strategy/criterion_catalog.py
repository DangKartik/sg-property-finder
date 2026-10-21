"""Criterion catalog module."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class CriterionDirection(str, Enum):
    """Stereotype: Strategy. Strategy enum describing whether a criterion is minimised or maximised."""
    MINIMIZE = 'MINIMIZE'
    MAXIMIZE = 'MAXIMIZE'

@dataclass(frozen=True)
class CriterionDefinition:
    """Stereotype: Strategy. Strategy value object defining a criterion's ID, unit, direction and buffer."""
    criterionId: str
    criterionName: str
    unit: str
    direction: CriterionDirection
    bufferM: int | None = None
    defaultWeight: float | None = None

class CriterionCatalog:
    """Stereotype: Strategy. Strategy container holding the frozen criterion definitions used by scoring."""
    definitions: dict[str, CriterionDefinition]

    def __init__(self, definitions: dict[str, CriterionDefinition]) -> None:
        """Initialise the CriterionCatalog with its dependencies.

        Args:
            definitions: dict[str, CriterionDefinition]

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getCriterion(self, criterionId: str) -> CriterionDefinition | None:
        """Return criterion.

        Args:
            criterionId: str

        Returns:
            CriterionDefinition | None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getAllCriteria(self) -> list[CriterionDefinition]:
        """Return all criteria.

        Args:
            None.

        Returns:
            list[CriterionDefinition].

        Failure handling:
            Not applicable at the skeleton level."""
        ...
