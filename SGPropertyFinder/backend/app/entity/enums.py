"""Enums module."""

from __future__ import annotations
from enum import Enum

class TransitMode(str, Enum):
    """Stereotype: Entity. Enumeration of commute modes supported by the routing adapter."""
    PUBLIC_TRANSIT = 'PUBLIC_TRANSIT'
    DRIVING = 'DRIVING'
    WALKING = 'WALKING'

class EnvironmentGranularity(str, Enum):
    """Stereotype: Entity. Enumeration of spatial levels at which environment data is reported."""
    NATIONAL = 'NATIONAL'
    REGION = 'REGION'
    SUBZONE = 'SUBZONE'

class WarningSeverity(str, Enum):
    """Stereotype: Entity. Enumeration of data-availability warning severities."""
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'

class DataAvailabilityCode(str, Enum):
    """Stereotype: Entity. Enumeration of machine-readable reasons for a data-availability warning."""
    MISSING_SOURCE_DATA = 'MISSING_SOURCE_DATA'
    VALID_ZERO = 'VALID_ZERO'
    STALE_CACHE = 'STALE_CACHE'
    PARTIAL_DATA = 'PARTIAL_DATA'
    ESTIMATED_COMMUTE_FALLBACK = 'ESTIMATED_COMMUTE_FALLBACK'
