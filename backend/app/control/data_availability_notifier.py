"""Stateless data-availability warning factory."""

from __future__ import annotations

from datetime import datetime, timezone

from app.entity.data_availability_warning import DataAvailabilityWarning
from app.entity.enums import DataAvailabilityCode, WarningSeverity


class DataAvailabilityNotifier:
    """Stereotype: Control. Creates warnings without retaining request state."""

    def notifyDataUnavailable(
        self,
        datasetCode: str,
        subzoneCode: str | None = None,
        code: DataAvailabilityCode | None = None,
        source: str = "data.gov.sg",
        isStale: bool = False,
        isRetryable: bool = False,
        message: str | None = None,
    ) -> DataAvailabilityWarning:
        """Build a warning for one dataset/criterion."""
        reason = code or DataAvailabilityCode.MISSING_SOURCE_DATA
        severity = (
            WarningSeverity.INFO
            if reason is DataAvailabilityCode.VALID_ZERO
            else WarningSeverity.WARNING
        )
        if reason is DataAvailabilityCode.MISSING_SOURCE_DATA and not isRetryable:
            severity = WarningSeverity.WARNING
        if message is None:
            message = _defaultMessage(datasetCode, reason, isStale)
        return DataAvailabilityWarning(
            subzoneCode=subzoneCode,
            datasetCode=datasetCode,
            code=reason,
            severity=severity,
            isStale=isStale,
            isRetryable=isRetryable,
            source=source,
            message=message,
            asOf=datetime.now(timezone.utc),
        )


def _defaultMessage(datasetCode: str, code: DataAvailabilityCode, isStale: bool) -> str:
    if isStale:
        return f"{datasetCode} data is from a stale fallback snapshot"
    if code is DataAvailabilityCode.VALID_ZERO:
        return f"{datasetCode} has a valid zero value"
    if code is DataAvailabilityCode.PARTIAL_DATA:
        return f"{datasetCode} is only partially available"
    return f"{datasetCode} data is unavailable"
