"""Google/OneMap encoded-polyline helpers.

Each encoded polyline is a self-contained sequence of deltas starting at
``(0, 0)``. Concatenating two encoded strings is therefore invalid: every point
in the second string must be decoded independently and then re-encoded relative
to the last point of the first string. OneMap public-transport itineraries are
split into walking and transit legs, so this module merges those legs into one
continuous geometry for Leaflet.
"""

from __future__ import annotations

from typing import Iterable


def decodePolyline(encoded: str | None) -> list[tuple[float, float]]:
    """Decode an encoded polyline into ``(latitude, longitude)`` pairs.

    Args:
        encoded: Google/OneMap encoded polyline. Empty values return an empty list.

    Returns:
        list[tuple[float, float]]: Decoded WGS84 coordinates.

    Failure handling:
        Raise ``ValueError`` when the encoded string is truncated or contains an
        invalid character.
    """
    if not encoded:
        return []

    points: list[tuple[float, float]] = []
    index = 0
    latitude = 0
    longitude = 0
    while index < len(encoded):
        latitude_delta, index = _decodeValue(encoded, index)
        longitude_delta, index = _decodeValue(encoded, index)
        latitude += latitude_delta
        longitude += longitude_delta
        points.append((latitude / 1e5, longitude / 1e5))
    return points


def encodePolyline(points: Iterable[tuple[float, float]]) -> str:
    """Encode ``(latitude, longitude)`` pairs as one polyline string.

    Args:
        points: WGS84 coordinates in route order.

    Returns:
        str: Google/OneMap encoded polyline.
    """
    encoded: list[str] = []
    previous_latitude = 0
    previous_longitude = 0
    for latitude, longitude in points:
        latitude_value = round(latitude * 1e5)
        longitude_value = round(longitude * 1e5)
        encoded.append(_encodeValue(latitude_value - previous_latitude))
        encoded.append(_encodeValue(longitude_value - previous_longitude))
        previous_latitude = latitude_value
        previous_longitude = longitude_value
    return "".join(encoded)


def mergeEncodedPolylines(parts: Iterable[str | None]) -> str:
    """Merge independently encoded polylines into one continuous polyline.

    Args:
        parts: Encoded leg geometries in travel order.

    Returns:
        str: A single encoded polyline. Duplicate points at leg joins are dropped.
    """
    points: list[tuple[float, float]] = []
    for part in parts:
        decoded = decodePolyline(part)
        if not decoded:
            continue
        if points and points[-1] == decoded[0]:
            decoded = decoded[1:]
        points.extend(decoded)
    return encodePolyline(points)


def _decodeValue(encoded: str, index: int) -> tuple[int, int]:
    """Decode one signed varint starting at ``index``."""
    result = 0
    shift = 0
    while True:
        if index >= len(encoded):
            raise ValueError("Truncated encoded polyline")
        byte = ord(encoded[index]) - 63
        index += 1
        if byte < 0:
            raise ValueError("Encoded polyline contains an invalid character")
        result |= (byte & 0x1F) << shift
        shift += 5
        if byte < 0x20:
            break
    delta = ~(result >> 1) if result & 1 else result >> 1
    return delta, index


def _encodeValue(value: int) -> str:
    """Encode one signed integer as a varint."""
    value = ~(value << 1) if value < 0 else value << 1
    chunks: list[str] = []
    while value >= 0x20:
        chunks.append(chr((0x20 | (value & 0x1F)) + 63))
        value >>= 5
    chunks.append(chr(value + 63))
    return "".join(chunks)
