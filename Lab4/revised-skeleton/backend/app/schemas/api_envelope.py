from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from app.schemas.data_availability_warning import DataAvailabilityWarning

T = TypeVar("T")


@dataclass
class ApiError:
    code: str
    message: str
    details: dict[str, Any] | None = None


@dataclass
class ApiEnvelope(Generic[T]):
    success: bool
    data: T | None = None
    warnings: list[DataAvailabilityWarning] = field(default_factory=list)
    error: ApiError | None = None
