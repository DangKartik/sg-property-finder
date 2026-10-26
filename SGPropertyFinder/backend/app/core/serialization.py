"""JSON-safe serialization for dataclasses, enums and datetimes."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any


def toJsonable(value: Any) -> Any:
    """Convert domain objects into JSON-compatible values."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return {key: toJsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): toJsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [toJsonable(item) for item in value]
    return value
