"""Transport-agnostic REST handlers used by main.py and unit tests."""

from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import unquote

from datetime import datetime, timezone

from app.bootstrap import AppContext
from app.core.serialization import toJsonable
from app.entity.enums import TransitMode
from app.entity.types import Coordinates
from app.schemas.api_envelope import ApiEnvelope, ApiError
from app.services.profile_factory import preferenceProfileFromDto, profileDtoFromDict


def ok(data: Any, warnings: list[Any] | None = None) -> ApiEnvelope[Any]:
    """Create a successful API envelope."""
    return ApiEnvelope(success=True, data=toJsonable(data), warnings=warnings or [], error=None)


def fail(code: str, message: str, details: Any = None) -> ApiEnvelope[Any]:
    """Create a failed API envelope."""
    return ApiEnvelope(
        success=False,
        data=None,
        warnings=[],
        error=ApiError(code=code, message=message, details=toJsonable(details)),
    )


def searchAddress(query: str, context: AppContext) -> ApiEnvelope[Any]:
    """Handle workplace address search."""
    if not query or not query.strip():
        return fail("INVALID_QUERY", "Enter an address or postal code.")
    try:
        matches = context.oneMapAdapter.searchAddress(query.strip())
    except Exception as exc:
        return fail("ADDRESS_LOOKUP_FAILED", "Unable to search for the address.", {"retryable": True})
    if not matches:
        return fail("ADDRESS_NOT_FOUND", "Address not Found. Enter a valid postal code or building name.")
    return ok(matches)


def validateProfile(profilePayload: dict[str, Any], context: AppContext) -> ApiEnvelope[Any]:
    """Validate a profile without persisting or ranking it."""
    try:
        dto = profileDtoFromDict(profilePayload)
    except ValueError as exc:
        return fail("INVALID_PROFILE", str(exc))
    validation = context.validator.validateProfileData(dto)
    return ok(validation)


def recommendations(profilePayload: dict[str, Any], context: AppContext) -> ApiEnvelope[Any]:
    """Validate a profile and return ranked recommendations."""
    parsed, error = _profileFromPayload(profilePayload, context)
    if error is not None:
        return error
    try:
        result = context.rankingControl.generateRankedRecommendations(parsed)
    except Exception as exc:
        return fail("RANKING_FAILED", "Unable to generate recommendations.", {"retryable": True})
    return ok(result, result.warnings)


def factsheet(
    subzoneCode: str,
    profilePayload: dict[str, Any],
    context: AppContext,
) -> ApiEnvelope[Any]:
    """Return a detailed factsheet for one subzone."""
    parsed, error = _profileFromPayload(profilePayload, context)
    if error is not None:
        return error
    try:
        detail = context.detailsControl.fetchNeighborhoodDetails(subzoneCode, parsed)
    except KeyError:
        return fail("SUBZONE_NOT_FOUND", f"Unknown subzone: {subzoneCode}")
    except Exception:
        return fail("FACTSHEET_FAILED", "Unable to load the factsheet.", {"retryable": True})
    return ok(detail, detail.warnings)


def comparison(
    profilePayload: dict[str, Any],
    subzoneCodes: list[str],
    context: AppContext,
) -> ApiEnvelope[Any]:
    """Compare two or more subzones."""
    parsed, error = _profileFromPayload(profilePayload, context)
    if error is not None:
        return error
    try:
        result = context.comparisonControl.compare(parsed, subzoneCodes)
    except ValueError as exc:
        return fail("INVALID_COMPARISON", str(exc))
    except Exception:
        return fail("COMPARISON_FAILED", "Unable to compare the selected subzones.", {"retryable": True})
    return ok(result, result.details[0].warnings if result.details else [])


def commuteOverlay(payload: dict[str, Any], context: AppContext) -> ApiEnvelope[Any]:
    """Return a transit/driving/walking route overlay."""
    try:
        origin_data = payload["origin"]
        destination_data = payload["destination"]
        origin = Coordinates(float(origin_data["latitude"]), float(origin_data["longitude"]))
        destination = Coordinates(
            float(destination_data["latitude"]), float(destination_data["longitude"])
        )
        mode = TransitMode(str(payload.get("mode", TransitMode.PUBLIC_TRANSIT.value)))
        departure_text = payload.get("departureTime")
        departure = (
            datetime.fromisoformat(str(departure_text).replace("Z", "+00:00"))
            if departure_text
            else None
        )
        if departure is not None and departure.tzinfo is None:
            departure = departure.replace(tzinfo=timezone.utc)
        route = context.mapControl.getCommuteOverlay(origin, destination, mode, departure)
        return ok(route)
    except (KeyError, TypeError, ValueError) as exc:
        return fail("INVALID_ROUTE_REQUEST", f"Invalid route request: {exc}")
    except Exception:
        return fail("ROUTE_FAILED", "Unable to retrieve a route overlay.", {"retryable": True})


