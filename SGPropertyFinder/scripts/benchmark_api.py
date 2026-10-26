"""Benchmark the SG Property Finder HTTP API and OneMap commute path.

The script can start a dedicated Uvicorn instance so measurements are not
affected by the developer's existing server or by a data refresh.

Examples
--------
    python scripts/benchmark_api.py --spawn-server --warm-samples 20
    python scripts/benchmark_api.py --base-url http://127.0.0.1:8000 --warm-samples 20

Results are written as JSON (default: docs/sla_benchmark_results.json).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DEFAULT_PORT = 8011
DEFAULT_OUTPUT = ROOT / "docs" / "sla_benchmark_results.json"

# Non-CBD anchors so public-transport ranking exercises the live shortlist.
COLD_ANCHORS = [
    ("Pasir Ris", 1.3733, 103.9494),
    ("Jurong East", 1.3331, 103.7420),
    ("Punggol", 1.4050, 103.9020),
    ("Woodlands", 1.4369, 103.7865),
    ("Serangoon", 1.3496, 103.8737),
]

DESTINATIONS = [
    (1.3733, 103.9494),
    (1.3533, 103.9451),
    (1.3331, 103.7420),
    (1.4369, 103.7865),
    (1.4050, 103.9020),
    (1.3496, 103.8737),
    (1.3210, 103.9310),
    (1.3000, 103.8500),
    (1.3800, 103.7500),
    (1.4300, 103.8350),
]


def profile_payload(name: str, latitude: float, longitude: float) -> dict[str, Any]:
    """Build the benchmark profile (commute-heavy public transport)."""
    return {
        "profileId": f"bench-{name.lower().replace(' ', '-')}",
        "profileName": f"Benchmark {name}",
        "budgetMin": 0,
        "budgetMax": 2_000_000,
        "selectedFlatTypes": ["4 ROOM"],
        "workplaceAddress": name,
        "anchorCoordinates": {"latitude": latitude, "longitude": longitude},
        "criteriaWeights": [
            {"criterionId": "PRICE", "weightValue": 1},
            {"criterionId": "COMMUTE_TIME", "weightValue": 10},
            {"criterionId": "SCHOOL_PROXIMITY", "weightValue": 1},
            {"criterionId": "GREEN_COVERAGE", "weightValue": 1},
            {"criterionId": "AMENITIES_DENSITY", "weightValue": 1},
        ],
        "preferredCommuteMode": "PUBLIC_TRANSIT",
        "isActive": True,
        "minimumPrimarySchools": 0,
        "minimumSecondarySchools": 0,
        "minimumTertiarySchools": 0,
        "minimumMalls": 0,
        "minimumHospitals": 0,
    }


def percentile(values: list[float], fraction: float) -> float | None:
    """Linear-interpolated percentile for a small sample."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def stats(samples: list[float]) -> dict[str, Any]:
    """Summarise a list of millisecond timings."""
    if not samples:
        return {
            "count": 0,
            "minMs": None,
            "meanMs": None,
            "p50Ms": None,
            "p95Ms": None,
            "p99Ms": None,
            "maxMs": None,
        }
    return {
        "count": len(samples),
        "minMs": round(min(samples), 2),
        "meanMs": round(statistics.mean(samples), 2),
        "p50Ms": round(percentile(samples, 0.50) or 0.0, 2),
        "p95Ms": round(percentile(samples, 0.95) or 0.0, 2),
        "p99Ms": round(percentile(samples, 0.99) or 0.0, 2),
        "maxMs": round(max(samples), 2),
    }


def wait_for_health(client: httpx.Client, timeout_seconds: int = 120) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        try:
            response = client.get("/api/v1/health", timeout=3)
            if response.status_code == 200 and response.json().get("success"):
                return
        except Exception as exc:  # noqa: BLE001 - startup probe
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"Backend did not become healthy: {last_error}")


def start_server(port: int) -> tuple[subprocess.Popen[bytes], Any]:
    """Start a dedicated Uvicorn process with stale-data refresh disabled."""
    log_path = ROOT / "docs" / "sla_benchmark_server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")
    env = os.environ.copy()
    env["DATA_MAX_AGE_HOURS"] = "99999"
    env["APP_ENV"] = "benchmark"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=BACKEND,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    return process, log_file


