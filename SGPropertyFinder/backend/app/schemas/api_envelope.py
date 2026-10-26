"""Api envelope module."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar
if TYPE_CHECKING:
    from app.entity.data_availability_warning import DataAvailabilityWarning
T = TypeVar('T')

@dataclass
class ApiError:
    """Stereotype: Schema DTO. Schema DTO describing an API error inside the standard response envelope."""
    code: str
    message: str
    details: dict[str, Any] | None = None

@dataclass
class ApiEnvelope(Generic[T]):
    """Stereotype: Schema DTO. Schema DTO wrapping every API response with data, warnings and errors."""
    success: bool
    data: T | None = None
    warnings: list[DataAvailabilityWarning] = field(default_factory=list)
    error: ApiError | None = None