def generateReport(
    profilePayload: dict[str, Any],
    subzoneCodes: list[str],
    context: AppContext,
) -> ApiEnvelope[Any]:
    """Generate a PDF report and return secure download metadata."""
    parsed, error = _profileFromPayload(profilePayload, context)
    if error is not None:
        return error
    try:
        recommendations_result = context.rankingControl.generateRankedRecommendations(parsed)
        codes = list(dict.fromkeys(subzoneCodes)) or [
            item.subzoneId for item in recommendations_result.getItems()[:3]
        ]
        details = [
            context.detailsControl.fetchNeighborhoodDetails(code, parsed) for code in codes
        ]
        report = context.reportControl.generatePdfReport(recommendations_result, details)
        share_url = context.reportControl.generateShareableUrl(parsed, codes, "/")
        return ok({"report": report, "shareUrl": share_url}, recommendations_result.warnings)
    except Exception:
        return fail("REPORT_FAILED", "Unable to generate the PDF report.", {"retryable": True})


def geometry(context: AppContext, scores: dict[str, float] | None = None) -> ApiEnvelope[Any]:
    """Return the URA subzone FeatureCollection."""
    return ok(context.registry.toFeatureCollection(scores))


def criteria(context: AppContext) -> ApiEnvelope[Any]:
    """Return the frozen criterion catalogue."""
    return ok(context.scoringStrategy.criterionCatalog.getAllCriteria())


def dataStatus(context: AppContext) -> ApiEnvelope[Any]:
    """Return live/snapshot freshness metadata for the frontend cache layer."""
    return ok(context.datasetService.status())


def refreshData(context: AppContext) -> ApiEnvelope[Any]:
    """Force a live data.gov.sg refresh and return the resulting statuses."""
    try:
        statuses = context.datasetService.refresh()
    except Exception:
        return fail("DATA_REFRESH_FAILED", "Unable to refresh data.gov.sg datasets.", {"retryable": True})
    return ok(statuses)


def reportPath(reportId: str, context: AppContext) -> Any:
    """Return a stored report path or None when expired/missing."""
    return context.reportStore.getPath(reportId)


def decodeShare(share: str) -> tuple[dict[str, Any], list[str]]:
    """Decode a shareable URL payload."""
    try:
        raw = unquote(share)
        padded = raw + ("=" * (-len(raw) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid share payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid share payload")
    return payload.get("profile", {}), list(payload.get("subzones", []))


def decodeShareLink(share: str, context: AppContext) -> ApiEnvelope[Any]:
    """Decode a share link into a ProfileDTO and selected subzone codes."""
    if not share or not share.strip():
        return fail("INVALID_SHARE_LINK", "A share payload is required.")
    try:
        profile_payload, subzone_codes = decodeShare(share.strip())
    except ValueError as exc:
        return fail("INVALID_SHARE_LINK", str(exc))
    if not isinstance(profile_payload, dict) or not profile_payload:
        return fail("INVALID_SHARE_LINK", "The share link does not contain a profile.")
    try:
        profile = profileDtoFromDict(profile_payload)
    except ValueError as exc:
        return fail("INVALID_SHARE_LINK", str(exc))
    codes = list(
        dict.fromkeys(
            str(code).strip()
            for code in subzone_codes
            if str(code).strip()
        )
    )
    return ok({"profile": profile, "subzoneCodes": codes})


def health() -> ApiEnvelope[Any]:
    """Return a simple health response."""
    return ok({"status": "ok"})


def ready(context: AppContext) -> ApiEnvelope[Any]:
    """Return readiness based on loaded subzones."""
    loaded = len(context.registry.getAllSubzones())
    return ok({"ready": loaded > 0, "subzoneCount": loaded})


def _profileFromPayload(
    payload: dict[str, Any],
    context: AppContext,
) -> tuple[Any, ApiEnvelope[Any] | None]:
    try:
        dto = profileDtoFromDict(payload)
    except ValueError as exc:
        return None, fail("INVALID_PROFILE", str(exc))
    validation = context.validator.validateProfileData(dto)
    if not validation.isValid:
        return None, fail("VALIDATION_ERROR", "Profile validation failed.", validation)
    return preferenceProfileFromDto(dto), None