def stop_server(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
    else:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def timed_request(
    client: httpx.Client,
    method: str,
    path: str,
    **kwargs: Any,
) -> tuple[float, dict[str, Any], int]:
    """Return elapsed milliseconds, parsed JSON and HTTP status."""
    started = time.perf_counter()
    response = client.request(method, path, **kwargs)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    try:
        payload = response.json()
    except Exception:  # noqa: BLE001 - binary or malformed response
        payload = {}
    return elapsed_ms, payload, response.status_code


def benchmark_http(client: httpx.Client, warm_samples: int) -> dict[str, Any]:
    """Measure endpoint latency and cold/warm recommendation performance."""
    results: dict[str, Any] = {}

    # Simple GET endpoints.
    for name, path in (
        ("health", "/api/v1/health"),
        ("criteria", "/api/v1/criteria"),
        ("geometry", "/api/v1/subzones/geometry"),
        ("amenities", "/api/v1/amenities"),
    ):
        samples: list[float] = []
        statuses: list[int] = []
        for _ in range(warm_samples):
            elapsed, _, status = timed_request(client, "GET", path)
            samples.append(elapsed)
            statuses.append(status)
        results[name] = {
            "stats": stats(samples),
            "httpStatuses": sorted(set(statuses)),
        }

    geometry_payload = client.get("/api/v1/subzones/geometry").json()
    features = geometry_payload.get("data", {}).get("features", [])
    codes = [
        feature.get("properties", {}).get("subzoneCode")
        for feature in features[:2]
        if feature.get("properties", {}).get("subzoneCode")
    ]

    # Cold recommendations: each anchor is unique, so the commute cache misses.
    cold_samples: list[float] = []
    cold_details: list[dict[str, Any]] = []
    for name, latitude, longitude in COLD_ANCHORS:
        payload = profile_payload(name, latitude, longitude)
        elapsed, body, status = timed_request(
            client, "POST", "/api/v1/recommendations", json=payload
        )
        cold_samples.append(elapsed)
        data = body.get("data") or {}
        cold_details.append(
            {
                "anchor": name,
                "elapsedMs": round(elapsed, 2),
                "httpStatus": status,
                "success": bool(body.get("success")),
                "items": len(data.get("items", [])),
                "warnings": len(data.get("warnings", [])),
            }
        )

    # Warm recommendations: repeat the first anchor after its cache is populated.
    warm_payload = profile_payload(*COLD_ANCHORS[0])
    timed_request(client, "POST", "/api/v1/recommendations", json=warm_payload)
    warm_timings: list[float] = []
    warm_warning_counts: list[int] = []
    warm_item_counts: list[int] = []
    for _ in range(warm_samples):
        elapsed, body, _ = timed_request(
            client, "POST", "/api/v1/recommendations", json=warm_payload
        )
        data = body.get("data") or {}
        warm_timings.append(elapsed)
        warm_warning_counts.append(len(data.get("warnings", [])))
        warm_item_counts.append(len(data.get("items", [])))

    results["recommendations"] = {
        "cold": {
            "stats": stats(cold_samples),
            "samples": cold_details,
        },
        "warm": {
            "stats": stats(warm_timings),
            "items": sorted(set(warm_item_counts)),
            "warnings": {
                "min": min(warm_warning_counts) if warm_warning_counts else 0,
                "max": max(warm_warning_counts) if warm_warning_counts else 0,
            },
        },
    }

    # Comparison and factsheet use the same profile and first two subzones.
    if len(codes) >= 2:
        comparison_payload = {
            "profile": warm_payload,
            "subzoneCodes": codes[:2],
        }
        samples = []
        for _ in range(max(3, warm_samples // 2)):
            elapsed, _, _ = timed_request(
                client, "POST", "/api/v1/comparison", json=comparison_payload
            )
            samples.append(elapsed)
        results["comparison"] = {"stats": stats(samples)}

        profile_query = quote(json.dumps(warm_payload, separators=(",", ":")))
        samples = []
        for _ in range(max(3, warm_samples // 2)):
            elapsed, _, _ = timed_request(
                client,
                "GET",
                f"/api/v1/subzones/{codes[0]}/factsheet?profile={profile_query}",
            )
            samples.append(elapsed)
        results["factsheet"] = {"stats": stats(samples)}

    # PDF generation is heavier; use a smaller sample.
    pdf_payload = {
        "profile": warm_payload,
        "subzoneCodes": codes[:2] or ["TAMPINES01", "BEDOK01"],
    }
    pdf_samples = []
    for _ in range(5):
        elapsed, _, _ = timed_request(
            client, "POST", "/api/v1/reports/pdf", json=pdf_payload
        )
        pdf_samples.append(elapsed)
    results["pdf"] = {"stats": stats(pdf_samples)}

    return results


def benchmark_commute(warm_samples: int) -> dict[str, Any]:
    """Benchmark the live OneMap commute path cold and warm, in process."""
    sys.path.insert(0, str(BACKEND))
    from app.adapter.one_map_api_adapter import OneMapApiAdapter
    from app.config import Settings
    from app.control.commute_control import CommuteControl
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.core.time import nextWeekdayPeak
    from app.entity.enums import TransitMode
    from app.entity.types import Coordinates

    settings = Settings.fromEnv()
    adapter = OneMapApiAdapter(
        settings.ONEMAP_BASE_URL,
        settings.ONEMAP_EMAIL or "",
        settings.ONEMAP_PASSWORD or "",
    )
    control = CommuteControl(
        adapter,
        DataAvailabilityNotifier(),
        matrixPath=BACKEND / "assets" / "data" / "commute_matrix.json",
    )
    origin = Coordinates(1.3733, 103.9494)
    departure = nextWeekdayPeak()

    cold_samples: list[float] = []
    fallbacks = 0
    errors: list[str] = []
    for index, (latitude, longitude) in enumerate(DESTINATIONS):
        warnings: list[Any] = []
        started = time.perf_counter()
        try:
            control.retrieveCommute(
                origin,
                Coordinates(latitude, longitude),
                TransitMode.PUBLIC_TRANSIT,
                departure,
                f"BENCH-C-{index}",
                warnings,
            )
            if warnings:
                fallbacks += 1
        except Exception as exc:  # noqa: BLE001 - record live failures
            errors.append(str(exc))
        cold_samples.append((time.perf_counter() - started) * 1000.0)

    warm_samples_ms: list[float] = []
    for index, (latitude, longitude) in enumerate(DESTINATIONS):
        started = time.perf_counter()
        control.retrieveCommute(
            origin,
            Coordinates(latitude, longitude),
            TransitMode.PUBLIC_TRANSIT,
            departure,
            f"BENCH-C-{index}",
        )
        warm_samples_ms.append((time.perf_counter() - started) * 1000.0)

    return {
        "cold": {
            "stats": stats(cold_samples),
            "fallbacks": fallbacks,
            "errors": errors,
        },
        "warm": {"stats": stats(warm_samples_ms)},
        "destinationCount": len(DESTINATIONS),
        "mode": "PUBLIC_TRANSIT",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--spawn-server", action="store_true")
    parser.add_argument("--warm-samples", type=int, default=20)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-commute",
        action="store_true",
        help="Skip the live OneMap commute benchmark.",
    )
    args = parser.parse_args(argv)
    base_url = args.base_url or f"http://127.0.0.1:{args.port}"

    server = None
    log_file = None
    try:
        if args.spawn_server:
            server, log_file = start_server(args.port)
        with httpx.Client(base_url=base_url, timeout=180.0) as client:
            wait_for_health(client)
            status_before = client.get("/api/v1/data/status").json()
            http_results = benchmark_http(client, args.warm_samples)
            status_after = client.get("/api/v1/data/status").json()

        commute_results = None
        if not args.skip_commute:
            commute_results = benchmark_commute(args.warm_samples)

        result = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "baseUrl": base_url,
            "environment": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "processor": platform.processor() or "unknown",
                "cpuCount": os.cpu_count(),
            },
            "config": {
                "warmSamples": args.warm_samples,
                "coldAnchors": [name for name, _, _ in COLD_ANCHORS],
                "dataRefreshDisabled": args.spawn_server,
                "profile": "budget 2M, 4 ROOM, PT, commute weight 10, other weights 1",
            },
            "dataStatusBefore": status_before.get("data"),
            "dataStatusAfter": status_after.get("data"),
            "http": http_results,
            "commute": commute_results,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print(f"Wrote {args.output}")
        print("\nHTTP results (ms):")
        for name in ("health", "criteria", "geometry", "amenities"):
            print(f"  {name:<14} {http_results[name]['stats']}")
        print(f"  recommendations cold {http_results['recommendations']['cold']['stats']}")
        print(f"  recommendations warm {http_results['recommendations']['warm']['stats']}")
        for name in ("comparison", "factsheet", "pdf"):
            if name in http_results:
                print(f"  {name:<14} {http_results[name]['stats']}")
        if commute_results:
            print("\nOneMap commute (ms):")
            print(f"  cold {commute_results['cold']['stats']} fallbacks={commute_results['cold']['fallbacks']}")
            print(f"  warm {commute_results['warm']['stats']}")
        return 0
    finally:
        if server is not None:
            stop_server(server)
        if log_file is not None:
            log_file.close()


if __name__ == "__main__":
    raise SystemExit(main())
